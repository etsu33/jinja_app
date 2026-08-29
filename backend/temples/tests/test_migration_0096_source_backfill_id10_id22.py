# backend/temples/tests/test_migration_0096_source_backfill_id10_id22.py
"""Behavioral tests for temples.0096_source_backfill_id10_id22.

P4 — `docs/audit/source-backfill-id10-id22-reproducibility.md`.

The migration's forward/reverse callables are exercised directly against the
real models via a tiny `apps` shim (GIS/nogis-independent).
"""

import importlib

import pytest
from django.utils import timezone

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services import evidence_gate
from temples.services.shrine_knowledge_selector import fetch_fact_ready_knowledge_histories

_mod = importlib.import_module("temples.migrations.0096_source_backfill_id10_id22")
apply_backfill = _mod.apply_source_backfill
revert_backfill = _mod.revert_source_backfill

SRC10_URL = "https://online.bunka.go.jp/heritages/detail/160978"
SRC22_URL = "https://www.dentou-hasshin.bunka.go.jp/search/158.html"


class _Apps:
    _models = {
        "Shrine": Shrine,
        "ShrineHistory": ShrineHistory,
        "ShrineKnowledgeSource": ShrineKnowledgeSource,
        "ShrineDeity": ShrineDeity,
    }

    def get_model(self, app_label, model_name):
        assert app_label == "temples"
        return self._models[model_name]


APPS = _Apps()


def _src(source_type, url, vs="source_confirmed", conf="high"):
    kw = dict(source_type=source_type, title="既存出典", url=url, verification_status=vs, confidence=conf)
    if vs in ("source_confirmed", "reviewed"):
        kw["verified_at"] = timezone.now()
    return ShrineKnowledgeSource.objects.create(**kw)


@pytest.fixture
def targets(db):
    """Recreate the relevant Production shape for ids 10 and 22."""
    s10 = Shrine.objects.create(
        id=10, name_jp="鶴岡八幡宮", address="神奈川県鎌倉市雪ノ下2-1-31", kind="shrine",
        goriyaku="勝運・仕事運・厄除け",
    )
    s22 = Shrine.objects.create(
        id=22, name_jp="給田六所神社", address="日本、〒157-0064 東京都世田谷区給田１丁目３−７",
        kind="shrine", goriyaku="地域の氏神として、暮らしや家内安全、日々の無事を見守る神社。",
    )
    # pre-existing non-primary sources
    s10_tour = _src("tourism_official", "https://www.trip-kamakura.com/place/japanheritage/209.html")
    s10_wiki = _src("secondary_editorial", "https://ja.wikipedia.org/wiki/tsurugaoka")
    s22_wiki = _src("secondary_editorial", "https://ja.wikipedia.org/wiki/rokusho", conf="medium")
    s22_tesshow = _src("local_history", "https://tesshow.jp/setagaya/shrine_kyuden_roksho.html", conf="medium")

    h13 = ShrineHistory.objects.create(
        id=13, shrine=s10, history_type="founding", title="由比若宮の勧請",
        content="康平6年(1063)8月、源頼義が石清水八幡宮を由比郷鶴岡へ勧請し、由比若宮とした。",
        sort_order=0, verification_status="source_confirmed", confidence="high", verified_at=timezone.now(),
    )
    h14 = ShrineHistory.objects.create(
        id=14, shrine=s10, history_type="historical_event", title="現在地への遷座",
        content="治承4年(1180)10月12日、源頼朝が現在の小林郷北山へ遷座した。",
        sort_order=1, verification_status="source_confirmed", confidence="high", verified_at=timezone.now(),
    )
    h15 = ShrineHistory.objects.create(
        id=15, shrine=s10, history_type="historical_event", title="源義家による修復",
        content="永保元年(1081)2月、源義家が修復を加えた。",
        sort_order=2, verification_status="source_confirmed", confidence="high", verified_at=timezone.now(),
    )
    h27 = ShrineHistory.objects.create(
        id=27, shrine=s22, history_type="founding", title="武蔵総社六所宮よりの分霊勧請",
        content="武蔵国府中の武蔵総社六所宮（現大國魂神社）の分霊を勧請して創建したのが起源と伝わる。",
        sort_order=0, verification_status="source_confirmed", confidence="medium", verified_at=timezone.now(),
    )
    h28 = ShrineHistory.objects.create(
        id=28, shrine=s22, history_type="historical_event", title="村社列格",
        content="村社に列格した。",
        sort_order=1, verification_status="source_confirmed", confidence="medium", verified_at=timezone.now(),
    )
    for h in (h13, h14, h15):
        h.sources.set([s10_tour, s10_wiki])
    for h in (h27, h28):
        h.sources.set([s22_wiki, s22_tesshow])

    d22 = ShrineDeity.objects.create(
        id=39, shrine=s22, display_name="大国魂大神", role="primary", sort_order=0,
        verification_status="source_confirmed", confidence="medium", verified_at=timezone.now(),
    )
    d22.sources.set([s22_wiki, s22_tesshow])

    return dict(s10=s10, s22=s22, h13=h13, h14=h14, h15=h15, h27=h27, h28=h28, d22=d22)


def _src_urls(fact):
    return set(fact.sources.values_list("url", flat=True))


# 1 / 8 — scope is exactly ids 10 / 22; unrelated shrine untouched
@pytest.mark.django_db
def test_scope_is_exactly_10_and_22(targets):
    other = Shrine.objects.create(id=90000, name_jp="無関係神社", address="どこか", kind="shrine")
    oh = ShrineHistory.objects.create(
        shrine=other, history_type="founding", title="無関係由緒", content="無関係",
        sort_order=0, verification_status="source_confirmed", confidence="high", verified_at=timezone.now(),
    )
    before_other = _src_urls(oh)

    apply_backfill(APPS, None)

    assert SRC10_URL in _src_urls(targets["h13"])
    assert SRC10_URL in _src_urls(targets["h14"])
    assert SRC22_URL in _src_urls(targets["h27"])
    assert _src_urls(oh) == before_other  # unrelated shrine unchanged


# 2 — identity guard blocks a wrong-row write
@pytest.mark.django_db
def test_identity_mismatch_is_noop(targets):
    targets["s10"].name_jp = "改名された神社"
    targets["s10"].save(update_fields=["name_jp"])

    apply_backfill(APPS, None)

    assert SRC10_URL not in _src_urls(targets["h13"])
    assert not ShrineKnowledgeSource.objects.filter(url=SRC10_URL).exists()
    # id22 still processed
    assert SRC22_URL in _src_urls(targets["h27"])


# place_ref-set duplicate row is not the target
@pytest.mark.django_db
def test_place_ref_duplicate_row_is_not_targeted(db):
    from temples.models import PlaceRef

    pr = PlaceRef.objects.create(place_id="ChIJ_dummy", name="給田六所神社")
    dup = Shrine.objects.create(
        id=101, name_jp="給田六所神社", address="日本、〒157-0064 東京都世田谷区給田１丁目３−７",
        kind="shrine", place_ref=pr,
    )
    dh = ShrineHistory.objects.create(
        id=27, shrine=dup, history_type="founding", title="武蔵総社六所宮よりの分霊勧請",
        content="x", sort_order=0, verification_status="source_confirmed", confidence="medium",
        verified_at=timezone.now(),
    )
    apply_backfill(APPS, None)
    # pk 22 does not exist here; the only 給田六所神社 row has place_ref → guarded out
    assert SRC22_URL not in _src_urls(dh)


# Local/Production reproducibility: target Facts are matched by stable identity
# (shrine_id + history_type + title), NEVER by ShrineHistory pk — which differs
# between the local dev DB and Production for the same seed Fact.
@pytest.mark.django_db
def test_history_matched_by_stable_identity_not_by_pk(db):
    s10 = Shrine.objects.create(
        id=10, name_jp="鶴岡八幡宮", address="神奈川県鎌倉市雪ノ下2-1-31", kind="shrine",
        goriyaku="勝運・仕事運・厄除け",
    )
    # same seed Fact as Production, but a *different* pk (dev-DB drift shape)
    h = ShrineHistory.objects.create(
        id=999_013, shrine=s10, history_type="founding", title="由比若宮の勧請",
        content="康平6年(1063)…", sort_order=0,
        verification_status="source_confirmed", confidence="high", verified_at=timezone.now(),
    )
    apply_backfill(APPS, None)
    assert SRC10_URL in _src_urls(h)


# 3 / 4 — only the reviewed Source is inserted, only onto Source-backed existing histories
@pytest.mark.django_db
def test_only_reviewed_source_and_only_named_histories(targets):
    apply_backfill(APPS, None)

    # exactly two new Source rows, exactly the reviewed URLs
    new = set(ShrineKnowledgeSource.objects.filter(url__in=[SRC10_URL, SRC22_URL]).values_list("url", "source_type"))
    assert new == {(SRC10_URL, "cultural_property"), (SRC22_URL, "government")}
    src10 = ShrineKnowledgeSource.objects.get(url=SRC10_URL)
    assert src10.verification_status == "source_confirmed" and src10.verified_at is not None

    # id10: related to h13, h14 — NOT h15 (not in the spec)
    assert SRC10_URL not in _src_urls(targets["h15"])
    # id22: related to h27 — NOT h28, NOT deity 39
    assert SRC22_URL not in _src_urls(targets["h28"])
    assert SRC22_URL not in set(targets["d22"].sources.values_list("url", flat=True))
    # no Fact was created
    assert ShrineHistory.objects.count() == 5
    assert ShrineDeity.objects.count() == 1


# 5 / 6 / 7 — idempotent, no duplicate Source rows, no duplicate relations
@pytest.mark.django_db
def test_idempotent_no_duplicate_sources_or_relations(targets):
    apply_backfill(APPS, None)
    apply_backfill(APPS, None)
    apply_backfill(APPS, None)

    assert ShrineKnowledgeSource.objects.filter(url=SRC10_URL).count() == 1
    assert ShrineKnowledgeSource.objects.filter(url=SRC22_URL).count() == 1
    assert targets["h13"].sources.filter(url=SRC10_URL).count() == 1
    assert targets["h27"].sources.filter(url=SRC22_URL).count() == 1
    # pre-existing sources still there
    assert targets["h13"].sources.count() == 3  # tour + wiki + new
    assert targets["h27"].sources.count() == 3  # wiki + tesshow + new


# 9 / 10 — no GoriyakuTag master change, no Need mapping change
@pytest.mark.django_db
def test_no_taxonomy_or_mapping_change(targets):
    from temples.domain.need_to_goriyaku_tag_ids import NEED_TO_GORIYAKU_IDS
    from temples.models import GoriyakuTag

    before_tags = GoriyakuTag.objects.count()
    before_map = {k: set(v) for k, v in NEED_TO_GORIYAKU_IDS.items()}

    apply_backfill(APPS, None)

    assert GoriyakuTag.objects.count() == before_tags
    assert {k: set(v) for k, v in NEED_TO_GORIYAKU_IDS.items()} == before_map
    # goriyaku text / tags untouched on both shrines
    targets["s10"].refresh_from_db()
    targets["s22"].refresh_from_db()
    assert targets["s10"].goriyaku == "勝運・仕事運・厄除け"
    assert targets["s22"].goriyaku == "地域の氏神として、暮らしや家内安全、日々の無事を見守る神社。"


# 12 — reverse removes exactly what forward added; pre-existing sources kept
@pytest.mark.django_db
def test_reverse_is_safe(targets):
    apply_backfill(APPS, None)
    revert_backfill(APPS, None)

    assert not ShrineKnowledgeSource.objects.filter(url__in=[SRC10_URL, SRC22_URL]).exists()
    assert SRC10_URL not in _src_urls(targets["h13"])
    assert SRC22_URL not in _src_urls(targets["h27"])
    # pre-existing provenance intact
    assert targets["h13"].sources.count() == 2
    assert targets["h27"].sources.count() == 2


@pytest.mark.django_db
def test_reverse_keeps_source_if_still_referenced_elsewhere(targets):
    apply_backfill(APPS, None)
    # simulate another Fact also citing the id10 source
    src10 = ShrineKnowledgeSource.objects.get(url=SRC10_URL)
    targets["h15"].sources.add(src10)

    revert_backfill(APPS, None)

    # relation removed from h13/h14 but the Source row survives (h15 still cites it)
    assert ShrineKnowledgeSource.objects.filter(url=SRC10_URL).exists()
    assert SRC10_URL not in _src_urls(targets["h13"])
    assert SRC10_URL in _src_urls(targets["h15"])


# 13 — Knowledge selector still works with the added Source relation
@pytest.mark.django_db
def test_knowledge_selector_unaffected(targets):
    before = fetch_fact_ready_knowledge_histories([10, 22])
    apply_backfill(APPS, None)
    after = fetch_fact_ready_knowledge_histories([10, 22])
    # same shrines, same fact-ready history counts (provenance-only change)
    assert {k: len(v) for k, v in before.items()} == {k: len(v) for k, v in after.items()}


# 14 — Evidence Gate semantics unchanged (the histories were already usable)
@pytest.mark.django_db
def test_evidence_gate_semantics_unchanged(targets):
    def usable(h):
        return evidence_gate.decide_fact_usability(
            verification_status=h.verification_status,
            confidence=h.confidence,
            source_verification_statuses=[s.verification_status for s in h.sources.all()],
        ).usable

    before = {h.id: usable(h) for h in ShrineHistory.objects.all()}
    apply_backfill(APPS, None)
    after = {hid: usable(ShrineHistory.objects.get(id=hid)) for hid in before}
    assert before == after
    assert all(after.values())  # all remain usable
