"""Compass Monthly Direction-only Core の Product Contract test.

正本:
    docs/product/compass-direction-only-candidate-universe-decision.md
    docs/product/compass-direction-only-ranking-weekly-theme-decision.md
    docs/knowledge/recommendation-eligibility-contract.md

この file は新しい Direction-only Core（compass_direction_only_core）だけを対象にする。
旧 Monthly API（get_compass_recommendations(purpose=...)）の挙動は既存 test が守る。
"""

from __future__ import annotations

import ast
import inspect
import math
import random
from pathlib import Path

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from temples.models import GoriyakuTag, Shrine, ShrineDeity
from temples.services import compass_direction_only_core as core
from temples.services import compass_recommendation_orchestrator as legacy_orchestrator
from temples.services import concierge_chat_candidates as shared_candidates
from temples.services.compass_direction_only_core import (
    MAX_CANDIDATE_RADIUS_M,
    STATE_DIRECTION_FILTER_UNAVAILABLE,
    STATE_DIRECTION_ZERO_CANDIDATES,
    STATE_NO_COMMON_DIRECTION,
    STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES,
    STATE_RECOMMENDATION_SUCCESS,
    get_compass_direction_only_candidates,
    load_structural_universe_within_60km,
    lossless_bounding_box,
    rank_active_set,
)
from temples.services.compass_runtime import NoCommonDirectionResult
from temples.services.concierge_chat_candidates import (
    _distance_m,
    build_chat_candidates_with_eligibility,
)
from temples.tests.support.recommendation_eligibility import (
    attach_usable_deity_fact,
    attach_usable_history_fact,
    create_fact_ready_source,
)

pytestmark = pytest.mark.django_db

ORIGIN = {"lat": 35.0, "lng": 135.0}
NORTH = {"referenceDirections": ["北"], "calculationMethod": "annual_monthly_kyusei_v1"}
EARTH_RADIUS_M = 6371000.0


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _destination(lat: float, lng: float, *, bearing_deg: float, distance_m: float):
    """球面上で (lat, lng) から bearing / distance 進んだ点（test data 生成専用）。"""
    delta = distance_m / EARTH_RADIUS_M
    theta = math.radians(bearing_deg)
    phi1 = math.radians(lat)
    lam1 = math.radians(lng)
    phi2 = math.asin(
        math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(theta)
    )
    lam2 = lam1 + math.atan2(
        math.sin(theta) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * math.sin(phi2),
    )
    return math.degrees(phi2), (math.degrees(lam2) + 540.0) % 360.0 - 180.0


def _shrine(
    name: str,
    *,
    km: float = 5.0,
    bearing: float = 0.0,
    popular_score: float = 0.0,
    address: str = "京都府京都市1-1",
    goriyaku: str = "",
) -> Shrine:
    lat, lng = _destination(ORIGIN["lat"], ORIGIN["lng"], bearing_deg=bearing, distance_m=km * 1000)
    return Shrine.objects.create(
        name_jp=name,
        address=address,
        latitude=lat,
        longitude=lng,
        popular_score=popular_score,
        goriyaku=goriyaku,
    )


def _eligible(name: str, **kwargs) -> Shrine:
    shrine = _shrine(name, **kwargs)
    attach_usable_deity_fact(shrine, display_name=f"{name}の祭神")
    return shrine


def _run(origin=ORIGIN, direction_context=NORTH):
    return get_compass_direction_only_candidates(origin=origin, direction_context=direction_context)


def _ids(result) -> list[int]:
    return [c["shrine_id"] for c in result.candidates]


def _names(result) -> list[str]:
    return [c["name"] for c in result.candidates]


# --------------------------------------------------------------------------
# A. Structural membership
# --------------------------------------------------------------------------


def test_structural_base_excludes_qa_fixtures_and_missing_structure():
    kept = _eligible("構造条件を満たす神社", km=3)
    qa = _eligible("テスト神社", km=3)
    qa_prefix = _eligible("テスト候補の社", km=3)
    no_coordinates = _eligible("座標なし神社", km=3)
    no_address = _eligible("住所なし構造神社", km=3)
    # DB の check constraint（chk_lat_lng_both_or_none）により、緯度だけ / 経度だけが
    # null の row は存在できない。表現可能な「両方 null」を作る。conftest の pre_save が
    # 座標を補完するため、signal を通らない update で null にする。
    Shrine.objects.filter(pk=no_coordinates.pk).update(latitude=None, longitude=None)
    Shrine.objects.filter(pk=no_address.pk).update(address="")

    result = _run()

    assert result.state == STATE_RECOMMENDATION_SUCCESS
    assert _ids(result) == [kept.id]
    assert result.source_candidate_count == 1
    for excluded in (qa, qa_prefix, no_coordinates, no_address):
        assert excluded.id not in _ids(result)


def test_structural_base_requires_latitude_and_longitude_independently():
    # 片方だけ null の row は DB constraint で作れないため、候補 SQL が
    # latitude / longitude それぞれに NOT NULL 条件を持つことを SQL で確認する。
    with CaptureQueriesContext(connection) as ctx:
        load_structural_universe_within_60km(origin_lat=ORIGIN["lat"], origin_lng=ORIGIN["lng"])

    (sql,) = [q["sql"] for q in ctx.captured_queries if '"temples_shrine"' in q["sql"]]
    where = sql.split(" WHERE ", 1)[1]
    assert '"temples_shrine"."latitude" IS NOT NULL' in where
    assert '"temples_shrine"."longitude" IS NOT NULL' in where
    assert '"temples_shrine"."address" = \'\'' in where


def _code_string_constants(module) -> set[str]:
    """docstring を除いた、code 上の文字列定数。"""
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                docstrings.add(id(body[0].value))
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    }


def test_structural_base_reuses_the_existing_qa_exclusion_authority():
    source = Path(core.__file__).read_text(encoding="utf-8")
    assert "exclude_qa_fixture_shrines" in source
    # QA 除外条件（名前の規約）を Compass 側に書き直していない
    constants = "\n".join(_code_string_constants(core))
    for literal in ("テスト", "承認テスト", "検証", "noaddr", "test"):
        assert literal not in constants


# --------------------------------------------------------------------------
# B. 60km universe
# --------------------------------------------------------------------------


def test_shrine_just_inside_60km_survives_and_just_outside_is_excluded():
    inside = _eligible("59.99km北の神社", km=59.99)
    outside = _eligible("60.01km北の神社", km=60.01)
    assert _distance_m(ORIGIN["lat"], ORIGIN["lng"], inside.latitude, inside.longitude) <= 60000
    assert _distance_m(ORIGIN["lat"], ORIGIN["lng"], outside.latitude, outside.longitude) > 60000

    result = _run()

    assert result.state == STATE_RECOMMENDATION_SUCCESS
    assert _ids(result) == [inside.id]
    assert result.distance_stage_km == 60


def test_bounding_box_candidate_outside_exact_60km_is_removed_by_exact_distance():
    # 北東の四隅付近: 緯度・経度とも box 内だが、実距離は 60km を超える
    corner_lat, corner_lng = ORIGIN["lat"] + 0.5, ORIGIN["lng"] + 0.45
    corner = Shrine.objects.create(
        name_jp="box隅の神社", address="京都府1-1", latitude=corner_lat, longitude=corner_lng
    )
    box = lossless_bounding_box(
        lat=ORIGIN["lat"], lng=ORIGIN["lng"], radius_m=MAX_CANDIDATE_RADIUS_M
    )
    assert box.min_lat <= corner_lat <= box.max_lat
    assert box.min_lng <= corner_lng <= box.max_lng
    assert _distance_m(ORIGIN["lat"], ORIGIN["lng"], corner_lat, corner_lng) > 60000

    universe = load_structural_universe_within_60km(
        origin_lat=ORIGIN["lat"], origin_lng=ORIGIN["lng"]
    )

    assert corner.id not in [shrine.id for shrine, _ in universe]


def test_no_fallback_beyond_60km():
    beyond = _eligible("61km北の神社", km=61)

    result = _run()

    # U60 が空なら「方位内に候補0」と同じ direction_zero_candidates（新しい state は作らない）
    assert result.state == STATE_DIRECTION_ZERO_CANDIDATES
    assert result.candidates == []
    assert result.source_candidate_count == 0
    assert beyond.id not in _ids(result)


def test_bounding_box_is_lossless_for_every_point_within_60km():
    rng = random.Random(20260927)
    origins = [(35.0, 135.0), (43.06, 141.35), (26.21, 127.68), (0.0, 0.0), (-33.9, 151.2)]
    origins += [(rng.uniform(-80, 80), rng.uniform(-179, 179)) for _ in range(40)]
    # 極付近・日付変更線付近（経度を絞らない分岐）
    origins += [(89.7, 10.0), (-89.8, -40.0), (10.0, 179.9), (-5.0, -179.95)]

    checked = 0
    for lat, lng in origins:
        box = lossless_bounding_box(lat=lat, lng=lng, radius_m=60000)
        for _ in range(300):
            distance = rng.choice([rng.uniform(0, 60000), rng.uniform(59990, 60000.999)])
            p_lat, p_lng = _destination(
                lat, lng, bearing_deg=rng.uniform(0, 360), distance_m=distance
            )
            if _distance_m(lat, lng, p_lat, p_lng) > 60000:
                continue
            checked += 1
            assert box.min_lat <= p_lat <= box.max_lat, (lat, lng, p_lat, p_lng)
            if box.min_lng is not None:
                assert box.min_lng <= p_lng <= box.max_lng, (lat, lng, p_lat, p_lng)
    assert checked > 10000


# --------------------------------------------------------------------------
# C. No popularity / count loss (>300 shrines)
# --------------------------------------------------------------------------


def test_low_popularity_shrine_is_not_lost_to_the_old_popular_top_n_pool():
    # 60km 圏内（南20km）に、人気の高い Shrine を旧 pool 上限（300）を超えて並べる。
    # 方位は合わず Knowledge も無いので Direction-only Core の結果には入らないが、
    # 旧設計の「ORDER BY -popular_score LIMIT 300」はこれらで埋まる。
    popular = []
    for index in range(310):
        lat, lng = _destination(
            ORIGIN["lat"], ORIGIN["lng"], bearing_deg=180.0, distance_m=20000 + index * 10
        )
        popular.append(
            Shrine(
                name_jp=f"人気の神社{index}",
                address="京都府1-1",
                latitude=lat,
                longitude=lng,
                popular_score=1000.0,
            )
        )
    Shrine.objects.bulk_create(popular)
    target = _eligible("北10kmの静かな神社", km=10, popular_score=0.0)

    # 旧設計（共有 builder に Compass の pool 設定を渡したもの）では target が pool に入らない
    legacy_pool = build_chat_candidates_with_eligibility(
        lat=ORIGIN["lat"],
        lng=ORIGIN["lng"],
        limit=legacy_orchestrator.DEFAULT_CANDIDATE_POOL_LIMIT,
    )
    assert legacy_pool.source_count == 300
    assert target.id not in [c["shrine_id"] for c in legacy_pool.candidates]

    # Direction-only Core は件数上限なしで U60 を作り、target を残す
    result = _run()

    assert result.state == STATE_RECOMMENDATION_SUCCESS
    assert _ids(result) == [target.id]
    assert result.source_candidate_count == 311
    assert result.eligible_candidate_count == 1


def test_candidate_source_query_has_no_popularity_order_or_limit():
    _eligible("北5kmの神社", km=5)

    with CaptureQueriesContext(connection) as ctx:
        load_structural_universe_within_60km(origin_lat=ORIGIN["lat"], origin_lng=ORIGIN["lng"])

    shrine_queries = [q["sql"] for q in ctx.captured_queries if '"temples_shrine"' in q["sql"]]
    assert len(shrine_queries) == 1
    # SELECT 句は全 column を読むので、membership / 順序を決める部分だけを検査する
    after_from = shrine_queries[0].upper().split(" FROM ", 1)[1]
    assert "POPULAR_SCORE" not in after_from
    assert " LIMIT " not in after_from
    assert " OFFSET " not in after_from
    order_by = after_from.split(" ORDER BY ", 1)[1]
    assert order_by.strip() == '"TEMPLES_SHRINE"."ID" ASC'


# --------------------------------------------------------------------------
# D. Shared Eligibility
# --------------------------------------------------------------------------


def test_usable_deity_only_or_history_only_is_eligible_and_neither_is_excluded():
    deity_only = _shrine("祭神のみ", km=4)
    attach_usable_deity_fact(deity_only)
    history_only = _shrine("由緒のみ", km=5)
    attach_usable_history_fact(history_only)
    neither = _shrine("Factなし", km=6)
    # fact-ready でない Fact は usable ではない
    unverified = _shrine("未確認Factのみ", km=7)
    deity = ShrineDeity.objects.create(
        shrine=unverified, display_name="未検証", sort_order=0, verification_status="unverified"
    )
    deity.sources.add(create_fact_ready_source())

    result = _run()

    assert result.state == STATE_RECOMMENDATION_SUCCESS
    assert set(_ids(result)) == {deity_only.id, history_only.id}
    assert neither.id not in _ids(result)
    assert unverified.id not in _ids(result)
    assert result.source_candidate_count == 4
    assert result.eligible_candidate_count == 2


def test_eligibility_zero_is_a_distinct_valid_result():
    _shrine("Factのない北の神社", km=5)

    result = _run()

    assert result.state == STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES
    assert result.candidates == []
    assert result.source_candidate_count == 1
    assert result.eligible_candidate_count == 0


def test_eligibility_is_delegated_to_the_shared_rule(monkeypatch):
    _eligible("北5kmの神社", km=5)
    calls = []

    def _deny_all(*, knowledge_deities, knowledge_histories):
        calls.append((knowledge_deities, knowledge_histories))
        return False

    # 共有層の唯一の判定式を差し替えると、Core の結果もそれに従う（Core は判定しない）
    monkeypatch.setattr(shared_candidates, "is_recommendation_eligible", _deny_all)

    result = _run()

    assert calls
    assert result.state == STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES


def test_core_module_contains_no_eligibility_logic():
    tree = ast.parse(Path(core.__file__).read_text(encoding="utf-8"))
    identifiers = (
        {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        | {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
    )
    for marker in (
        "is_recommendation_eligible",
        "decide_fact_usability",
        "fetch_fact_ready_knowledge_deities",
        "fetch_fact_ready_knowledge_histories",
        "FACT_READY_VERIFICATION_STATUSES",
        "verification_status",
    ):
        assert (
            marker not in identifiers
        ), f"Direction-only Core must not re-implement eligibility: {marker}"


# --------------------------------------------------------------------------
# E. Direction
# --------------------------------------------------------------------------


def test_matching_sector_survives_and_other_sectors_are_excluded():
    north = _eligible("北の神社", km=8, bearing=0)
    east = _eligible("東の神社", km=8, bearing=90)
    south = _eligible("南の神社", km=8, bearing=180)

    result = _run()

    assert _ids(result) == [north.id]
    assert east.id not in _ids(result)
    assert south.id not in _ids(result)
    assert result.eligible_candidate_count == 3
    assert result.direction_candidate_count == 1


def test_direction_filter_authority_is_reused(monkeypatch):
    _eligible("北の神社", km=8)
    calls = []
    original = core.filter_candidates_by_direction

    def _spy(candidates, *, origin, reference_directions):
        calls.append(list(reference_directions or []))
        return original(candidates, origin=origin, reference_directions=reference_directions)

    monkeypatch.setattr(core, "filter_candidates_by_direction", _spy)

    result = _run()

    assert result.state == STATE_RECOMMENDATION_SUCCESS
    assert calls and all(c == ["北"] for c in calls)
    # 方位計算・8方位ラベルを Core 側に複製していない
    source = Path(core.__file__).read_text(encoding="utf-8")
    for marker in ("_bearing", "_direction_label", "_DIRECTION_LABELS", "atan2"):
        assert marker not in source


def test_direction_only_zero_is_a_valid_empty_result():
    _eligible("南の神社", km=8, bearing=180)

    result = _run()

    assert result.state == STATE_DIRECTION_ZERO_CANDIDATES
    assert result.candidates == []
    assert result.eligible_candidate_count == 1
    assert result.direction_candidate_count == 0
    assert result.distance_candidate_count == 0
    assert result.distance_stage_km is None


@pytest.mark.parametrize(
    "origin",
    [
        None,
        {},
        {"lat": 35.0},
        {"lat": "abc", "lng": 135.0},
        {"lat": float("nan"), "lng": 135.0},
        {"lat": 35.0, "lng": float("inf")},
        {"lat": 91.0, "lng": 135.0},
        {"lat": 35.0, "lng": 181.0},
        "35,135",
    ],
)
def test_invalid_origin_is_unavailable_without_touching_the_database(
    origin, django_assert_num_queries
):
    _eligible("北の神社", km=8)

    with django_assert_num_queries(0):
        result = _run(origin=origin)

    assert result.state == STATE_DIRECTION_FILTER_UNAVAILABLE
    assert result.candidates == []
    assert result.source_candidate_count is None


@pytest.mark.parametrize(
    "direction_context",
    [
        None,
        {},
        {"referenceDirections": []},
        {"referenceDirections": ["north"]},
        {"referenceDirections": None},
        "北",
    ],
)
def test_invalid_direction_context_is_unavailable(direction_context, django_assert_num_queries):
    _eligible("北の神社", km=8)

    with django_assert_num_queries(0):
        result = _run(direction_context=direction_context)

    assert result.state == STATE_DIRECTION_FILTER_UNAVAILABLE
    assert result.candidates == []


def test_no_common_direction_keeps_its_own_state(django_assert_num_queries):
    _eligible("北の神社", km=8)

    with django_assert_num_queries(0):
        result = _run(direction_context=NoCommonDirectionResult())

    assert result.state == STATE_NO_COMMON_DIRECTION
    assert result.candidates == []
    assert result.direction_context is None


def test_unavailable_takes_precedence_over_eligibility_zero():
    # Eligibility を満たす Shrine が無くても、入力が不正なら unavailable（Group A が先）
    _shrine("Factのない北の神社", km=5)

    result = _run(direction_context={"referenceDirections": ["invalid"]})

    assert result.state == STATE_DIRECTION_FILTER_UNAVAILABLE


# --------------------------------------------------------------------------
# F. Distance stage
# --------------------------------------------------------------------------


def test_five_within_15km_uses_stage_15():
    near = [_eligible(f"北{km}km", km=km) for km in (2, 4, 6, 8, 10)]
    _eligible("北20km", km=20)

    result = _run()

    assert result.distance_stage_km == 15
    assert _ids(result) == [s.id for s in near]
    assert result.direction_candidate_count == 6
    assert result.distance_candidate_count == 5


def test_fewer_than_five_within_15km_but_five_within_30km_uses_stage_30():
    kms = (3, 6, 9, 12, 25)
    shrines = [_eligible(f"北{km}km", km=km) for km in kms]
    _eligible("北45km", km=45)

    result = _run()

    assert result.distance_stage_km == 30
    assert _ids(result) == [s.id for s in shrines]


def test_fewer_than_five_within_30km_uses_stage_60():
    shrines = [_eligible(f"北{km}km", km=km) for km in (5, 20, 28, 50)]

    result = _run()

    assert result.distance_stage_km == 60
    assert _ids(result) == [s.id for s in shrines]


@pytest.mark.parametrize("count", [1, 2, 3, 4])
def test_one_to_four_candidates_at_60km_is_a_valid_success(count):
    shrines = [_eligible(f"北{40 + i}km", km=40 + i) for i in range(count)]

    result = _run()

    assert result.state == STATE_RECOMMENDATION_SUCCESS
    assert result.distance_stage_km == 60
    assert _ids(result) == [s.id for s in shrines]


def test_zero_within_60km_is_empty_without_backfill():
    _eligible("北70km", km=70)
    _eligible("南10km", km=10, bearing=180)

    result = _run()

    assert result.state == STATE_DIRECTION_ZERO_CANDIDATES
    assert result.candidates == []


def test_distance_stage_is_the_shared_compass_authority():
    from temples.services import compass_distance_stage

    assert (
        legacy_orchestrator._apply_compass_distance_stage
        is compass_distance_stage.apply_compass_distance_stage
    )
    assert core.apply_compass_distance_stage is compass_distance_stage.apply_compass_distance_stage
    assert core.MAX_CANDIDATE_RADIUS_M == compass_distance_stage.DISTANCE_STAGE_3_KM * 1000
    assert (
        compass_distance_stage.DISTANCE_STAGE_1_KM,
        compass_distance_stage.DISTANCE_STAGE_2_KM,
        compass_distance_stage.DISTANCE_STAGE_3_KM,
        compass_distance_stage.DISTANCE_STAGE_EXPANSION_THRESHOLD,
    ) == (15, 30, 60, 5)


# --------------------------------------------------------------------------
# G. Ranking
# --------------------------------------------------------------------------


def test_ranking_is_distance_ascending():
    far = _eligible("北12km", km=12, popular_score=900)
    near = _eligible("北3km", km=3, popular_score=1)
    mid = _eligible("北7km", km=7, popular_score=50)

    result = _run()

    assert _ids(result) == [near.id, mid.id, far.id]
    distances = [c["distance_m"] for c in result.candidates]
    assert distances == sorted(distances)


def test_exact_distance_ties_break_by_shrine_id():
    first = _eligible("同距離A", km=6)
    second = _eligible("同距離B", km=6)
    Shrine.objects.filter(pk=first.pk).update(popular_score=0.0)
    Shrine.objects.filter(pk=second.pk).update(popular_score=999.0)
    first.refresh_from_db()
    Shrine.objects.filter(pk=second.pk).update(latitude=first.latitude, longitude=first.longitude)

    result = _run()

    assert [c["distance_m"] for c in result.candidates][0] == [
        c["distance_m"] for c in result.candidates
    ][1]
    assert _ids(result) == sorted([first.id, second.id])


def test_rank_active_set_uses_only_distance_then_shrine_id():
    candidates = [
        {"shrine_id": 9, "distance_m": 500, "popular_score": 0},
        {"shrine_id": 3, "distance_m": 700, "popular_score": 999},
        {"shrine_id": 4, "distance_m": 500, "popular_score": 999},
    ]

    assert [c["shrine_id"] for c in rank_active_set(candidates)] == [4, 9, 3]


def test_ranking_ignores_popularity_knowledge_amount_and_goriyaku():
    shrines = [_eligible(f"北{km}km", km=km) for km in (3, 5, 8, 11)]
    baseline = _ids(_run())

    # popular_score を逆転させる
    for index, shrine in enumerate(shrines):
        Shrine.objects.filter(pk=shrine.pk).update(popular_score=1000.0 - index * 300)
    assert _ids(_run()) == baseline

    # 遠い Shrine ほど Knowledge Fact を多くする
    for index, shrine in enumerate(shrines):
        for extra in range(index * 2):
            attach_usable_deity_fact(shrine, display_name=f"追加祭神{extra}")
            attach_usable_history_fact(shrine, title=f"追加由緒{extra}")
    assert _ids(_run()) == baseline

    # goriyaku（text と tag）を与える
    tag = GoriyakuTag.objects.create(name="仕事運", category="ご利益")
    for shrine in shrines[2:]:
        Shrine.objects.filter(pk=shrine.pk).update(goriyaku="仕事運 商売繁盛 縁結び")
        shrine.goriyaku_tags.add(tag)
    assert _ids(_run()) == baseline


# --------------------------------------------------------------------------
# H. Purpose independence
# --------------------------------------------------------------------------


def test_core_entrypoint_accepts_no_purpose():
    params = inspect.signature(get_compass_direction_only_candidates).parameters
    assert list(params) == ["origin", "direction_context"]
    with pytest.raises(TypeError):
        get_compass_direction_only_candidates(  # type: ignore[call-arg]
            origin=ORIGIN, direction_context=NORTH, purpose="career"
        )


def test_core_module_has_no_semantic_routing():
    """docstring / comment の説明文ではなく、code 上の識別子と文字列を検査する。"""
    tree = ast.parse(Path(core.__file__).read_text(encoding="utf-8"))
    docstring_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                docstring_nodes.add(id(body[0].value))

    tokens: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            tokens.add(node.id)
        elif isinstance(node, ast.Attribute):
            tokens.add(node.attr)
        elif isinstance(node, ast.arg):
            tokens.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg:
            tokens.add(node.arg)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            tokens.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                tokens.add(node.module)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in docstring_nodes:
                tokens.add(node.value)

    joined = "\n".join(tokens).lower()
    for forbidden in (
        "purpose",
        "need_tag",
        "need_tags",
        "need_tags",
        "interpret_consultation",
        "consultation_interpreter",
        "interpretation_profile",
        "goriyaku",
        "selected_goriyaku_tag_ids",
        "popular_score",
        "build_chat_recommendations",
        "build_chat_candidates",
        "score",
        "reason",
    ):
        assert forbidden not in joined, f"Direction-only Core must not reference: {forbidden}"


def test_candidate_payload_is_factual_and_carries_shrine_id():
    shrine = _eligible("北の神社", km=8)
    attach_usable_history_fact(shrine)

    (candidate,) = _run().candidates

    assert candidate["shrine_id"] == shrine.id
    assert set(candidate) == {
        "shrine_id",
        "id",
        "name",
        "address",
        "latitude",
        "longitude",
        "distance_m",
        "knowledge_deities",
        "knowledge_histories",
    }
    assert candidate["knowledge_deities"] and candidate["knowledge_histories"]


def test_state_names_match_the_existing_monthly_contract():
    assert (
        STATE_DIRECTION_FILTER_UNAVAILABLE == legacy_orchestrator.STATE_DIRECTION_FILTER_UNAVAILABLE
    )
    assert STATE_NO_COMMON_DIRECTION == legacy_orchestrator.STATE_NO_COMMON_DIRECTION
    assert (
        STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES
        == legacy_orchestrator.STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES
    )
    assert STATE_DIRECTION_ZERO_CANDIDATES == legacy_orchestrator.STATE_DIRECTION_ZERO_CANDIDATES
    assert STATE_RECOMMENDATION_SUCCESS == legacy_orchestrator.STATE_RECOMMENDATION_SUCCESS


# --------------------------------------------------------------------------
# I. Query shape（N+1 がないこと。exact budget は置かない）
# --------------------------------------------------------------------------


def test_query_count_does_not_scale_with_candidate_count():
    def _count() -> int:
        with CaptureQueriesContext(connection) as ctx:
            result = _run()
        assert result.state == STATE_RECOMMENDATION_SUCCESS
        return len(ctx.captured_queries)

    # 両方の run で Fact の種類（deity と history）を揃える。種類が無いと Django が
    # その prefetch を発行しないため、件数ではなくデータの形で本数が変わってしまう。
    for km in (3, 6):
        attach_usable_history_fact(_eligible(f"北{km}km", km=km))
    small = _count()

    for index in range(40):
        shrine = _eligible(f"北追加{index}", km=10 + index)
        attach_usable_history_fact(shrine)
    large = _count()

    assert small == large
