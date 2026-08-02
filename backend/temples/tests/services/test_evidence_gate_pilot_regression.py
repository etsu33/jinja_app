"""Evidence Gate Foundation: Pilot回帰テスト。

明治神宮Pilot / 品川神社Pilot（Pilot Evidence Readiness QA: PASS済み）と
同等の条件をfactoryで再現し、Evidence Gate導入後もRecommendation selector /
Shrine Detail双方で同じFactが選ばれ続けることを確認する。
実DBのShrine ID（1, 50等）には依存しない。
"""

from __future__ import annotations

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.evidence_gate import decide_fact_usability
from temples.services.shrine_knowledge_selector import (
    fetch_fact_ready_knowledge_deities,
    fetch_fact_ready_knowledge_histories,
)

pytestmark = pytest.mark.django_db


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
        verification_status=verification_status,
    )
    if verification_status in ("source_confirmed", "reviewed"):
        defaults["verified_at"] = timezone.now()
    defaults.update(kwargs)
    return ShrineKnowledgeSource.objects.create(**defaults)


def _create_deity(shrine: Shrine, display_name: str, sort_order: int, **kwargs) -> ShrineDeity:
    defaults = dict(
        display_name=display_name,
        verification_status="source_confirmed",
        confidence="high",
        sort_order=sort_order,
        verified_at=timezone.now(),
    )
    defaults.update(kwargs)
    return ShrineDeity.objects.create(shrine=shrine, **defaults)


def _create_history(shrine: Shrine, title: str, sort_order: int, **kwargs) -> ShrineHistory:
    defaults = dict(
        history_type="founding",
        title=title,
        content="内容",
        verification_status="source_confirmed",
        confidence="high",
        sort_order=sort_order,
        verified_at=timezone.now(),
    )
    defaults.update(kwargs)
    return ShrineHistory.objects.create(shrine=shrine, **defaults)


# --- 明治神宮Pilot相当 ---


def test_meiji_jingu_equivalent_pilot_is_usable_on_both_paths():
    shrine = _create_shrine("Pilot監査-明治神宮相当")
    source = _create_source("公式サイト「明治神宮とは」")

    deity1 = _create_deity(shrine, "明治天皇", sort_order=0)
    deity2 = _create_deity(shrine, "昭憲皇太后", sort_order=1)
    history = _create_history(shrine, "明治神宮の創建", sort_order=0)
    for fact in (deity1, deity2, history):
        fact.sources.add(source)

    for fact in (deity1, deity2, history):
        decision = decide_fact_usability(
            verification_status=fact.verification_status,
            confidence=fact.confidence,
            source_verification_statuses=[s.verification_status for s in fact.sources.all()],
        )
        assert decision.usable is True

    deities_result = fetch_fact_ready_knowledge_deities([shrine.id])
    histories_result = fetch_fact_ready_knowledge_histories([shrine.id])
    assert len(deities_result.get(shrine.id, [])) == 2
    assert len(histories_result.get(shrine.id, [])) == 1

    client = APIClient()
    resp = client.get(f"/api/shrines/{shrine.id}/")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["deities"]) == 2
    assert len(body["histories"]) == 1


# --- 品川神社Pilot相当 ---


def test_shinagawa_jinja_equivalent_pilot_preserves_differing_source_relations():
    shrine = _create_shrine("Pilot監査-品川神社相当")
    source_a = _create_source("品川神社公式")
    source_b = _create_source("東京都神社庁")

    deity1 = _create_deity(shrine, "天比理乃咩命", sort_order=0)
    deity2 = _create_deity(shrine, "宇賀之売命", sort_order=1)
    deity3 = _create_deity(shrine, "素盞嗚尊", sort_order=2)
    for deity in (deity1, deity2, deity3):
        deity.sources.add(source_a, source_b)

    history1 = _create_history(shrine, "1187年の創始", sort_order=0)
    history1.sources.add(source_a, source_b)
    history2 = _create_history(shrine, "1319年の奉祀", sort_order=1)
    history2.sources.add(source_a)
    history3 = _create_history(shrine, "1478年の奉祀", sort_order=2)
    history3.sources.add(source_a)

    for fact in (deity1, deity2, deity3, history1, history2, history3):
        decision = decide_fact_usability(
            verification_status=fact.verification_status,
            confidence=fact.confidence,
            source_verification_statuses=[s.verification_status for s in fact.sources.all()],
        )
        assert decision.usable is True

    deities_result = fetch_fact_ready_knowledge_deities([shrine.id])[shrine.id]
    histories_result = fetch_fact_ready_knowledge_histories([shrine.id])[shrine.id]
    assert len(deities_result) == 3
    assert [d["sort_order"] for d in deities_result] == [0, 1, 2]
    assert len(histories_result) == 3
    assert [h["sort_order"] for h in histories_result] == [0, 1, 2]

    client = APIClient()
    resp = client.get(f"/api/shrines/{shrine.id}/")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["deities"]) == 3
    assert len(body["histories"]) == 3
    assert [d["sort_order"] for d in body["deities"]] == [0, 1, 2]
    assert [h["sort_order"] for h in body["histories"]] == [0, 1, 2]

    # Source Relationの差(1187=A+B, 1319/1478=Aのみ)がDetail nested sourcesへ
    # そのまま反映されることを確認する。
    histories_by_title = {h["title"]: h for h in body["histories"]}
    assert {s["id"] for s in histories_by_title["1187年の創始"]["sources"]} == {
        source_a.id,
        source_b.id,
    }
    assert {s["id"] for s in histories_by_title["1319年の奉祀"]["sources"]} == {source_a.id}
    assert {s["id"] for s in histories_by_title["1478年の奉祀"]["sources"]} == {source_a.id}
