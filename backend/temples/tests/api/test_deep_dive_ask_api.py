"""Deep Dive Ask API(PR-B5、Thin API Boundary)のcontract test。

docs/product/deep-dive-answer-generation-contract.md §11 API Responsibility。
Backend Authority(readiness判定・question classification・Fact取得・Evidence
filtering・LLM payload構築・provenance決定)がView内で再実装されていないこと、
Not Ready/Fact 0件でLLMが呼ばれないこと、internal field(verification_status/
confidence/reason_strength/content)が公開されないことを検証する。
実LLM(openai SDK)は一切呼び出さない。
"""

from __future__ import annotations

import json

import pytest
from django.utils import timezone

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services import deep_dive_answer

pytestmark = pytest.mark.django_db

URL = "/api/deep-dive/ask/"


def _create_shrine(name: str) -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def _create_source(
    title: str, verification_status: str = "source_confirmed", **kwargs
) -> ShrineKnowledgeSource:
    defaults = dict(
        source_type="shrine_official",
        title=title,
        publisher="神社公式",
        url="https://example.com/",
        verification_status=verification_status,
    )
    if verification_status in ("source_confirmed", "reviewed"):
        defaults["verified_at"] = timezone.now()
    defaults.update(kwargs)
    return ShrineKnowledgeSource.objects.create(**defaults)


def _create_deity(shrine: Shrine, display_name: str, sort_order: int = 0, **kwargs) -> ShrineDeity:
    defaults = dict(
        display_name=display_name,
        verification_status="source_confirmed",
        confidence="high",
        sort_order=sort_order,
        verified_at=timezone.now(),
    )
    defaults.update(kwargs)
    return ShrineDeity.objects.create(shrine=shrine, **defaults)


def _create_history(shrine: Shrine, title: str, sort_order: int = 0, **kwargs) -> ShrineHistory:
    defaults = dict(
        history_type="founding",
        title=title,
        content="内容の本文",
        verification_status="source_confirmed",
        confidence="high",
        sort_order=sort_order,
        verified_at=timezone.now(),
    )
    defaults.update(kwargs)
    return ShrineHistory.objects.create(shrine=shrine, **defaults)


def _make_full_ready_shrine(name: str = "フルレディ神社") -> Shrine:
    shrine = _create_shrine(name)
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    history = _create_history(shrine, "由緒")
    for fact in (deity, history):
        fact.sources.add(source)
    return shrine


def _boom(*args, **kwargs):
    raise AssertionError("LLM must not be constructed/called on this path")


class _FakeLLMClient:
    def __init__(self, content=None, raise_exc: Exception | None = None):
        self._client = object()
        self._mode = "chat"
        self._content = content
        self._raise_exc = raise_exc
        self.calls: list[list[dict]] = []

    def chat(self, messages):
        self.calls.append(messages)
        if self._raise_exc is not None:
            raise self._raise_exc
        return {"role": "assistant", "content": self._content}


def _post(client, body):
    return client.post(URL, data=json.dumps(body), content_type="application/json")


# --- 1. Full Ready ---


def test_1_full_ready_returns_200_with_answer_and_provenance(client, monkeypatch):
    fake_client = _FakeLLMClient(content="この神社の神様についてお答えします。")
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)

    shrine = _make_full_ready_shrine("明治神宮相当")

    res = _post(client, {"shrine_id": shrine.id, "question": "誰を祀っていますか？"})

    assert res.status_code == 200
    body = res.json()
    assert body["readiness"] == "full"
    assert body["answer"] == "この神社の神様についてお答えします。"
    assert body["question_type"] == ["deity_who"]
    assert len(body["facts_used"]) == 1
    assert body["facts_used"][0]["type"] == "deity"
    assert len(body["sources_used"]) == 1
    assert body["limitations"] is None
    assert body["unanswered_aspects"] == []


# --- 2. Limited ---


def test_2_limited_shrine_returns_200_with_limited_readiness(client, monkeypatch):
    fake_client = _FakeLLMClient(content="確認できる範囲でお答えします。")
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)

    shrine = _create_shrine("給田六所神社相当")
    source = _create_source("公式")
    deity = _create_deity(shrine, "大国魂大神", confidence="medium")
    history = _create_history(shrine, "由緒", confidence="medium")
    for fact in (deity, history):
        fact.sources.add(source)

    res = _post(client, {"shrine_id": shrine.id, "question": "誰を祀っていますか？"})

    assert res.status_code == 200
    body = res.json()
    assert body["readiness"] == "limited"
    assert body["limitations"] is not None
    assert len(body["facts_used"]) == 1


# --- 3. Not Ready ---


def test_3_not_ready_shrine_returns_200_not_an_error(client, monkeypatch):
    monkeypatch.setattr(deep_dive_answer, "LLMClient", _boom)
    shrine = _create_shrine("由緒未確認神社")
    # ShrineDeity/ShrineHistoryを一切作らない → not_ready。

    res = _post(client, {"shrine_id": shrine.id, "question": "誰を祀っていますか？"})

    # Not Readyはエラーではなく正常なProduct State(Knowledge不足) -> 200。
    assert res.status_code == 200
    body = res.json()
    assert body["readiness"] == "not_ready"
    assert body["answer"] == ""
    assert body["facts_used"] == []
    assert body["sources_used"] == []
    assert body["limitations"] is not None


# --- 4. Zero Fact ---


def test_4_zero_fact_short_circuit_returns_200_with_unanswered_aspects(client, monkeypatch):
    monkeypatch.setattr(deep_dive_answer, "LLMClient", _boom)
    shrine = _create_shrine("伝承なし神社")
    source = _create_source("公式")
    deity = _create_deity(shrine, "神")
    founding = _create_history(shrine, "創建の経緯", history_type="founding")
    for fact in (deity, founding):
        fact.sources.add(source)
    # tradition種別のHistoryは無い。

    res = _post(client, {"shrine_id": shrine.id, "question": "どんな伝承がありますか？"})

    assert res.status_code == 200
    body = res.json()
    assert body["facts_used"] == []
    assert body["unanswered_aspects"] == ["tradition"]
    assert body["limitations"] is not None


# --- 5. Invalid Shrine ---


def test_5_invalid_shrine_id_returns_404(client):
    res = _post(client, {"shrine_id": 999999, "question": "誰を祀っていますか？"})

    assert res.status_code == 404
    assert "detail" in res.json()


# --- 6. Empty Question ---


def test_6_empty_question_is_not_a_validation_error(client, monkeypatch):
    monkeypatch.setattr(deep_dive_answer, "LLMClient", _boom)
    shrine = _make_full_ready_shrine("空質問神社")

    res = _post(client, {"shrine_id": shrine.id, "question": ""})

    # 空文字は分類不能("other")として正常に処理される。バリデーションエラーにしない。
    assert res.status_code == 200
    body = res.json()
    assert body["question_type"] == ["other"]
    assert body["facts_used"] == []


# --- 7. Malformed Request ---


def test_7_missing_required_fields_returns_400(client):
    res = client.post(URL, data=json.dumps({}), content_type="application/json")

    assert res.status_code == 400
    body = res.json()
    assert "shrine_id" in body
    assert "question" in body


def test_7b_wrong_type_shrine_id_returns_400(client):
    res = _post(client, {"shrine_id": "not-a-number", "question": "誰を祀っていますか？"})

    assert res.status_code == 400
    assert "shrine_id" in res.json()


def test_7c_malformed_json_body_returns_400(client):
    res = client.post(URL, data="{not valid json", content_type="application/json")

    assert res.status_code == 400


# --- 8. LLM Failure ---


def test_8_llm_failure_returns_200_with_deterministic_answer_and_retrieved_facts(client, monkeypatch):
    fake_client = _FakeLLMClient(raise_exc=RuntimeError("network down"))
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)

    shrine = _make_full_ready_shrine("LLM失敗神社")

    res = _post(client, {"shrine_id": shrine.id, "question": "誰を祀っていますか？"})

    assert res.status_code == 200
    body = res.json()
    # LLM失敗時はFactを捏造したfallback文章ではなく、deterministic builder
    # (PR-ND1)による実際のFactに基づく回答が返る(PR-ND2、意図的な契約変更)。
    assert body["answer"] == "神をお祀りしています。"
    assert body["answer"] != "現在、回答の生成に失敗しました。時間をおいて再度お試しください。"
    # LLMが失敗しても、retrieval済みの安全なfacts_used/sources_usedはそのまま返る。
    assert len(body["facts_used"]) == 1
    assert len(body["sources_used"]) == 1


# --- 9. Provenance一致 ---


def test_9_provenance_matches_service_output_exactly(client, monkeypatch):
    fake_client = _FakeLLMClient(content="回答本文。")
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)

    shrine = _create_shrine("Provenance検証神社")
    source_a = _create_source("Source A")
    source_b = _create_source("Source B")
    deity = _create_deity(shrine, "神")
    deity.sources.add(source_a, source_b)
    history = _create_history(shrine, "由緒")
    history.sources.add(source_a)

    res = _post(client, {"shrine_id": shrine.id, "question": "誰を祀っていますか？"})

    assert res.status_code == 200
    body = res.json()

    expected = deep_dive_answer.generate_deep_dive_answer(
        shrine_id=shrine.id, question_text="誰を祀っていますか？"
    )
    assert {f["id"] for f in body["facts_used"]} == {f.id for f in expected.facts_used}
    assert {f["type"] for f in body["facts_used"]} == {f.type for f in expected.facts_used}
    assert {s["id"] for s in body["sources_used"]} == {s.id for s in expected.sources_used}
    assert {s["id"] for s in body["sources_used"]} == {source_a.id, source_b.id}


# --- 10. Internal Fields非公開 ---


def test_10_internal_fields_are_never_exposed(client, monkeypatch):
    fake_client = _FakeLLMClient(content="回答本文。")
    monkeypatch.setattr(deep_dive_answer, "LLMClient", lambda: fake_client)

    shrine = _make_full_ready_shrine("内部field検証神社")

    res = _post(client, {"shrine_id": shrine.id, "question": "誰を祀っていますか？"})

    assert res.status_code == 200
    raw_text = res.content.decode("utf-8")
    for internal_field in (
        "verification_status",
        "confidence",
        "reason_strength",
        "content",
        "source_ids",
        "llm_used",
    ):
        assert internal_field not in raw_text, f"{internal_field} leaked into API response"


# --- 11. Not Ready LLM Call 0 (API経由でのCall Gate検証) ---


def test_11_not_ready_never_constructs_llm_client_via_api(client, monkeypatch):
    monkeypatch.setattr(deep_dive_answer, "LLMClient", _boom)
    shrine = _create_shrine("Not Ready LLM検証神社")
    # ShrineDeity/ShrineHistoryを一切作らない → not_ready。

    # _boomはLLMClient()が呼ばれた瞬間にAssertionErrorを送出する。例外なく
    # 200が返ることが、API経由でもLLMが一切構築されないことの証明になる。
    res = _post(client, {"shrine_id": shrine.id, "question": "誰を祀っていますか？"})

    assert res.status_code == 200
    assert res.json()["readiness"] == "not_ready"
