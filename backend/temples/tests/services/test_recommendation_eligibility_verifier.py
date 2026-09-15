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
    ShrineIdentity,
    count_batch_candidates,
    load_batch_shrine_identities,
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


def test_load_batch_shrine_identities_resolves_w0_db01():
    identities = load_batch_shrine_identities("W0-DB01")

    assert len(identities) == 5
    assert count_batch_candidates("W0-DB01") == 5
    by_name = {i.name: i.address for i in identities}
    assert by_name["三輪神社"] == "愛知県名古屋市中区大須3-9-32"
    assert by_name["榴岡天満宮"] == "宮城県仙台市宮城野区榴ケ岡105-3"


def test_load_batch_shrine_identities_all_have_address():
    """canonical identityはaddress必須。name-onlyのidentityを返さない。"""
    for identity in load_batch_shrine_identities("W0-DB01"):
        assert identity.address.strip()


def test_load_batch_shrine_identities_unknown_batch_is_empty():
    assert load_batch_shrine_identities("W0-DB99") == []
    assert count_batch_candidates("W0-DB99") == 0


# ---------------------------------------------------------------------------
# canonical identity resolution
#
# Shrineは (name_jp, address, location) がunique。同名別所在の神社は実在するため、
# name-onlyでは一意に解決できない。--batch は Candidate Master の
# (official_name, official_address) を canonical identity として解決する。
# ---------------------------------------------------------------------------


_AMBIGUOUS_NAME = "諏訪神社"
_ADDRESS_A = "長野県諏訪市中洲1-1"
_ADDRESS_B = "北海道札幌市中央区2-2"


@pytest.fixture
def same_name_different_address() -> dict[str, Shrine]:
    """同名・別所在の2社。一方のみusable Factを持つ。"""
    a = _shrine(_AMBIGUOUS_NAME, address=_ADDRESS_A, latitude=36.0, longitude=138.1)
    b = _shrine(_AMBIGUOUS_NAME, address=_ADDRESS_B, latitude=43.0, longitude=141.3)
    attach_usable_deity_fact(a)
    return {"a": a, "b": b}


def test_shrine_name_stays_unresolved_for_same_name_different_address(
    same_name_different_address,
):
    """--shrine-name の挙動は不変。同名一致は推測解決せずUNRESOLVED。"""
    report = verify_recommendation_eligibility(shrine_names=[_AMBIGUOUS_NAME])

    result = report.results[0]
    assert result.status == UNRESOLVED
    assert result.shrine_id is None
    assert "name_jp matched multiple shrines" in (result.note or "")
    assert report.eligible_count == 0
    assert report.all_eligible is False


def test_canonical_identity_resolves_the_correct_shrine_deterministically(
    same_name_different_address,
):
    """(name_jp, address) はusable Factを持つ側を一意に解決する。"""
    eligible_side = same_name_different_address["a"]

    report = verify_recommendation_eligibility(
        shrine_identities=[ShrineIdentity(name=_AMBIGUOUS_NAME, address=_ADDRESS_A)],
    )

    result = report.results[0]
    assert result.status == ELIGIBLE
    assert result.shrine_id == eligible_side.id
    assert result.usable_deity_fact_count == 1
    assert report.all_eligible is True


def test_canonical_identity_resolves_the_other_shrine_independently(
    same_name_different_address,
):
    """同名でもaddressが異なればもう一方を独立に解決する（取り違えない）。"""
    ineligible_side = same_name_different_address["b"]

    report = verify_recommendation_eligibility(
        shrine_identities=[ShrineIdentity(name=_AMBIGUOUS_NAME, address=_ADDRESS_B)],
    )

    result = report.results[0]
    assert result.status == INELIGIBLE
    assert result.shrine_id == ineligible_side.id
    assert result.usable_fact_count == 0


def test_canonical_identity_resolution_is_deterministic_across_runs(
    same_name_different_address,
):
    identity = ShrineIdentity(name=_AMBIGUOUS_NAME, address=_ADDRESS_A)
    first = verify_recommendation_eligibility(shrine_identities=[identity]).results[0]
    second = verify_recommendation_eligibility(shrine_identities=[identity]).results[0]

    assert first.shrine_id == second.shrine_id
    assert first.status == second.status == ELIGIBLE


def test_canonical_identity_with_unknown_address_is_unresolved(
    same_name_different_address,
):
    """addressが一致しなければ、同名Shrineが存在しても解決しない。"""
    report = verify_recommendation_eligibility(
        shrine_identities=[ShrineIdentity(name=_AMBIGUOUS_NAME, address="存在しない住所")],
    )

    result = report.results[0]
    assert result.status == UNRESOLVED
    assert "(name_jp, address) not found" in (result.note or "")


def test_canonical_identity_label_is_reported_as_requested(
    same_name_different_address,
):
    report = verify_recommendation_eligibility(
        shrine_identities=[ShrineIdentity(name=_AMBIGUOUS_NAME, address=_ADDRESS_A)],
    )

    assert report.results[0].requested == f"{_AMBIGUOUS_NAME} / {_ADDRESS_A}"


def test_batch_command_uses_canonical_identity_not_name_only(
    same_name_different_address, tmp_path
):
    """--batch がCandidate Masterのcanonical identityで解決することを固定する。

    同名別所在の2社が存在する状況で、Candidate Masterが `official_address` に
    片方を指定していれば、その1社だけが解決される。
    """
    master = tmp_path / "candidate_master.json"
    master.write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "candidate_id": "amb-001",
                        "build_batch": "TEST-AMB",
                        "official_name": _AMBIGUOUS_NAME,
                        "official_address": _ADDRESS_A,
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    identities = load_batch_shrine_identities("TEST-AMB", path=master)
    assert identities == [ShrineIdentity(name=_AMBIGUOUS_NAME, address=_ADDRESS_A)]

    report = verify_recommendation_eligibility(shrine_identities=identities)
    assert report.results[0].shrine_id == same_name_different_address["a"].id
    assert report.results[0].status == ELIGIBLE


def test_batch_aborts_when_candidate_lacks_canonical_identity(tmp_path):
    """official_addressが欠けるCandidateを推測解決しない（件数差で中止）。"""
    master = tmp_path / "candidate_master.json"
    master.write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "candidate_id": "ok-001",
                        "build_batch": "TEST-PARTIAL",
                        "official_name": "住所あり神社",
                        "official_address": "東京都港区1-1",
                    },
                    {
                        "candidate_id": "ng-001",
                        "build_batch": "TEST-PARTIAL",
                        "candidate_name": "住所なし神社",
                        "official_name": "住所なし神社",
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert count_batch_candidates("TEST-PARTIAL", path=master) == 2
    assert len(load_batch_shrine_identities("TEST-PARTIAL", path=master)) == 1
