# backend/temples/tests/test_migration_0101_p8b_remove_non_shrine_artifact_id105.py
"""Behavioral tests for temples.0101_p8b_remove_non_shrine_artifact_id105 (P8-B).

`docs/audit/p8-identity-coordinate-remediation.md` §9 / §15 / §19.

`P8_B_DELIVERY = REVERSIBLE_DATA_MIGRATION`, fail-closed: forward runs only
when the exact audited PRE state for `Shrine` pk 105 (the 広島市
locality/political artefact) is present, and raises `PreconditionViolation`
otherwise (aborting the whole `RunPython` transaction). `P8_B_PLACE_REF_POLICY
= DROP_SHRINE_LINK_ONLY` — forward keeps the standalone `place_ref` row;
reverse re-links it.

Forward/reverse callables are exercised directly against the real models via a
tiny `apps` + `schema_editor` shim, matching the 0095-0100 migration-test
pattern (GIS/nogis-independent).
"""

import importlib

import pytest
from django.db import connection

from temples.models import (
    ActionEvent,
    Favorite,
    GoriyakuTag,
    PlaceRef,
    Shrine,
    ShrineDeity,
    ShrineHistory,
    ShrineInteractionLog,
    ShrineKnowledgeSource,
    Visit,
)

_mod = importlib.import_module("temples.migrations.0101_p8b_remove_non_shrine_artifact_id105")
forward = _mod.remove_artifact_forward
reverse = _mod.restore_artifact_reverse
PreconditionViolation = _mod.PreconditionViolation

PID = "ChIJu0_z7giZWjURcvfBz1DO5Ac"
ID = 105
NAME = "広島市"
ADDR = "日本、広島県広島市"
LAT, LNG = 34.3852894, 132.4553055


class _Apps:
    _models = {"Shrine": Shrine, "PlaceRef": PlaceRef}

    def get_model(self, app_label, model_name):
        assert app_label == "temples"
        return self._models[model_name]


class _SchemaEditor:
    connection = connection


APPS = _Apps()
SE = _SchemaEditor()


def _make_place_ref(types=("locality", "political")):
    return PlaceRef.objects.create(
        place_id=PID, name=NAME, address=ADDR, latitude=LAT, longitude=LNG,
        snapshot_json={"name": NAME, "formatted_address": ADDR, "types": list(types)},
    )


def _make_artifact(**over):
    kw = dict(id=ID, kind="shrine", name_jp=NAME, address=ADDR,
              latitude=LAT, longitude=LNG, place_ref_id=PID)
    kw.update(over)
    return Shrine.objects.create(**kw)


def _row(pk=ID):
    return Shrine.objects.filter(pk=pk).first()


def _raw_delete_shrine(pk):
    with connection.cursor() as cur:
        cur.execute("DELETE FROM temples_shrine WHERE id = %s", [pk])


@pytest.fixture
def full_pre(db, django_user_model):
    pr = _make_place_ref()
    art = _make_artifact()
    return dict(pr=pr, art=art, user=django_user_model.objects.create(id=1, username="p8b-op"))


def _snapshot(row):
    return (row.kind, row.name_jp, row.address, row.latitude, row.longitude, row.place_ref_id)


# --------------------------------------------------------------------------- #
# 1-4, 17-18 valid forward / reverse
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_exact_pre_forward_removes_id105_and_keeps_place_ref(full_pre):
    forward(APPS, SE)
    assert _row() is None                                   # 1
    assert PlaceRef.objects.filter(pk=PID).exists()         # 2 -- DROP_SHRINE_LINK_ONLY


@pytest.mark.django_db
def test_forward_then_reverse_restores_exact_snapshot(full_pre):
    before = _snapshot(_row())
    forward(APPS, SE)
    reverse(APPS, SE)
    r = _row()
    assert r is not None                                    # 3
    assert _snapshot(r) == before
    assert r.place_ref_id == PID                            # 4
    assert PlaceRef.objects.filter(pk=PID).count() == 1     # no PlaceRef dup


@pytest.mark.django_db
def test_forward_reverse_forward_deterministic(full_pre):
    forward(APPS, SE)
    reverse(APPS, SE)
    forward(APPS, SE)
    assert _row() is None and PlaceRef.objects.filter(pk=PID).exists()  # 18


@pytest.mark.django_db
def test_migration_shape(full_pre):
    assert _mod.Migration.dependencies == [("temples", "0100_p8a_duplicate_shrine_shadow_cleanup")]
    ops = _mod.Migration.operations
    assert len(ops) == 1 and ops[0].__class__.__name__ == "RunPython"


@pytest.mark.django_db
def test_recommendation_scoring_untouched(full_pre):
    other = Shrine.objects.create(id=90001, kind="shrine", name_jp="無関係神社",
                                  address="どこか", latitude=35.0, longitude=135.0)
    t, _ = GoriyakuTag.objects.get_or_create(name="勝運-x")
    other.goriyaku_tags.add(t)
    before = set(other.goriyaku_tags.values_list("id", flat=True))
    forward(APPS, SE)
    other.refresh_from_db()
    assert set(other.goriyaku_tags.values_list("id", flat=True)) == before  # impact = NONE
    assert other.name_jp == "無関係神社"


# --------------------------------------------------------------------------- #
# 5-12 forward abort paths -- each raises and leaves everything unchanged (16)
# --------------------------------------------------------------------------- #
def _assert_intact():
    r = _row()
    assert r is not None
    assert _snapshot(r) == ("shrine", NAME, ADDR, LAT, LNG, PID) or r.kind != "shrine" or r.name_jp != NAME or r.address != ADDR
    assert PlaceRef.objects.filter(pk=PID).exists()


@pytest.mark.django_db
def test_unexpected_name_forward_raises(full_pre):
    Shrine.objects.filter(pk=ID).update(name_jp="広島東照宮")
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None and _row().name_jp == "広島東照宮"   # 5 / 16


@pytest.mark.django_db
def test_unexpected_address_forward_raises(full_pre):
    Shrine.objects.filter(pk=ID).update(address="広島県広島市中区基町21-2")
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None and _row().address == "広島県広島市中区基町21-2"  # 6


@pytest.mark.django_db
def test_unexpected_kind_forward_raises(full_pre):
    Shrine.objects.filter(pk=ID).update(kind="temple")
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None and _row().kind == "temple"          # 7


@pytest.mark.django_db
def test_wrong_place_ref_forward_raises(full_pre):
    other_pr = PlaceRef.objects.create(place_id="ChIJ_place_of_worship", name="別",
                                       snapshot_json={"types": ["place_of_worship"]})
    Shrine.objects.filter(pk=ID).update(place_ref_id=other_pr.place_id)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None                                       # 8


@pytest.mark.django_db
def test_place_ref_is_place_of_worship_forward_raises(full_pre):
    """A future legitimate shrine re-using pk 105 with a place_of_worship
    place_ref must NOT be deleted."""
    PlaceRef.objects.filter(pk=PID).update(
        snapshot_json={"types": ["establishment", "place_of_worship", "point_of_interest"]}
    )
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None


# --------------------------------------------------------------------------- #
# F1 — strict, unconditional PlaceRef type validation
# --------------------------------------------------------------------------- #
def _pre_snapshot():
    r = _row()
    pr = PlaceRef.objects.get(pk=PID)
    return (r.kind, r.name_jp, r.address, r.latitude, r.longitude, r.place_ref_id,
            r.popular_score, r.owner_id, pr.snapshot_json)


def _assert_p8b_intact(before):
    assert _row() is not None
    r = _row()
    pr = PlaceRef.objects.get(pk=PID)
    assert (r.kind, r.name_jp, r.address, r.latitude, r.longitude, r.place_ref_id,
            r.popular_score, r.owner_id, pr.snapshot_json) == before


@pytest.mark.django_db
def test_place_ref_types_empty_list_forward_raises(full_pre):
    PlaceRef.objects.filter(pk=PID).update(snapshot_json={"name": NAME, "types": []})
    before = _pre_snapshot()
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_p8b_intact(before)  # F1 #1


@pytest.mark.django_db
def test_place_ref_types_absent_forward_raises(full_pre):
    PlaceRef.objects.filter(pk=PID).update(snapshot_json={"name": NAME, "formatted_address": ADDR})
    before = _pre_snapshot()
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_p8b_intact(before)  # F1 #2


@pytest.mark.django_db
def test_place_ref_types_not_a_list_forward_raises(full_pre):
    PlaceRef.objects.filter(pk=PID).update(snapshot_json={"types": "locality"})
    before = _pre_snapshot()
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_p8b_intact(before)  # F1 #3


@pytest.mark.django_db
def test_place_ref_snapshot_not_a_dict_forward_raises(full_pre):
    PlaceRef.objects.filter(pk=PID).update(snapshot_json=["locality", "political"])
    before = _pre_snapshot()
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_p8b_intact(before)


@pytest.mark.django_db
def test_place_ref_types_political_only_forward_raises(full_pre):
    PlaceRef.objects.filter(pk=PID).update(snapshot_json={"types": ["political"]})
    before = _pre_snapshot()
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_p8b_intact(before)  # F1 #4


@pytest.mark.django_db
def test_place_ref_types_locality_political_forward_succeeds(full_pre):
    # exact audited shape (locality present, place_of_worship absent)
    assert PlaceRef.objects.get(pk=PID).snapshot_json["types"] == ["locality", "political"]
    forward(APPS, SE)
    assert _row() is None                                             # F1 #5
    assert PlaceRef.objects.filter(pk=PID).exists()


@pytest.mark.django_db
def test_place_ref_types_with_place_of_worship_forward_raises(full_pre):
    PlaceRef.objects.filter(pk=PID).update(
        snapshot_json={"types": ["locality", "political", "place_of_worship"]}
    )
    before = _pre_snapshot()
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    _assert_p8b_intact(before)  # F1 #6


# --------------------------------------------------------------------------- #
# F1 optional — exact forward coordinate PRE (reverse restores static values)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_wrong_latitude_forward_raises(full_pre):
    Shrine.objects.filter(pk=ID).update(latitude=34.4)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None and _row().latitude == 34.4


@pytest.mark.django_db
def test_wrong_longitude_forward_raises(full_pre):
    Shrine.objects.filter(pk=ID).update(longitude=132.5)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None and _row().longitude == 132.5


@pytest.mark.django_db
def test_unexpected_goriyaku_tag_forward_raises(full_pre):
    t, _ = GoriyakuTag.objects.get_or_create(name="想定外タグ")
    _row().goriyaku_tags.add(t)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None                                       # 9


@pytest.mark.django_db
def test_unexpected_knowledge_relation_forward_raises(full_pre):
    ShrineDeity.objects.create(shrine_id=ID, display_name="想定外神", role="primary",
                               sort_order=0, verification_status="draft", confidence="low")
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None and ShrineDeity.objects.filter(shrine_id=ID).exists()  # 10


@pytest.mark.django_db
def test_unexpected_history_relation_forward_raises(full_pre):
    ShrineHistory.objects.create(shrine_id=ID, history_type="founding", title="想定外",
                                 content="…", sort_order=0,
                                 verification_status="draft", confidence="low")
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None


@pytest.mark.django_db
def test_unexpected_favorite_forward_raises(full_pre):
    Favorite.objects.create(user=full_pre["user"], shrine_id=ID)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None and Favorite.objects.filter(shrine_id=ID).exists()  # 11


@pytest.mark.django_db
def test_unexpected_visit_forward_raises(full_pre):
    Visit.objects.create(user=full_pre["user"], shrine_id=ID)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None and Visit.objects.filter(shrine_id=ID).exists()


@pytest.mark.django_db
def test_unexpected_interaction_and_action_event_forward_raises(full_pre):
    il = ShrineInteractionLog.objects.create(user=full_pre["user"], shrine_id=ID,
                                             action_type="detail_view", metadata={})
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None and ShrineInteractionLog.objects.filter(pk=il.pk).exists()  # 12
    il.delete()
    ae = ActionEvent.objects.create(user=full_pre["user"], shrine_id=ID, action_type="route_open")
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None and ActionEvent.objects.filter(pk=ae.pk).exists()


@pytest.mark.django_db
def test_nonzero_counter_forward_raises(full_pre):
    Shrine.objects.filter(pk=ID).update(popular_score=3.0)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None and _row().popular_score == 3.0


@pytest.mark.django_db
def test_owner_set_forward_raises(full_pre):
    Shrine.objects.filter(pk=ID).update(owner_id=full_pre["user"].id)
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert _row() is not None


# --------------------------------------------------------------------------- #
# 13-15 reverse abort paths
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_reverse_pk105_occupied_raises(full_pre):
    forward(APPS, SE)
    Shrine.objects.create(id=ID, kind="shrine", name_jp="別物", address="x",
                          latitude=1.0, longitude=2.0)
    with pytest.raises(PreconditionViolation):
        reverse(APPS, SE)                                           # 13
    assert _row().name_jp == "別物"  # not overwritten


@pytest.mark.django_db
def test_reverse_after_forward_then_place_ref_deleted_is_noop(full_pre):
    """Task item #14 ("reverse with expected PlaceRef missing"): after a real
    forward (Shrine deleted, PlaceRef kept), if the PlaceRef is *also* deleted
    out-of-band, the observable state ("Shrine 105 absent AND its PlaceRef
    absent") is byte-identical to a fresh-lineage forward no-op. Reverse is a
    **clean no-op** — it never fabricates the artefact or a replacement
    PlaceRef, and the artefact staying removed is the intended end state.
    (Deliberate symmetric-contract choice over a bare RAISE — see PR body.)"""
    forward(APPS, SE)
    PlaceRef.objects.filter(pk=PID).delete()
    reverse(APPS, SE)
    assert _row() is None                                           # no fabrication
    assert not PlaceRef.objects.filter(pk=PID).exists()             # no replacement PlaceRef


@pytest.mark.django_db
def test_reverse_place_ref_claimed_raises(full_pre):
    forward(APPS, SE)
    Shrine.objects.create(id=90002, kind="shrine", name_jp="別神社", address="y",
                          latitude=1.0, longitude=2.0, place_ref_id=PID)
    with pytest.raises(PreconditionViolation):
        reverse(APPS, SE)                                           # 15
    assert _row() is None


# --------------------------------------------------------------------------- #
# applicability boundary -- narrowest observable, symmetric
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_fresh_lineage_forward_and_reverse_are_symmetric_noops(db):
    # neither the artefact nor its distinctive place_ref exists
    assert _row() is None and not PlaceRef.objects.filter(pk=PID).exists()
    forward(APPS, SE)   # clean no-op
    assert _row() is None and not PlaceRef.objects.filter(pk=PID).exists()
    reverse(APPS, SE)   # clean no-op -- must NOT fabricate the artefact
    assert _row() is None and not PlaceRef.objects.filter(pk=PID).exists()


@pytest.mark.django_db
def test_forward_shrine_absent_but_place_ref_present_raises(db):
    _make_place_ref()  # place_ref present, shrine 105 absent -> ambiguous
    assert _row() is None
    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)
    assert PlaceRef.objects.filter(pk=PID).exists()  # unchanged


@pytest.mark.django_db
def test_reverse_fresh_lineage_is_noop(db):
    assert _row() is None and not PlaceRef.objects.filter(pk=PID).exists()
    reverse(APPS, SE)
    assert _row() is None
