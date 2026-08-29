# backend/temples/tests/test_migration_0097_p5_id21_id22_tag_reconciliation.py
"""Behavioral tests for temples.0097_p5_id21_id22_tag_reconciliation.

P5-DATA — `docs/audit/p5-id21-id22-tag-reconciliation.md`.

Forward/reverse callables are exercised directly against the real models via a
tiny `apps` shim (GIS/nogis-independent).
"""

import importlib

import pytest

from temples.domain.need_to_goriyaku_tag_ids import (
    NEED_TO_GORIYAKU_IDS,
    need_tags_to_goriyaku_ids,
)
from temples.models import GoriyakuTag, Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource

_mod = importlib.import_module("temples.migrations.0097_p5_id21_id22_tag_reconciliation")
forward = _mod.reconcile_forward
reverse = _mod.reconcile_reverse

ID21_PROSE = "地域に根ざした稲荷社として、商売繁盛や五穀豊穣、日々の暮らしの安定を願う神社。"
ID22_PROSE = "地域の氏神として、暮らしや家内安全、日々の無事を見守る神社。"


class _Apps:
    _models = {
        "Shrine": Shrine,
        "GoriyakuTag": GoriyakuTag,
        "ShrineDeity": ShrineDeity,
        "ShrineHistory": ShrineHistory,
        "ShrineKnowledgeSource": ShrineKnowledgeSource,
    }

    def get_model(self, app_label, model_name):
        assert app_label == "temples"
        return self._models[model_name]


APPS = _Apps()

CANON = {
    1: "縁結び", 2: "厄除け", 3: "交通安全", 4: "商売繁盛", 5: "五穀豊穣", 6: "開運",
    7: "家内安全", 8: "福徳", 9: "学業成就", 10: "合格祈願", 11: "勝運", 12: "仕事運",
    13: "航海安全", 14: "海上安全", 15: "武運長久", 16: "安産", 17: "八方除", 18: "夫婦円満",
    19: "八難除", 20: "恋愛成就", 21: "導き", 22: "美容", 23: "方除け", 24: "健康長寿",
    25: "芸能", 26: "家庭円満", 27: "出世運", 28: "金運", 29: "芸能運", 30: "強運厄除け",
    31: "技芸上達", 32: "八方除け", 33: "病気平癒", 34: "火防", 35: "子宝", 36: "心願成就",
    37: "延命長寿", 38: "足腰健康", 39: "農業守護",
}


@pytest.fixture(autouse=True)
def _canonical_master(db):
    for i, name in CANON.items():
        GoriyakuTag.objects.update_or_create(id=i, defaults={"name": name})


def _tag(name):
    return GoriyakuTag.objects.get(name=name)


def _tag_names(shrine):
    return sorted(shrine.goriyaku_tags.values_list("name", flat=True))


@pytest.fixture
def targets(db):
    """Production catalog-row shape for ids 21 / 22 (canonical tag ids)."""
    s21 = Shrine.objects.create(
        id=21, name_jp="長太稲荷神社",
        address="日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０",
        kind="shrine", goriyaku=ID21_PROSE, history_theme="守り",
    )
    s22 = Shrine.objects.create(
        id=22, name_jp="給田六所神社",
        address="日本、〒157-0064 東京都世田谷区給田１丁目３−７",
        kind="shrine", goriyaku=ID22_PROSE, history_theme="守り",
    )
    s21.goriyaku_tags.set([_tag("商売繁盛"), _tag("五穀豊穣")])
    s22.goriyaku_tags.set([_tag("家内安全")])
    # id22 has Knowledge (unaffected by P5-DATA)
    src = ShrineKnowledgeSource.objects.create(
        source_type="secondary_editorial", title="Wikipedia", url="https://ja.wikipedia.org/wiki/rokusho",
        verification_status="source_confirmed", confidence="medium",
    )
    from django.utils import timezone
    src.verified_at = timezone.now()
    src.save(update_fields=["verified_at"])
    d = ShrineDeity.objects.create(
        shrine=s22, display_name="大国魂大神", role="primary", sort_order=0,
        verification_status="source_confirmed", confidence="medium", verified_at=timezone.now(),
    )
    d.sources.add(src)
    h = ShrineHistory.objects.create(
        shrine=s22, history_type="founding", title="武蔵総社六所宮よりの分霊勧請",
        content="…分霊を勧請して創建…", sort_order=0,
        verification_status="source_confirmed", confidence="medium", verified_at=timezone.now(),
    )
    h.sources.add(src)
    return dict(s21=s21, s22=s22, src=src, d22=d, h22=h)


# 1 / 4 / 5 / 6 — scope + the approved canonical removals
@pytest.mark.django_db
def test_forward_removes_the_approved_tags(targets):
    forward(APPS, None)
    targets["s21"].refresh_from_db()
    targets["s22"].refresh_from_db()
    assert _tag_names(targets["s21"]) == []   # 商売繁盛 + 五穀豊穣 removed
    assert _tag_names(targets["s22"]) == []   # 家内安全 removed


# 7 / 8 — 地域安泰 removed if present; safe no-op if absent (Production shape)
@pytest.mark.django_db
def test_chiiki_antai_absent_in_production_shape_is_safe_noop(targets):
    assert not GoriyakuTag.objects.filter(name="地域安泰").exists()  # Production 39-row master
    forward(APPS, None)  # must not raise, must not create the tag
    assert not GoriyakuTag.objects.filter(name="地域安泰").exists()


@pytest.mark.django_db
def test_chiiki_antai_removed_when_present_local_shape(targets):
    legacy = GoriyakuTag.objects.create(name="地域安泰")  # drifted-local-DB legacy label
    targets["s21"].goriyaku_tags.add(legacy)
    targets["s22"].goriyaku_tags.add(legacy)

    forward(APPS, None)

    targets["s21"].refresh_from_db()
    targets["s22"].refresh_from_db()
    assert "地域安泰" not in _tag_names(targets["s21"])
    assert "地域安泰" not in _tag_names(targets["s22"])
    assert GoriyakuTag.objects.filter(name="地域安泰").exists()  # row itself NOT deleted


# 2 — wrong shrine identity → no-op
@pytest.mark.django_db
def test_identity_mismatch_is_noop(targets):
    targets["s21"].name_jp = "別名になった神社"
    targets["s21"].save(update_fields=["name_jp"])
    forward(APPS, None)
    targets["s21"].refresh_from_db()
    assert set(_tag_names(targets["s21"])) == {"五穀豊穣", "商売繁盛"}  # untouched
    targets["s22"].refresh_from_db()
    assert _tag_names(targets["s22"]) == []  # id22 still processed


# 3 — place_ref-set duplicate shadow row untouched
@pytest.mark.django_db
def test_place_ref_shadow_row_untouched(db):
    from temples.models import PlaceRef

    pr = PlaceRef.objects.create(place_id="ChIJ_shadow", name="長太稲荷神社")
    shadow = Shrine.objects.create(
        id=103, name_jp="長太稲荷神社", address="日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０",
        kind="shrine", place_ref=pr,
    )
    shadow.goriyaku_tags.set([_tag("商売繁盛"), _tag("五穀豊穣")])
    forward(APPS, None)
    shadow.refresh_from_db()
    assert set(_tag_names(shadow)) == {"五穀豊穣", "商売繁盛"}  # shadow untouched (pk 21 absent here)


# 9 — unrelated tags on the target shrines remain
@pytest.mark.django_db
def test_unrelated_tags_on_targets_remain(targets):
    targets["s21"].goriyaku_tags.add(_tag("開運"))          # not in the removal list
    targets["s22"].goriyaku_tags.add(_tag("縁結び"))
    forward(APPS, None)
    targets["s21"].refresh_from_db()
    targets["s22"].refresh_from_db()
    assert _tag_names(targets["s21"]) == ["開運"]
    assert _tag_names(targets["s22"]) == ["縁結び"]


# 10 / 11 — raw goriyaku prose and history_theme are NOT modified (Decision P5-4)
@pytest.mark.django_db
def test_raw_goriyaku_and_history_theme_preserved(targets):
    forward(APPS, None)
    targets["s21"].refresh_from_db()
    targets["s22"].refresh_from_db()
    assert targets["s21"].goriyaku == ID21_PROSE
    assert targets["s21"].history_theme == "守り"
    assert targets["s22"].goriyaku == ID22_PROSE
    assert targets["s22"].history_theme == "守り"


# 12 — no GoriyakuTag master row created or deleted
@pytest.mark.django_db
def test_no_goriyaku_tag_master_change(targets):
    before = set(GoriyakuTag.objects.values_list("id", "name"))
    forward(APPS, None)
    assert set(GoriyakuTag.objects.values_list("id", "name")) == before
    assert GoriyakuTag.objects.count() == 39


# 13 — Need mapping unchanged
@pytest.mark.django_db
def test_need_mapping_unchanged(targets):
    before = {k: set(v) for k, v in NEED_TO_GORIYAKU_IDS.items()}
    forward(APPS, None)
    assert {k: set(v) for k, v in NEED_TO_GORIYAKU_IDS.items()} == before
    assert NEED_TO_GORIYAKU_IDS["travel_safe"] == {3, 13, 14}


# 14 / 15 — Knowledge Facts and Sources unchanged (id22)
@pytest.mark.django_db
def test_knowledge_and_sources_unchanged(targets):
    d_before = (targets["d22"].display_name, targets["d22"].verification_status, targets["d22"].confidence,
                set(targets["d22"].sources.values_list("url", flat=True)))
    h_before = (targets["h22"].title, targets["h22"].verification_status, targets["h22"].confidence,
                set(targets["h22"].sources.values_list("url", flat=True)))
    src_count = ShrineKnowledgeSource.objects.count()
    deity_count = ShrineDeity.objects.count()
    hist_count = ShrineHistory.objects.count()

    forward(APPS, None)

    targets["d22"].refresh_from_db()
    targets["h22"].refresh_from_db()
    assert (targets["d22"].display_name, targets["d22"].verification_status, targets["d22"].confidence,
            set(targets["d22"].sources.values_list("url", flat=True))) == d_before
    assert (targets["h22"].title, targets["h22"].verification_status, targets["h22"].confidence,
            set(targets["h22"].sources.values_list("url", flat=True))) == h_before
    assert ShrineKnowledgeSource.objects.count() == src_count
    assert ShrineDeity.objects.count() == deity_count
    assert ShrineHistory.objects.count() == hist_count


# 16 — forward idempotent
@pytest.mark.django_db
def test_forward_idempotent(targets):
    forward(APPS, None)
    forward(APPS, None)
    forward(APPS, None)
    targets["s21"].refresh_from_db()
    targets["s22"].refresh_from_db()
    assert _tag_names(targets["s21"]) == []
    assert _tag_names(targets["s22"]) == []


# 17 — reverse restores the intended pre-migration relations (canonical tags exist)
@pytest.mark.django_db
def test_reverse_restores_canonical_relations(targets):
    forward(APPS, None)
    reverse(APPS, None)
    targets["s21"].refresh_from_db()
    targets["s22"].refresh_from_db()
    assert set(_tag_names(targets["s21"])) == {"五穀豊穣", "商売繁盛"}
    assert _tag_names(targets["s22"]) == ["家内安全"]


# 18 — reverse does not create a missing legacy tag (地域安泰 absent → skipped)
@pytest.mark.django_db
def test_reverse_does_not_create_missing_legacy_tag(targets):
    forward(APPS, None)
    reverse(APPS, None)
    assert not GoriyakuTag.objects.filter(name="地域安泰").exists()
    # ...but a present 地域安泰 IS restored
    legacy = GoriyakuTag.objects.create(name="地域安泰")
    targets["s21"].goriyaku_tags.add(legacy)
    forward(APPS, None)
    reverse(APPS, None)
    targets["s21"].refresh_from_db()
    assert "地域安泰" in _tag_names(targets["s21"])


# 19 — PK drift does not affect semantic matching (name-based)
@pytest.mark.django_db
def test_pk_drift_name_based_matching(db):
    # simulate the drifted local table: same names at *different* pks
    GoriyakuTag.objects.filter(name__in=["商売繁盛", "五穀豊穣"]).delete()
    d_sho = GoriyakuTag.objects.create(id=9017, name="商売繁盛")
    d_go = GoriyakuTag.objects.create(id=9005, name="五穀豊穣")
    assert d_sho.id == 9017 and d_go.id == 9005

    s21 = Shrine.objects.create(
        id=21, name_jp="長太稲荷神社", address="日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０",
        kind="shrine", goriyaku=ID21_PROSE, history_theme="守り",
    )
    s21.goriyaku_tags.set([d_sho, d_go])

    forward(APPS, None)
    s21.refresh_from_db()
    assert _tag_names(s21) == []  # matched by name despite drifted pks


# 20 — id21 Recommendation `money` match disappears (M2M-derived)
@pytest.mark.django_db
def test_id21_money_match_disappears(targets):
    money_gids = need_tags_to_goriyaku_ids(["money"])
    before = set(targets["s21"].goriyaku_tags.values_list("id", flat=True)) & money_gids
    assert before  # currently matches money via 商売繁盛(4) / 五穀豊穣(5)

    forward(APPS, None)

    targets["s21"].refresh_from_db()
    after = set(targets["s21"].goriyaku_tags.values_list("id", flat=True)) & money_gids
    assert after == set()


# 21 — id22 Recommendation `health` / `rest` M2M match disappears
@pytest.mark.django_db
def test_id22_health_rest_match_disappears(targets):
    hr_gids = need_tags_to_goriyaku_ids(["health"]) | need_tags_to_goriyaku_ids(["rest"])
    before = set(targets["s22"].goriyaku_tags.values_list("id", flat=True)) & hr_gids
    assert before  # currently matches via 家内安全(7)

    forward(APPS, None)

    targets["s22"].refresh_from_db()
    after = set(targets["s22"].goriyaku_tags.values_list("id", flat=True)) & hr_gids
    assert after == set()


# 22 — an unrelated shrine's Recommendation-relevant M2M is stable
@pytest.mark.django_db
def test_unrelated_shrine_m2m_stable(targets):
    other = Shrine.objects.create(id=70123, name_jp="無関係神社", address="どこか", kind="shrine")
    other.goriyaku_tags.set([_tag("商売繁盛"), _tag("家内安全"), _tag("五穀豊穣")])
    before = set(_tag_names(other))
    forward(APPS, None)
    other.refresh_from_db()
    assert set(_tag_names(other)) == before
