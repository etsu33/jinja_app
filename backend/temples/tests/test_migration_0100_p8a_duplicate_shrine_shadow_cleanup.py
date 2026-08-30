# backend/temples/tests/test_migration_0100_p8a_duplicate_shrine_shadow_cleanup.py
"""Behavioral tests for temples.0100_p8a_duplicate_shrine_shadow_cleanup (P8-A).

`docs/audit/p8-identity-coordinate-remediation.md` §6-§19.

`P8_A_PRESTATE_POLICY = FAIL_CLOSED`: forward runs only when the COMPLETE
audited PRE state for all three shadow->primary pairs and the two audited
`ShrineInteractionLog` rows is present, and raises `PreconditionViolation`
otherwise (aborting the whole `RunPython` transaction). The only clean no-op
is a genuinely absent subject (no shadow rows), proven symmetric with reverse.

Forward/reverse callables are exercised directly against the real models via a
tiny `apps` + `schema_editor` shim, matching the 0095-0099 migration-test
pattern (GIS/nogis-independent).
"""

import importlib
from datetime import datetime, timezone

import pytest
from django.db import connection

from temples.models import (
    ActionEvent,
    ConciergeThread,
    Favorite,
    Goshuin,
    GoriyakuTag,
    PlaceRef,
    Shrine,
    ShrineDeity,
    ShrineHistory,
    ShrineInteractionLog,
    ShrineKnowledgeSource,
    ShrineReflection,
    Visit,
)

_mod = importlib.import_module("temples.migrations.0100_p8a_duplicate_shrine_shadow_cleanup")
forward = _mod.cleanup_forward
reverse = _mod.cleanup_reverse
PreconditionViolation = _mod.PreconditionViolation

IL101_TS = datetime(2026, 6, 11, 7, 18, 5, 580624, tzinfo=timezone.utc)
IL103_TS = datetime(2026, 6, 11, 8, 0, 22, 85501, tzinfo=timezone.utc)
CORRECTED_49 = (35.6717809, 139.799519)
OLD_49 = (35.6733, 139.7967)

S21 = dict(name_jp="長太稲荷神社", address="日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０",
           latitude=35.660614, longitude=139.6017688)
S22 = dict(name_jp="給田六所神社", address="日本、〒157-0064 東京都世田谷区給田１丁目３−７",
           latitude=35.662443, longitude=139.5920237)
S49 = dict(name_jp="富岡八幡宮", address="東京都江東区富岡1-20-3",
           latitude=CORRECTED_49[0], longitude=CORRECTED_49[1])
S101 = dict(id=101, kind="shrine", **S22, place_ref_id="ChIJl-MEepfxGGAR1Eo44p__GaE")
S103 = dict(id=103, kind="shrine", **S21, place_ref_id="ChIJX19mq8nxGGARsA2kP4gX90M")
S104 = dict(id=104, kind="shrine", name_jp="富岡八幡宮",
           address="日本、〒135-0047 東京都江東区富岡１丁目２０−３",
           latitude=35.6717809, longitude=139.799519,
           place_ref_id="ChIJK11I4BGJGGAR5mZswigcu58")


class _Apps:
    _models = {
        "Shrine": Shrine, "ShrineDeity": ShrineDeity, "ShrineHistory": ShrineHistory,
        "ShrineKnowledgeSource": ShrineKnowledgeSource, "ShrineInteractionLog": ShrineInteractionLog,
        "Favorite": Favorite, "Visit": Visit, "ShrineReflection": ShrineReflection,
        "Goshuin": Goshuin, "ActionEvent": ActionEvent, "ConciergeThread": ConciergeThread,
        "PlaceRef": PlaceRef,
    }

    def get_model(self, app_label, model_name):
        assert app_label == "temples"
        return self._models[model_name]


class _SchemaEditor:
    connection = connection


APPS = _Apps()
SE = _SchemaEditor()


# --------------------------------------------------------------------------- #
# builders
# --------------------------------------------------------------------------- #
def _operator(django_user_model):
    u, _ = django_user_model.objects.get_or_create(
        id=1, defaults=dict(username="p8a-operator", email="op@example.test")
    )
    return u


def _place_refs():
    for pid, name in (
        ("ChIJl-MEepfxGGAR1Eo44p__GaE", "給田六所神社"),
        ("ChIJX19mq8nxGGARsA2kP4gX90M", "長太稲荷神社"),
        ("ChIJK11I4BGJGGAR5mZswigcu58", "富岡八幡宮"),
    ):
        PlaceRef.objects.get_or_create(place_id=pid, defaults=dict(name=name))


def _make_primary(pk, spec, *, goriyaku="", tag_names=()):
    s = Shrine.objects.create(id=pk, kind="shrine", goriyaku=goriyaku, **spec)
    for n in tag_names:
        t, _ = GoriyakuTag.objects.get_or_create(name=n)
        s.goriyaku_tags.add(t)
    return s


def _make_shadow(spec):
    return Shrine.objects.create(**spec)


def _make_il(user, shrine_id, ts):
    return ShrineInteractionLog.objects.create(
        user=user, shrine_id=shrine_id, action_type="detail_view", source="map",
        metadata={"ctx": "map", "event": "shrine_detail_view"}, created_at=ts,
    )


@pytest.fixture
def full_pre(db, django_user_model):
    """The complete audited P8-A PRE state."""
    op = _operator(django_user_model)
    _place_refs()
    p22 = _make_primary(22, S22, goriyaku="地域の氏神として…", tag_names=["家内安全-p"])
    p21 = _make_primary(21, S21, goriyaku="地域に根ざした稲荷社として…", tag_names=["商売繁盛-p", "五穀豊穣-p"])
    p49 = _make_primary(49, S49, goriyaku="勝運・商売繁盛", tag_names=["商売繁盛-p", "勝運-p"])
    # id22 Knowledge (must survive untouched)
    src = ShrineKnowledgeSource.objects.create(
        source_type="secondary_editorial", title="六所神社 - Wikipedia",
        url="https://ja.wikipedia.org/wiki/rokusho",
        verification_status="source_confirmed", confidence="medium",
    )
    d22 = ShrineDeity.objects.create(shrine=p22, display_name="大国魂大神", role="primary",
                                    sort_order=0, verification_status="source_confirmed", confidence="medium")
    d22.sources.set([src])
    h22 = ShrineHistory.objects.create(shrine=p22, history_type="founding", title="分霊勧請",
                                       content="…", sort_order=0,
                                       verification_status="source_confirmed", confidence="medium")
    h22.sources.set([src])
    s101 = _make_shadow(S101)
    s103 = _make_shadow(S103)
    s104 = _make_shadow(S104)
    il1 = _make_il(op, 101, IL101_TS)
    il3 = _make_il(op, 103, IL103_TS)
    return dict(op=op, p21=p21, p22=p22, p49=p49, s101=s101, s103=s103, s104=s104,
                il1=il1, il3=il3, d22=d22, h22=h22, src=src)


def _row(pk):
    return Shrine.objects.filter(pk=pk).first()


def _raw_delete_shrine(pk):
    """Delete a Shrine row without Django's deletion collector (which walks
    model relations whose column may not exist in this env, e.g.
    `temples_conciergehistory.shrine_id`). Same approach the migration uses."""
    with connection.cursor() as cur:
        cur.execute("DELETE FROM temples_shrine WHERE id = %s", [pk])


def _il_shrine(pk):
    return ShrineInteractionLog.objects.get(pk=pk).shrine_id


def _snapshot_49(row):
    return (row.name_jp, row.address, row.latitude, row.longitude, row.place_ref_id)


# --------------------------------------------------------------------------- #
# 1-8 valid forward
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_valid_forward_moves_logs_and_deletes_shadows(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    p49_before = _snapshot_49(_row(49))

    forward(APPS, SE)

    assert _il_shrine(il1_pk) == 22          # 1
    assert _il_shrine(il3_pk) == 21          # 2
    assert _row(101) is None                 # 3
    assert _row(103) is None                 # 4
    assert _row(104) is None                 # 5
    assert _row(21) is not None and _row(22) is not None and _row(49) is not None  # 6
    assert _snapshot_49(_row(49)) == p49_before  # 7 + 8 (no coord / identity write to id49)
    assert (_row(49).latitude, _row(49).longitude) == CORRECTED_49


@pytest.mark.django_db
def test_forward_leaves_primary_semantic_data_untouched(full_pre):
    p22, p21, p49 = full_pre["p22"], full_pre["p21"], full_pre["p49"]
    before = {
        22: (p22.goriyaku, set(p22.goriyaku_tags.values_list("name", flat=True))),
        21: (p21.goriyaku, set(p21.goriyaku_tags.values_list("name", flat=True))),
        49: (p49.goriyaku, set(p49.goriyaku_tags.values_list("name", flat=True))),
    }
    d_ids = set(ShrineDeity.objects.filter(shrine_id=22).values_list("id", flat=True))
    h_ids = set(ShrineHistory.objects.filter(shrine_id=22).values_list("id", flat=True))
    src_ids = set(full_pre["d22"].sources.values_list("id", flat=True))

    forward(APPS, SE)

    for pk in (22, 21, 49):
        r = _row(pk)
        assert (r.goriyaku, set(r.goriyaku_tags.values_list("name", flat=True))) == before[pk]  # 29
    assert set(ShrineDeity.objects.filter(shrine_id=22).values_list("id", flat=True)) == d_ids  # 30
    assert set(ShrineHistory.objects.filter(shrine_id=22).values_list("id", flat=True)) == h_ids
    full_pre["d22"].refresh_from_db()
    assert set(full_pre["d22"].sources.values_list("id", flat=True)) == src_ids
    assert ShrineKnowledgeSource.objects.filter(pk=full_pre["src"].pk).exists()  # 28


@pytest.mark.django_db
def test_forward_does_not_touch_unrelated_shrine_or_id105(full_pre, django_user_model):
    other = Shrine.objects.create(id=90001, kind="shrine", name_jp="無関係神社",
                                  address="どこか", latitude=35.0, longitude=135.0)
    hiroshima = Shrine.objects.create(id=105, kind="shrine", name_jp="広島市",
                                      address="日本、広島県広島市", latitude=34.38, longitude=132.45)
    forward(APPS, SE)
    other.refresh_from_db()
    assert (other.name_jp, other.latitude) == ("無関係神社", 35.0)  # 31
    assert Shrine.objects.filter(pk=105).exists()  # 36 (no id105 mutation)
    hiroshima.refresh_from_db()
    assert hiroshima.name_jp == "広島市"


@pytest.mark.django_db
def test_forward_scoring_evidence_for_primaries_unchanged(full_pre):
    """Recommendation scoring reads only goriyaku_tags GID intersection; P8-A
    changes no primary tag, so the scoring evidence is byte-identical."""
    before = {
        pk: set(_row(pk).goriyaku_tags.values_list("id", flat=True)) for pk in (21, 22, 49)
    }
    forward(APPS, SE)
    after = {
        pk: set(_row(pk).goriyaku_tags.values_list("id", flat=True)) for pk in (21, 22, 49)
    }
    assert after == before  # 32


@pytest.mark.django_db
def test_forward_performs_zero_coordinate_write_to_id49(full_pre):
    before = _row(49).updated_at
    forward(APPS, SE)
    r = _row(49)
    assert (r.latitude, r.longitude) == CORRECTED_49
    assert r.updated_at == before  # id49 row never saved  # 8 / 20


@pytest.mark.django_db
def test_migration_shape(full_pre):
    assert _mod.Migration.dependencies == [("temples", "0099_fix_shrine_49_coordinates")]  # 33
    ops = _mod.Migration.operations
    assert len(ops) == 1 and ops[0].__class__.__name__ == "RunPython"  # 34
    assert _mod.Migration.__dict__.get("atomic", True) is True  # 35 (Django default)


# --------------------------------------------------------------------------- #
# 9-17 forward abort paths -- each raises and leaves everything intact
# --------------------------------------------------------------------------- #
def _assert_untouched(full_pre, il1_pk, il3_pk):
    assert _row(101) is not None and _row(103) is not None and _row(104) is not None
    assert _il_shrine(il1_pk) == 101 and _il_shrine(il3_pk) == 103
    assert (_row(49).latitude, _row(49).longitude) == CORRECTED_49
    assert _row(21) is not None and _row(22) is not None


@pytest.mark.django_db
def test_wrong_shadow_identity_raises(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    Shrine.objects.filter(pk=103).update(name_jp="別名になった神社")
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_untouched(full_pre, il1_pk, il3_pk)  # 9 / 18


@pytest.mark.django_db
def test_missing_primary_raises(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    ShrineDeity.objects.filter(shrine_id=22).delete()
    ShrineHistory.objects.filter(shrine_id=22).delete()
    _row(22).goriyaku_tags.clear()
    _raw_delete_shrine(22)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row(101) is not None and _row(103) is not None and _row(104) is not None
    assert _il_shrine(il1_pk) == 101 and _il_shrine(il3_pk) == 103  # 10


@pytest.mark.django_db
def test_id49_old_coordinate_raises(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    Shrine.objects.filter(pk=49).update(latitude=OLD_49[0], longitude=OLD_49[1])
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row(101) is not None and _row(104) is not None
    assert _il_shrine(il1_pk) == 101 and _il_shrine(il3_pk) == 103  # 11


@pytest.mark.django_db
def test_id49_third_coordinate_raises(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    Shrine.objects.filter(pk=49).update(latitude=35.5, longitude=139.5)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row(101) is not None and _row(104) is not None  # 12


@pytest.mark.django_db
def test_extra_interaction_log_on_shadow_raises(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    _make_il(full_pre["op"], 101, datetime(2026, 6, 11, 9, 0, 0, tzinfo=timezone.utc))
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_untouched(full_pre, il1_pk, il3_pk)  # 13


@pytest.mark.django_db
def test_missing_expected_interaction_log_raises(full_pre):
    il3_pk = full_pre["il3"].pk
    full_pre["il1"].delete()
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row(101) is not None and _row(103) is not None and _row(104) is not None
    assert _il_shrine(il3_pk) == 103  # 14


@pytest.mark.django_db
def test_il_predicate_mismatch_raises(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    ShrineInteractionLog.objects.filter(pk=il1_pk).update(action_type="route_open")
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_untouched(full_pre, il1_pk, il3_pk)


@pytest.mark.django_db
def test_unexpected_user_owned_reference_raises(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    Favorite.objects.create(user=full_pre["op"], shrine_id=104)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_untouched(full_pre, il1_pk, il3_pk)
    assert Favorite.objects.filter(shrine_id=104).exists()  # 15 -- not cascade-deleted


@pytest.mark.django_db
def test_unexpected_visit_reference_raises(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    Visit.objects.create(user=full_pre["op"], shrine_id=101)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_untouched(full_pre, il1_pk, il3_pk)
    assert Visit.objects.filter(shrine_id=101).exists()


@pytest.mark.django_db
def test_nonzero_shadow_counter_raises(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    Shrine.objects.filter(pk=101).update(popular_score=7.0)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_untouched(full_pre, il1_pk, il3_pk)  # 16


@pytest.mark.django_db
def test_unexpected_semantic_relation_on_shadow_raises(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    ShrineHistory.objects.create(shrine_id=104, history_type="founding", title="想定外",
                                 content="…", sort_order=0,
                                 verification_status="draft", confidence="low")
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_untouched(full_pre, il1_pk, il3_pk)  # 17


@pytest.mark.django_db
def test_shadow_goriyaku_tag_on_shadow_raises(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    t, _ = GoriyakuTag.objects.get_or_create(name="想定外タグ")
    _row(103).goriyaku_tags.add(t)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_untouched(full_pre, il1_pk, il3_pk)


@pytest.mark.django_db
def test_partial_shadow_set_raises(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    full_pre["il3"].delete()
    _raw_delete_shrine(103)  # only 101 + 104 remain
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row(101) is not None and _row(104) is not None
    assert _il_shrine(il1_pk) == 101


# --------------------------------------------------------------------------- #
# 19-27 reverse
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_valid_forward_then_reverse_restores(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    p49_before = _snapshot_49(_row(49))

    forward(APPS, SE)
    reverse(APPS, SE)

    for spec in (S101, S103, S104):
        r = _row(spec["id"])
        assert r is not None                                            # 19
        assert (r.name_jp, r.address, r.latitude, r.longitude, r.place_ref_id) == (
            spec["name_jp"], spec["address"], spec["latitude"], spec["longitude"], spec["place_ref_id"]
        )
    assert _il_shrine(il1_pk) == 101 and _il_shrine(il3_pk) == 103       # 20
    assert _snapshot_49(_row(49)) == p49_before                          # 21


@pytest.mark.django_db
def test_forward_reverse_forward_deterministic(full_pre):
    il1_pk, il3_pk = full_pre["il1"].pk, full_pre["il3"].pk
    forward(APPS, SE)
    reverse(APPS, SE)
    forward(APPS, SE)
    assert _row(101) is None and _row(103) is None and _row(104) is None
    assert _il_shrine(il1_pk) == 22 and _il_shrine(il3_pk) == 21         # 27


@pytest.mark.django_db
def test_reverse_conflicting_shadow_pk_raises(full_pre):
    forward(APPS, SE)
    Shrine.objects.create(id=103, kind="shrine", name_jp="別物", address="x",
                          latitude=1.0, longitude=2.0)  # squat pk 103
    with pytest.raises(PreconditionViolation):
        reverse(APPS, SE)
    # no partial restore: 101 / 104 still absent
    assert _row(101) is None and _row(104) is None                      # 22 / 23 / 24


@pytest.mark.django_db
def test_reverse_missing_moved_log_raises(full_pre):
    forward(APPS, SE)
    ShrineInteractionLog.objects.filter(shrine_id=22).delete()  # lose one moved log
    with pytest.raises(PreconditionViolation):
        reverse(APPS, SE)
    assert _row(101) is None and _row(103) is None and _row(104) is None  # 25 -- no partial restore


@pytest.mark.django_db
def test_reverse_unexpected_id49_coordinate_raises(full_pre):
    forward(APPS, SE)
    Shrine.objects.filter(pk=49).update(latitude=OLD_49[0], longitude=OLD_49[1])
    with pytest.raises(PreconditionViolation):
        reverse(APPS, SE)
    assert _row(101) is None and _row(103) is None                      # 26
    assert (_row(49).latitude, _row(49).longitude) == OLD_49            # reverse did NOT rewrite id49


# --------------------------------------------------------------------------- #
# applicability boundary -- proven symmetric
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_absent_subject_forward_and_reverse_are_symmetric_noops(db):
    # fresh DB shape: no shadow rows, no P8-A primaries (Shrine pk 1 from the
    # autouse conftest fixture is unrelated).
    assert not Shrine.objects.filter(pk__in=[21, 22, 49, 101, 103, 104]).exists()

    forward(APPS, SE)  # clean no-op
    assert not Shrine.objects.filter(pk__in=[101, 103, 104]).exists()

    reverse(APPS, SE)  # clean no-op -- must NOT fabricate shadows
    assert not Shrine.objects.filter(pk__in=[101, 103, 104]).exists()


@pytest.mark.django_db
def test_primaries_only_forward_noop_then_reverse_noop(db, django_user_model):
    _place_refs()
    _make_primary(22, S22)
    _make_primary(21, S21)
    _make_primary(49, S49)
    assert not Shrine.objects.filter(pk__in=[101, 103, 104]).exists()

    forward(APPS, SE)  # no shadows -> clean no-op
    assert not Shrine.objects.filter(pk__in=[101, 103, 104]).exists()

    reverse(APPS, SE)  # primaries present but no moved il rows -> clean no-op
    assert not Shrine.objects.filter(pk__in=[101, 103, 104]).exists()
    assert not ShrineInteractionLog.objects.filter(shrine_id__in=[21, 22]).exists()


@pytest.mark.django_db
def test_reverse_on_fresh_db_is_noop(db):
    reverse(APPS, SE)
    assert not Shrine.objects.filter(pk__in=[101, 103, 104]).exists()
