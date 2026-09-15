"""Shared Recommendation Eligibility read-only verifier のテスト。

検証対象（`temples.services.recommendation_eligibility_verifier`）:

- eligible shrine / ineligible shrine / unknown shrine の分類
- 結果を説明する最小限のEvidence件数
- **書き込み副作用が一切ないこと**

verifierは eligibility rule と Evidence Gate 条件を再実装しない。本テストも
新しい適格条件を定義せず、既存の `attach_usable_*_fact` helper が組み立てる
usable Fact の有無だけで期待値を決める。
"""

from __future__ import annotations

import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models.signals import (
    post_delete,
    post_save,
    pre_delete,
    pre_save,
)
from io import StringIO

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.recommendation_eligibility_verifier import (
    ELIGIBLE,
    INELIGIBLE,
    UNRESOLVED,
    load_batch_shrine_names,
    verify_recommendation_eligibility,
)
from temples.tests.support.recommendation_eligibility import (
    attach_usable_deity_fact,
    attach_usable_history_fact,
)

pytestmark = pytest.mark.django_db


def _shrine(
    name: str,
    *,
    address: str = "東京都千代田区1-1",
    latitude: float = 35.0,
    longitude: float = 139.0,
) -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )


# ---------------------------------------------------------------------------
# eligible shrine
# ---------------------------------------------------------------------------


def test_shrine_with_usable_deity_fact_is_eligible():
    shrine = _shrine("祭神あり神社")
    attach_usable_deity_fact(shrine)

    report = verify_recommendation_eligibility(shrine_ids=[shrine.id])

    assert len(report.results) == 1
    result = report.results[0]
    assert result.status == ELIGIBLE
    assert result.shrine_id == shrine.id
    assert result.name_jp == "祭神あり神社"
    assert result.usable_deity_fact_count == 1
    assert result.usable_history_fact_count == 0
    assert result.usable_fact_count == 1
    assert report.all_eligible is True


def test_shrine_with_usable_history_fact_is_eligible():
    shrine = _shrine("由緒あり神社")
    attach_usable_history_fact(shrine)

    report = verify_recommendation_eligibility(shrine_names=["由緒あり神社"])

    result = report.results[0]
    assert result.status == ELIGIBLE
    assert result.usable_deity_fact_count == 0
    assert result.usable_history_fact_count == 1


def test_evidence_counts_reflect_multiple_usable_facts():
    shrine = _shrine("両方あり神社")
    attach_usable_deity_fact(shrine, display_name="祭神A")
    attach_usable_deity_fact(shrine, display_name="祭神B")
    attach_usable_history_fact(shrine)

    result = verify_recommendation_eligibility(shrine_ids=[shrine.id]).results[0]

    assert result.status == ELIGIBLE
    assert result.usable_deity_fact_count == 2
    assert result.usable_history_fact_count == 1
    assert result.usable_fact_count == 3


# ---------------------------------------------------------------------------
# ineligible shrine
# ---------------------------------------------------------------------------


def test_shrine_without_usable_fact_is_ineligible():
    shrine = _shrine("Knowledgeなし神社")

    result = verify_recommendation_eligibility(shrine_ids=[shrine.id]).results[0]

    assert result.status == INELIGIBLE
    assert result.shrine_id == shrine.id
    assert result.usable_deity_fact_count == 0
    assert result.usable_history_fact_count == 0


def test_shrine_db_presence_alone_does_not_make_it_eligible():
    """Shrine DB presence != Recommendation eligibility。"""
    shrine = _shrine("DB存在のみ神社")

    report = verify_recommendation_eligibility(shrine_ids=[shrine.id])

    assert Shrine.objects.filter(id=shrine.id).exists()
    assert report.results[0].status == INELIGIBLE
    assert report.all_eligible is False


def test_fact_without_fact_ready_source_is_not_counted_as_usable():
    """Evidence Gateの判定をverifierが迂回しないこと。"""
    shrine = _shrine("出典未確認神社")
    deity = ShrineDeity.objects.create(
        shrine=shrine,
        display_name="出典未確認祭神",
        sort_order=0,
        verification_status="source_confirmed",
        confidence="high",
    )
    draft_source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="draft出典",
        verification_status="draft",
    )
    deity.sources.add(draft_source)

    result = verify_recommendation_eligibility(shrine_ids=[shrine.id]).results[0]

    assert result.status == INELIGIBLE
    assert result.usable_deity_fact_count == 0


# ---------------------------------------------------------------------------
# unknown / unresolvable shrine
# ---------------------------------------------------------------------------


def test_unknown_shrine_id_is_unresolved_not_eligible():
    report = verify_recommendation_eligibility(shrine_ids=[999_999])

    result = report.results[0]
    assert result.status == UNRESOLVED
    assert result.shrine_id is None
    assert "not found" in (result.note or "")
    assert report.eligible_count == 0
    assert report.all_eligible is False


def test_unknown_shrine_name_is_unresolved():
    report = verify_recommendation_eligibility(shrine_names=["存在しない神社"])

    assert report.results[0].status == UNRESOLVED
    assert report.unresolved_count == 1


def test_ambiguous_shrine_name_is_unresolved_not_guessed():
    """同名Shrineが複数ある場合、どれか1件を推測で採用しない。"""
    # Shrineは (name_jp, address, location) がunique。同名だがaddress/座標が
    # 異なる実在ケース（各地の同名神社）を再現する。
    first = _shrine("同名神社", address="東京都千代田区1-1", latitude=35.0, longitude=139.0)
    second = _shrine("同名神社", address="大阪府大阪市2-2", latitude=34.7, longitude=135.5)
    attach_usable_deity_fact(first)
    attach_usable_deity_fact(second)

    result = verify_recommendation_eligibility(shrine_names=["同名神社"]).results[0]

    assert result.status == UNRESOLVED
    assert "multiple" in (result.note or "")
    assert result.shrine_id is None


def test_unresolved_entry_does_not_pass_all_eligible():
    shrine = _shrine("適格神社")
    attach_usable_deity_fact(shrine)

    report = verify_recommendation_eligibility(
        shrine_ids=[shrine.id, 999_999],
    )

    assert report.eligible_count == 1
    assert report.unresolved_count == 1
    assert report.all_eligible is False


# ---------------------------------------------------------------------------
# no write side effects
# ---------------------------------------------------------------------------


_WATCHED_MODELS = (Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource)


class _WriteRecorder:
    """save / delete signalを捕捉して書き込み副作用を検出する。"""

    def __init__(self):
        self.writes: list[str] = []

    def __enter__(self):
        self._handlers = []
        for model in _WATCHED_MODELS:
            for signal, label in (
                (pre_save, "save"),
                (post_save, "save"),
                (pre_delete, "delete"),
                (post_delete, "delete"),
            ):
                handler = self._make_handler(model, label)
                signal.connect(handler, sender=model, weak=False)
                self._handlers.append((signal, handler, model))
        return self

    def __exit__(self, *exc):
        for signal, handler, model in self._handlers:
            signal.disconnect(handler, sender=model)
        return False

    def _make_handler(self, model, label):
        def _handler(*args, **kwargs):
            self.writes.append(f"{model.__name__}.{label}")

        return _handler


def test_verifier_performs_no_writes():
    eligible = _shrine("書き込み検査_適格")
    attach_usable_deity_fact(eligible)
    ineligible = _shrine("書き込み検査_不適格")

    before = {
        "shrine": Shrine.objects.count(),
        "deity": ShrineDeity.objects.count(),
        "history": ShrineHistory.objects.count(),
        "source": ShrineKnowledgeSource.objects.count(),
    }

    with _WriteRecorder() as recorder:
        report = verify_recommendation_eligibility(
            shrine_ids=[eligible.id, ineligible.id, 999_999],
            shrine_names=["書き込み検査_適格"],
        )

    assert recorder.writes == []
    assert report.eligible_count >= 1
    assert Shrine.objects.count() == before["shrine"]
    assert ShrineDeity.objects.count() == before["deity"]
    assert ShrineHistory.objects.count() == before["history"]
    assert ShrineKnowledgeSource.objects.count() == before["source"]


def test_command_performs_no_writes():
    shrine = _shrine("command書き込み検査")
    attach_usable_history_fact(shrine)

    out = StringIO()
    with _WriteRecorder() as recorder:
        call_command(
            "verify_recommendation_eligibility",
            "--shrine-id",
            str(shrine.id),
            stdout=out,
        )

    assert recorder.writes == []
    assert "ELIGIBLE" in out.getvalue()


# ---------------------------------------------------------------------------
# command interface
# ---------------------------------------------------------------------------


def test_command_json_output_shape():
    shrine = _shrine("JSON出力神社")
    attach_usable_deity_fact(shrine)

    out = StringIO()
    call_command(
        "verify_recommendation_eligibility",
        "--shrine-id",
        str(shrine.id),
        "--json",
        stdout=out,
    )

    payload = json.loads(out.getvalue())
    assert payload["summary"]["eligible_count"] == 1
    assert payload["summary"]["all_eligible"] is True
    entry = payload["results"][0]
    assert entry["status"] == ELIGIBLE
    assert entry["usable_deity_fact_count"] == 1


def test_command_requires_a_target():
    with pytest.raises(CommandError):
        call_command("verify_recommendation_eligibility")


def test_require_all_eligible_fails_on_ineligible():
    shrine = _shrine("Gate検査_不適格")

    out = StringIO()
    with pytest.raises(CommandError):
        call_command(
            "verify_recommendation_eligibility",
            "--shrine-id",
            str(shrine.id),
            "--require-all-eligible",
            stdout=out,
        )


# ---------------------------------------------------------------------------
# batch membership resolution
# ---------------------------------------------------------------------------


def test_load_batch_shrine_names_resolves_w0_db01():
    names = load_batch_shrine_names("W0-DB01")

    assert len(names) == 5
    assert "三輪神社" in names
    assert "榴岡天満宮" in names


def test_load_batch_shrine_names_unknown_batch_is_empty():
    assert load_batch_shrine_names("W0-DB99") == []
