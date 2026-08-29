# backend/temples/tests/test_migration_0095_batch17_recommendation_evidence.py
"""Behavioral tests for temples.0095_batch17_recommendation_evidence_activation.

P3 — `docs/audit/batch17-recommendation-evidence-review.md`.

The migration's forward/reverse callables are exercised directly against the
real models via a tiny `apps` shim, so the test is independent of the GIS /
nogis migration-graph split.
"""

import importlib

import pytest

from temples.models import GoriyakuTag, Shrine

_mod = importlib.import_module(
    "temples.migrations.0095_batch17_recommendation_evidence_activation"
)
activate = _mod.activate_batch17_evidence
deactivate = _mod.deactivate_batch17_evidence

# Expected activation from the review (kept in sync with the migration constant).
EXPECTED = {
    107: (
        "建部大社",
        "滋賀県大津市神領1-16-1",
        ["開運", "厄除け", "出世運", "勝運", "縁結び", "商売繁盛", "家内安全", "病気平癒"],
    ),
    108: (
        "波上宮",
        "沖縄県那覇市若狭1-25-11",
        ["海上安全", "家内安全", "商売繁盛", "厄除け", "安産", "交通安全", "合格祈願", "心願成就"],
    ),
}


class _Apps:
    """Minimal `apps` shim: `get_model` returns the real current models."""

    _models = {"Shrine": Shrine, "GoriyakuTag": GoriyakuTag}

    def get_model(self, app_label, model_name):
        assert app_label == "temples"
        return self._models[model_name]


APPS = _Apps()


@pytest.fixture(autouse=True)
def _canonical_master(db):
    """The 39-row canonical GoriyakuTag master (ids 1..39), as in Production."""
    names = [
        "縁結び", "厄除け", "交通安全", "商売繁盛", "五穀豊穣", "開運", "家内安全", "福徳",
        "学業成就", "合格祈願", "勝運", "仕事運", "航海安全", "海上安全", "武運長久", "安産",
        "八方除", "夫婦円満", "八難除", "恋愛成就", "導き", "美容", "方除け", "健康長寿",
        "芸能", "家庭円満", "出世運", "金運", "芸能運", "強運厄除け", "技芸上達", "八方除け",
        "病気平癒", "火防", "子宝", "心願成就", "延命長寿", "足腰健康", "農業守護",
    ]
    for i, name in enumerate(names, start=1):
        GoriyakuTag.objects.update_or_create(id=i, defaults={"name": name})


def _mk(pk, name, address, goriyaku="", tags=()):
    s = Shrine.objects.create(id=pk, name_jp=name, address=address, goriyaku=goriyaku, kind="shrine")
    if tags:
        s.goriyaku_tags.set(list(tags))
    return s


def _mk_targets():
    return {pk: _mk(pk, name, addr) for pk, (name, addr, _labels) in EXPECTED.items()}


def _tag_names(shrine):
    return list(shrine.goriyaku_tags.order_by("id").values_list("name", flat=True))


# 1 / 3 / 4 / 5 — only PASS labels are written, they all exist, M2M == PASS set
@pytest.mark.django_db
def test_forward_writes_exactly_the_pass_label_set():
    shrines = _mk_targets()
    activate(APPS, None)

    for pk, (_n, _a, labels) in EXPECTED.items():
        s = shrines[pk]
        s.refresh_from_db()
        assert s.goriyaku == "・".join(labels)
        assert set(_tag_names(s)) == set(labels)
        assert s.goriyaku_tags.count() == len(labels)


# 2 — HOLD / UNKNOWN / NO_EVIDENCE candidates never appear
@pytest.mark.django_db
def test_hold_and_unknown_candidates_are_not_written():
    shrines = _mk_targets()
    activate(APPS, None)

    forbidden = {"災難除", "醸造", "健康祈願", "攘災招福", "良縁祈願", "航海安全", "健康長寿"}
    for pk in EXPECTED:
        s = shrines[pk]
        s.refresh_from_db()
        assert forbidden.isdisjoint(set(_tag_names(s)))
        assert forbidden.isdisjoint(set(s.goriyaku.split("・")))
    # 106 北海道神宮 (UNKNOWN, Source unreachable) is not in the activation set at all.
    assert 106 not in EXPECTED


# 4 — no new GoriyakuTag is created
@pytest.mark.django_db
def test_no_new_goriyaku_tag_is_created():
    _mk_targets()
    before = set(GoriyakuTag.objects.values_list("id", "name"))
    activate(APPS, None)
    after = set(GoriyakuTag.objects.values_list("id", "name"))
    assert before == after
    assert GoriyakuTag.objects.count() == 39


# 6 — scoped to ids 107/108 only (106 untouched, unrelated untouched)
@pytest.mark.django_db
def test_activation_is_scoped_to_107_108_only():
    shrines = _mk_targets()
    shrine_106 = _mk(106, "北海道神宮", "北海道札幌市中央区宮ヶ丘474")
    unrelated = _mk(50000, "無関係神社", "東京都どこか区", goriyaku="", tags=[])

    activate(APPS, None)

    shrine_106.refresh_from_db()
    assert shrine_106.goriyaku == ""
    assert shrine_106.goriyaku_tags.count() == 0

    unrelated.refresh_from_db()
    assert unrelated.goriyaku == ""
    assert unrelated.goriyaku_tags.count() == 0

    for pk in EXPECTED:
        shrines[pk].refresh_from_db()
        assert shrines[pk].goriyaku != ""


# 7 — idempotent
@pytest.mark.django_db
def test_forward_is_idempotent():
    shrines = _mk_targets()
    activate(APPS, None)
    snapshot = {
        pk: (shrines[pk].goriyaku, set(_tag_names(shrines[pk])))
        for pk in EXPECTED
        for _ in [shrines[pk].refresh_from_db()]
    }
    activate(APPS, None)
    activate(APPS, None)
    for pk in EXPECTED:
        shrines[pk].refresh_from_db()
        assert (shrines[pk].goriyaku, set(_tag_names(shrines[pk]))) == snapshot[pk]


# 8 — a target already carrying goriyaku/tags is left untouched (drift self-guard)
@pytest.mark.django_db
def test_target_with_preexisting_state_is_not_overwritten():
    pre = _mk(107, "建部大社", "滋賀県大津市神領1-16-1", goriyaku="別のご利益", tags=[GoriyakuTag.objects.get(id=6)])
    ok = _mk(108, *EXPECTED[108][:2])

    activate(APPS, None)

    pre.refresh_from_db()
    assert pre.goriyaku == "別のご利益"
    assert _tag_names(pre) == ["開運"]

    ok.refresh_from_db()
    assert ok.goriyaku == "・".join(EXPECTED[108][2])


# name/address mismatch → that shrine is a no-op
@pytest.mark.django_db
def test_pk_present_but_identity_mismatch_is_noop():
    wrong = _mk(107, "別の神社になった", "想定外の住所")
    ok = _mk(108, *EXPECTED[108][:2])

    activate(APPS, None)

    wrong.refresh_from_db()
    assert wrong.goriyaku == ""
    assert wrong.goriyaku_tags.count() == 0
    ok.refresh_from_db()
    assert ok.goriyaku != ""


# missing canonical label → whole shrine is a no-op, never get_or_create
@pytest.mark.django_db
def test_missing_canonical_label_makes_that_shrine_noop():
    GoriyakuTag.objects.filter(name="病気平癒").delete()  # 107 needs it
    s107 = _mk(107, *EXPECTED[107][:2])
    s108 = _mk(108, *EXPECTED[108][:2])

    activate(APPS, None)

    s107.refresh_from_db()
    assert s107.goriyaku == ""
    assert s107.goriyaku_tags.count() == 0
    # 108 does not need 病気平癒 → still activates
    s108.refresh_from_db()
    assert s108.goriyaku == "・".join(EXPECTED[108][2])
    assert GoriyakuTag.objects.count() == 38  # nothing re-created


# reverse restores empty state (only when current state matches what we wrote)
@pytest.mark.django_db
def test_reverse_restores_empty_state():
    shrines = _mk_targets()
    activate(APPS, None)
    deactivate(APPS, None)
    for pk in EXPECTED:
        shrines[pk].refresh_from_db()
        assert shrines[pk].goriyaku == ""
        assert shrines[pk].goriyaku_tags.count() == 0


@pytest.mark.django_db
def test_reverse_leaves_a_later_edit_alone():
    shrines = _mk_targets()
    activate(APPS, None)
    s = shrines[108]
    s.refresh_from_db()
    s.goriyaku = "後から編集された"
    s.save(update_fields=["goriyaku"])

    deactivate(APPS, None)

    s.refresh_from_db()
    assert s.goriyaku == "後から編集された"  # not clobbered
    # 107 (unedited) still reverts
    shrines[107].refresh_from_db()
    assert shrines[107].goriyaku == ""


# 9 / 10 — Evidence Gate and Need mapping are import-time constants, untouched here.
@pytest.mark.django_db
def test_need_mapping_and_evidence_gate_untouched_by_this_migration():
    from temples.domain.need_to_goriyaku_tag_ids import NEED_TO_GORIYAKU_IDS
    from temples.services import evidence_gate

    _mk_targets()
    before_map = {k: set(v) for k, v in NEED_TO_GORIYAKU_IDS.items()}
    before_gate = evidence_gate.FACT_READY_VERIFICATION_STATUSES

    activate(APPS, None)

    assert {k: set(v) for k, v in NEED_TO_GORIYAKU_IDS.items()} == before_map
    assert NEED_TO_GORIYAKU_IDS["travel_safe"] == {3, 13, 14}
    assert evidence_gate.FACT_READY_VERIFICATION_STATUSES == before_gate
