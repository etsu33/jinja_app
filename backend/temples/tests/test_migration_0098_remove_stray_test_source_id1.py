# backend/temples/tests/test_migration_0098_remove_stray_test_source_id1.py
"""Behavioral tests for temples.0098_remove_stray_test_source_id1.

P6-DATA — `docs/audit/p6-id1-user-observation-data-review.md`.

`P6_0098_PRESTATE_POLICY = FAIL_CLOSED`: forward runs only when the COMPLETE
audited PRE state is present and raises `RuntimeError` ("PRESTATE_MISMATCH")
otherwise (aborting the migration transaction). There is no "successful no-op"
path.

Forward/reverse callables are exercised directly against the real models via a
tiny `apps` shim (GIS/nogis-independent), matching the 0095 / 0096 / 0097
migration-test pattern. `conftest._ensure_shrine_exists` (autouse) always
provides `Shrine` pk 1, so these tests reshape that row into 明治神宮.
"""

import importlib
import json
from pathlib import Path

import pytest
from django.db.models import Max
from django.utils import timezone

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services import evidence_gate
from temples.services.shrine_knowledge_selector import fetch_fact_ready_knowledge_deities

_mod = importlib.import_module("temples.migrations.0098_remove_stray_test_source_id1")
forward = _mod.remove_stray_source
reverse = _mod.restore_stray_source
STRAY = _mod.STRAY_SOURCE
STRAY_SEED = _mod.STRAY_SOURCE_SEED

OFFICIAL_URL = "https://www.meijijingu.or.jp/about/"
MISMATCH = "PRESTATE_MISMATCH"


class _Apps:
    _models = {
        "Shrine": Shrine,
        "ShrineDeity": ShrineDeity,
        "ShrineHistory": ShrineHistory,
        "ShrineKnowledgeSource": ShrineKnowledgeSource,
    }

    def get_model(self, app_label, model_name):
        assert app_label == "temples"
        return self._models[model_name]


APPS = _Apps()


def _mk_stray(**overrides):
    kw = dict(STRAY_SEED)
    kw.update(overrides)
    if kw.get("verified_at"):
        kw["verified_at"] = timezone.now()
    return ShrineKnowledgeSource.objects.create(**kw)


def _mk_official():
    return ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="明治神宮 公式サイト「明治神宮とは」",
        publisher="明治神宮",
        url=OFFICIAL_URL,
        verification_status="source_confirmed",
        confidence="high",
        verified_at=timezone.now(),
    )


def _reshape_shrine1_as_meiji():
    s1 = Shrine.objects.get(pk=1)
    s1.name_jp = "明治神宮"
    s1.address = "東京都渋谷区代々木神園町1-1"
    s1.place_ref = None
    s1.latitude, s1.longitude = 35.6764, 139.6993
    s1.save()
    ShrineDeity.objects.filter(shrine_id=1).delete()
    ShrineHistory.objects.filter(shrine_id=1).delete()
    ShrineKnowledgeSource.objects.filter(source_type="user_observation").delete()
    return s1


def _new_shrine(name_jp):
    next_id = (Shrine.objects.aggregate(m=Max("id"))["m"] or 0) + 1000
    return Shrine.objects.create(id=next_id, name_jp=name_jp, address="x", kind="shrine")


def _mk_deity(shrine, display_name, sort_order):
    return ShrineDeity.objects.create(
        shrine=shrine, display_name=display_name, canonical_name=display_name,
        role="enshrined", sort_order=sort_order,
        verification_status="source_confirmed", confidence="high", verified_at=timezone.now(),
    )


@pytest.fixture
def prod_shape(db):
    """The exact audited Production PRE shape for Shrine id 1 (明治神宮)."""
    s1 = _reshape_shrine1_as_meiji()
    official = _mk_official()
    stray = _mk_stray()

    d_meiji = _mk_deity(s1, "明治天皇", 0)
    d_shoken = _mk_deity(s1, "昭憲皇太后", 1)
    for d in (d_meiji, d_shoken):
        d.sources.set([official, stray])

    h = ShrineHistory.objects.create(
        shrine=s1, history_type="official_origin", title="明治神宮の創建",
        content="明治神宮は、東京都渋谷区代々木に大正9年（1920）に創建された。",
        sort_order=0, verification_status="source_confirmed", confidence="high", verified_at=timezone.now(),
    )
    h.sources.set([official])

    return dict(s1=s1, official=official, stray=stray, d_meiji=d_meiji, d_shoken=d_shoken, h=h)


def _stray_qs():
    return ShrineKnowledgeSource.objects.filter(**STRAY)


def _src_ids(fact):
    fact.refresh_from_db()
    return set(fact.sources.values_list("id", flat=True))


def _semantic_snapshot():
    """A pk-independent snapshot of everything this migration could plausibly
    touch (relations are keyed by the linked Source's semantic identity, so a
    recreated-with-a-new-pk Source still compares equal)."""
    return {
        "sources": sorted(
            ShrineKnowledgeSource.objects.values_list(
                "source_type", "title", "publisher", "url", "bibliography",
                "verification_status", "confidence",
            )
        ),
        "deity_links": sorted(
            ShrineDeity.objects.filter(shrine_id=1)
            .values_list("display_name", "sources__source_type", "sources__title")
        ),
        "history_links": sorted(
            ShrineHistory.objects.filter(shrine_id=1)
            .values_list("title", "sources__source_type", "sources__title")
        ),
    }


# 1 — exact Production-shaped PRE → forward succeeds
@pytest.mark.django_db
def test_valid_prestate_forward_succeeds(prod_shape):
    forward(APPS, None)
    assert not _stray_qs().exists()
    assert _src_ids(prod_shape["d_meiji"]) == {prod_shape["official"].id}
    assert _src_ids(prod_shape["d_shoken"]) == {prod_shape["official"].id}


# applicability boundary — no Shrine pk 1 row at all → clean no-op (fresh DB)
@pytest.mark.django_db
def test_no_shrine1_row_is_clean_noop(db):
    # Raw delete to bypass the ORM cascade collector (unrelated to this
    # migration); conftest's autouse fixture created Shrine pk 1.
    from django.db import connection

    with connection.cursor() as cur:
        cur.execute("DELETE FROM temples_shrine WHERE id = 1")
    assert not Shrine.objects.filter(pk=1).exists()

    forward(APPS, None)   # must NOT raise
    reverse(APPS, None)   # must NOT raise
    assert not _stray_qs().exists()  # reverse did not fabricate anything


# 2 — zero Source PRE (Shrine pk 1 present) → forward raises / aborts
@pytest.mark.django_db
def test_zero_source_forward_raises(db):
    _reshape_shrine1_as_meiji()  # 明治神宮 present, but no stray Source, no deities
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)


@pytest.mark.django_db
def test_zero_source_but_full_deities_forward_raises(prod_shape):
    # stray Source removed, deities + relations otherwise intact
    prod_shape["d_meiji"].sources.set([prod_shape["official"]])
    prod_shape["d_shoken"].sources.set([prod_shape["official"]])
    prod_shape["stray"].delete()
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)


# 3 — multiple Source PRE → forward raises / aborts
@pytest.mark.django_db
def test_multiple_source_matches_forward_raises(prod_shape):
    dup = _mk_stray()
    prod_shape["d_meiji"].sources.add(dup)
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)
    assert _stray_qs().count() == 2  # nothing deleted


# 4 — wrong Shrine identity → forward raises / aborts
@pytest.mark.django_db
def test_wrong_shrine_identity_forward_raises(prod_shape):
    prod_shape["s1"].name_jp = "改名された神社"
    prod_shape["s1"].save(update_fields=["name_jp"])
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)
    assert _stray_qs().exists()


# 5 — place_ref-set identity → forward raises / aborts
@pytest.mark.django_db
def test_place_ref_set_forward_raises(prod_shape):
    from temples.models import PlaceRef

    pr = PlaceRef.objects.create(place_id="ChIJ_shadow_meiji", name="明治神宮")
    prod_shape["s1"].place_ref = pr
    prod_shape["s1"].save(update_fields=["place_ref"])
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)
    assert _stray_qs().exists()


# 6 — semantic mismatch → forward raises / aborts
@pytest.mark.django_db
def test_semantic_mismatch_bibliography_forward_raises(prod_shape):
    prod_shape["stray"].bibliography = "何か別の書誌"
    prod_shape["stray"].save(update_fields=["bibliography"])
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)
    assert ShrineKnowledgeSource.objects.filter(id=prod_shape["stray"].id).exists()


@pytest.mark.django_db
def test_semantic_mismatch_nonempty_url_forward_raises(prod_shape):
    prod_shape["stray"].url = "https://example.org/observed"
    prod_shape["stray"].save(update_fields=["url"])
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)


# 7 — missing 明治天皇 → forward raises
@pytest.mark.django_db
def test_missing_meiji_deity_forward_raises(prod_shape):
    prod_shape["d_meiji"].delete()
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)
    assert _stray_qs().exists()


# 8 — missing 昭憲皇太后 → forward raises
@pytest.mark.django_db
def test_missing_shoken_deity_forward_raises(prod_shape):
    prod_shape["d_shoken"].delete()
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)
    assert _stray_qs().exists()


@pytest.mark.django_db
def test_duplicate_target_deity_forward_raises(prod_shape):
    extra = _mk_deity(prod_shape["s1"], "明治天皇", 2)  # a second 明治天皇 row
    extra.sources.set([prod_shape["official"], prod_shape["stray"]])
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)


# 9 — stray Source linked only to 明治天皇 → forward raises
@pytest.mark.django_db
def test_only_meiji_relation_present_forward_raises(prod_shape):
    prod_shape["d_shoken"].sources.set([prod_shape["official"]])  # drop stray from 昭憲皇太后
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)
    assert _stray_qs().exists()
    assert prod_shape["stray"].id in _src_ids(prod_shape["d_meiji"])  # untouched


# 10 — stray Source linked only to 昭憲皇太后 → forward raises
@pytest.mark.django_db
def test_only_shoken_relation_present_forward_raises(prod_shape):
    prod_shape["d_meiji"].sources.set([prod_shape["official"]])
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)
    assert prod_shape["stray"].id in _src_ids(prod_shape["d_shoken"])  # untouched


# 11 — neither target relation exists → forward raises
@pytest.mark.django_db
def test_neither_relation_present_forward_raises(prod_shape):
    prod_shape["d_meiji"].sources.set([prod_shape["official"]])
    prod_shape["d_shoken"].sources.set([prod_shape["official"]])
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)
    assert _stray_qs().exists()


@pytest.mark.django_db
def test_stray_source_referenced_elsewhere_forward_raises(prod_shape):
    # a third Fact (history) also cites the stray Source → not safely deletable
    prod_shape["h"].sources.add(prod_shape["stray"])
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)
    assert _stray_qs().exists()
    assert prod_shape["stray"].id in _src_ids(prod_shape["d_meiji"])


# 12 — failure leaves DB semantically unchanged
@pytest.mark.django_db
def test_failed_forward_leaves_db_unchanged(prod_shape):
    prod_shape["d_shoken"].sources.set([prod_shape["official"]])  # trip a guard
    before = _semantic_snapshot()
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)
    assert _semantic_snapshot() == before


# 13 — valid forward → reverse restores exact Source + exactly the two links
@pytest.mark.django_db
def test_reverse_restores_exact_prestate(prod_shape):
    before = _semantic_snapshot()

    forward(APPS, None)
    reverse(APPS, None)

    matches = list(_stray_qs())
    assert len(matches) == 1
    src = matches[0]
    assert (src.source_type, src.title, src.publisher, src.url, src.bibliography) == (
        "user_observation", "テスト神社 境内案内板", "テスト神社", "",
        "テスト神社境内案内板（2026-08-01現地確認）",
    )
    assert (src.verification_status, src.confidence, src.language, src.accessed_at) == (
        "source_confirmed", "medium", "ja", None,
    )
    assert src.id in _src_ids(prod_shape["d_meiji"])
    assert src.id in _src_ids(prod_shape["d_shoken"])
    assert src.id not in _src_ids(prod_shape["h"])
    # exact-state: only the stray Source pk may differ (row was recreated)
    assert _semantic_snapshot() == before


# 14 — valid forward → reverse → forward remains deterministic
@pytest.mark.django_db
def test_forward_reverse_forward_deterministic(prod_shape):
    forward(APPS, None)
    reverse(APPS, None)
    forward(APPS, None)  # PRE valid again → succeeds
    assert not _stray_qs().exists()
    assert _src_ids(prod_shape["d_meiji"]) == {prod_shape["official"].id}
    assert _src_ids(prod_shape["d_shoken"]) == {prod_shape["official"].id}


@pytest.mark.django_db
def test_second_forward_after_deletion_raises(prod_shape):
    forward(APPS, None)  # succeeds
    with pytest.raises(RuntimeError, match=MISMATCH):
        forward(APPS, None)  # stray Source now gone → PRESTATE_MISMATCH


@pytest.mark.django_db
def test_reverse_reuses_existing_source_no_duplicate(prod_shape):
    reverse(APPS, None)  # stray still present (forward not run) → reuse, not create
    assert _stray_qs().count() == 1
    assert _stray_qs().first().id == prod_shape["stray"].id
    # extra reverse still no duplicate
    reverse(APPS, None)
    assert _stray_qs().count() == 1


# 15 — genuine shrine_official Source remains untouched
@pytest.mark.django_db
def test_official_source_untouched(prod_shape):
    forward(APPS, None)
    assert ShrineKnowledgeSource.objects.filter(url=OFFICIAL_URL, source_type="shrine_official").count() == 1
    assert prod_shape["official"].id in _src_ids(prod_shape["d_meiji"])
    assert prod_shape["official"].id in _src_ids(prod_shape["d_shoken"])
    assert prod_shape["official"].id in _src_ids(prod_shape["h"])
    reverse(APPS, None)
    assert prod_shape["official"].id in _src_ids(prod_shape["d_meiji"])
    assert prod_shape["official"].id in _src_ids(prod_shape["h"])


# 16 — unrelated Source / history references remain untouched
@pytest.mark.django_db
def test_unrelated_references_untouched(prod_shape):
    other = _new_shrine("伏見稲荷大社")
    osrc = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official", title="ご祭神｜伏見稲荷大社", url="https://inari.jp/about/saijin/",
        verification_status="source_confirmed", confidence="high", verified_at=timezone.now(),
    )
    od = _mk_deity(other, "宇迦之御魂大神", 0)
    od.sources.set([osrc])

    forward(APPS, None)

    assert _src_ids(od) == {osrc.id}
    prod_shape["h"].refresh_from_db()
    assert prod_shape["h"].title == "明治神宮の創建"
    assert _src_ids(prod_shape["h"]) == {prod_shape["official"].id}
    assert ShrineDeity.objects.filter(shrine_id=1).count() == 2
    assert ShrineHistory.objects.filter(shrine_id=1).count() == 1


# 17 — PK drift still irrelevant (match is by semantic identity)
@pytest.mark.django_db
def test_pk_drift_still_irrelevant(db):
    s1 = _reshape_shrine1_as_meiji()
    official = _mk_official()
    stray = _mk_stray(id=999004)  # local-dev-style pk
    assert stray.id == 999004
    d_meiji = _mk_deity(s1, "明治天皇", 0)
    d_shoken = _mk_deity(s1, "昭憲皇太后", 1)
    for d in (d_meiji, d_shoken):
        d.sources.set([official, stray])

    forward(APPS, None)

    assert not ShrineKnowledgeSource.objects.filter(id=999004).exists()
    assert _src_ids(d_meiji) == {official.id}
    assert _src_ids(d_shoken) == {official.id}


# 18 — Evidence Gate usability for both deities unchanged
@pytest.mark.django_db
def test_evidence_gate_usability_unchanged(prod_shape):
    def usable(d):
        d.refresh_from_db()
        return evidence_gate.decide_fact_usability(
            verification_status=d.verification_status,
            confidence=d.confidence,
            source_verification_statuses=[s.verification_status for s in d.sources.all()],
        ).usable

    before = {d.id: usable(d) for d in (prod_shape["d_meiji"], prod_shape["d_shoken"])}
    assert all(before.values())
    forward(APPS, None)
    after = {d.id: usable(d) for d in (prod_shape["d_meiji"], prod_shape["d_shoken"])}
    assert after == before and all(after.values())


# 19 — Recommendation Knowledge payload unchanged
@pytest.mark.django_db
def test_recommendation_knowledge_payload_unchanged(prod_shape):
    before = fetch_fact_ready_knowledge_deities([1])
    forward(APPS, None)
    after = fetch_fact_ready_knowledge_deities([1])
    assert before == after
    assert [d["display_name"] for d in after.get(1, [])] == ["明治天皇", "昭憲皇太后"]
    assert [d["confidence"] for d in after.get(1, [])] == ["high", "high"]


@pytest.mark.django_db
def test_scoring_inputs_untouched(prod_shape):
    from temples.models import GoriyakuTag

    next_id = (GoriyakuTag.objects.aggregate(m=Max("id"))["m"] or 0) + 1000
    tag = GoriyakuTag.objects.create(id=next_id, name="P6テスト用タグ")
    prod_shape["s1"].goriyaku_tags.add(tag)
    prod_shape["s1"].goriyaku = "勝運・仕事運"
    prod_shape["s1"].save(update_fields=["goriyaku"])

    forward(APPS, None)

    prod_shape["s1"].refresh_from_db()
    assert set(prod_shape["s1"].goriyaku_tags.values_list("name", flat=True)) == {"P6テスト用タグ"}
    assert prod_shape["s1"].goriyaku == "勝運・仕事運"
    assert Shrine.objects.get(id=1).name_jp == "明治神宮"


@pytest.mark.django_db
def test_knowledge_coverage_delta(prod_shape):
    def snapshot():
        return dict(
            total_sources=ShrineKnowledgeSource.objects.count(),
            user_obs=ShrineKnowledgeSource.objects.filter(source_type="user_observation").count(),
            id1_deity_facts=ShrineDeity.objects.filter(shrine_id=1).count(),
            id1_history_facts=ShrineHistory.objects.filter(shrine_id=1).count(),
            id1_has_source=(
                ShrineDeity.objects.filter(shrine_id=1, sources__isnull=False).exists()
                or ShrineHistory.objects.filter(shrine_id=1, sources__isnull=False).exists()
            ),
        )

    before = snapshot()
    forward(APPS, None)
    after = snapshot()

    assert before["total_sources"] - after["total_sources"] == 1
    assert before["user_obs"] == 1 and after["user_obs"] == 0
    assert after["id1_deity_facts"] == before["id1_deity_facts"] == 2
    assert after["id1_history_facts"] == before["id1_history_facts"] == 1
    assert after["id1_has_source"] is True


# 20 — seed import no longer recreates src-999004 (BUNDLED_WITH_MIGRATION_PR)
def test_seed_no_longer_defines_the_test_source():
    seed_path = (
        Path(__file__).resolve().parents[1] / "data" / "knowledge_seeds" / "batch_1_7_seed.json"
    )
    text = seed_path.read_text(encoding="utf-8")
    raw = json.loads(text)
    keys = [s["key"] for s in raw["sources"]]
    assert "src-999004" not in keys
    assert not any(s.get("source_type") == "user_observation" for s in raw["sources"])
    assert "src-999004" not in text
    meiji = next(b for b in raw["shrines"] if b["shrine_ref"]["name_jp"] == "明治神宮")
    for d in meiji["deities"]:
        assert d["source_keys"] == ["src-999005"]
    official = next(s for s in raw["sources"] if s["key"] == "src-999005")
    assert official["source_type"] == "shrine_official"
    assert official["url"] == "https://www.meijijingu.or.jp/about/"
