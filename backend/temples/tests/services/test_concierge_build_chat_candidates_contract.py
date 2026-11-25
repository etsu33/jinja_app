# -*- coding: utf-8 -*-
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from temples.models import PlaceRef, Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.concierge_chat_candidates import (
    build_chat_candidates,
    build_chat_candidates_with_eligibility,
)
from temples.tests.support.recommendation_eligibility import (
    attach_usable_deity_fact,
    attach_usable_history_fact,
)


@pytest.fixture
def shrine_factory(db):
    def _factory(
        *,
        name: str,
        latitude=None,
        longitude=None,
        address: str = "東京都千代田区",
        place_id: str | None = None,
        popular_score: float = 0.0,
        usable_knowledge: bool = True,
    ) -> Shrine:
        place_ref = None
        if place_id:
            place_ref = PlaceRef.objects.create(place_id=place_id, name=name, address=address)

        shrine = Shrine(
            name_jp=name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            popular_score=popular_score,
            place_ref=place_ref,
        )
        Shrine.objects.bulk_create([shrine])
        created = Shrine.objects.get(pk=shrine.pk)
        if usable_knowledge:
            # Shared Recommendation Eligibility gate: 候補に載るには
            # usable Deity/History Factが最低1件必要。
            attach_usable_deity_fact(created, display_name=f"{name}の祭神")
        return created

    return _factory


@pytest.mark.django_db
def test_candidates_exclude_missing_coordinates(shrine_factory):
    """
    CR-006:
    lat/lng が欠損している shrine は候補に入らない。
    """

    shrine_factory(
        name="OK神社",
        latitude=35.0,
        longitude=139.0,
    )

    shrine_factory(
        name="NG神社",
        latitude=None,
        longitude=None,
    )

    cands = build_chat_candidates(
        lat=35.0,
        lng=139.0,
        area=None,
        goriyaku_tag_ids=None,
        trace_id="test",
    )

    names = [c["name"] for c in cands]

    assert "OK神社" in names
    assert "NG神社" not in names


@pytest.mark.django_db
def test_candidates_exclude_empty_address(shrine_factory):
    """
    CR-006:
    address が空文字の shrine は候補に入らない。
    """

    shrine_factory(
        name="住所あり神社",
        latitude=35.0,
        longitude=139.0,
        address="東京都千代田区1-1",
    )

    shrine_factory(
        name="住所なし神社",
        latitude=35.0,
        longitude=139.0,
        address="",
    )

    cands = build_chat_candidates(
        lat=35.0,
        lng=139.0,
        area=None,
        goriyaku_tag_ids=None,
        trace_id="test",
    )

    names = [c["name"] for c in cands]

    assert "住所あり神社" in names
    assert "住所なし神社" not in names


@pytest.mark.django_db
def test_candidates_include_distance_m(shrine_factory):
    """
    CR-006:
    candidate は distance_m を持つ。
    """

    shrine_factory(
        name="距離テスト神社",
        latitude=35.0,
        longitude=139.0,
        place_id="test_place_id",
    )

    cands = build_chat_candidates(
        lat=35.0,
        lng=139.0,
        area=None,
        goriyaku_tag_ids=None,
        trace_id="test",
    )

    cand = next(c for c in cands if c["name"] == "距離テスト神社")

    assert "distance_m" in cand


@pytest.mark.django_db
def test_candidates_include_place_id_when_available(shrine_factory):
    """
    CR-006:
    place_id がある shrine は candidate に place_id を含む。
    """

    shrine_factory(
        name="place_idテスト神社",
        latitude=35.0,
        longitude=139.0,
        place_id="test_place_id",
    )

    cands = build_chat_candidates(
        lat=35.0,
        lng=139.0,
        area=None,
        goriyaku_tag_ids=None,
        trace_id="test",
    )

    cand = next(c for c in cands if c["name"] == "place_idテスト神社")

    assert cand["place_id"] == "test_place_id"


@pytest.mark.django_db
def test_candidates_are_sorted_by_popular_score_desc(shrine_factory):
    """
    CR-006:
    candidate order は popular_score で降順。
    """

    shrine_factory(
        name="人気低",
        latitude=35.0,
        longitude=139.0,
        popular_score=10,
    )

    shrine_factory(
        name="人気高",
        latitude=35.0,
        longitude=139.0,
        popular_score=100,
    )

    cands = build_chat_candidates(
        lat=35.0,
        lng=139.0,
        area=None,
        goriyaku_tag_ids=None,
        trace_id="test",
    )

    names = [c["name"] for c in cands]

    assert names.index("人気高") < names.index("人気低")


def _create_source(verification_status: str = "source_confirmed") -> ShrineKnowledgeSource:
    kwargs = dict(source_type="shrine_official", title="出典", verification_status=verification_status)
    if verification_status in ("source_confirmed", "reviewed"):
        kwargs["verified_at"] = timezone.now()
    return ShrineKnowledgeSource.objects.create(**kwargs)


@pytest.mark.django_db
def test_candidates_include_fact_ready_knowledge_deities_and_histories(shrine_factory):
    # このtestは自前でusable Deity/Historyを作るため、factoryの自動付与は使わない。
    shrine = shrine_factory(
        name="Knowledge神社", latitude=35.0, longitude=139.0, usable_knowledge=False
    )
    source = _create_source("source_confirmed")

    deity = ShrineDeity.objects.create(
        shrine=shrine, display_name="祭神A", sort_order=0, verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    deity.sources.add(source)

    history = ShrineHistory.objects.create(
        shrine=shrine, history_type="official_origin", title="由緒A", content="内容A", sort_order=0,
        verification_status="source_confirmed", verified_at=timezone.now(),
    )
    history.sources.add(source)

    cands = build_chat_candidates(lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="test")
    cand = next(c for c in cands if c["name"] == "Knowledge神社")

    assert cand["knowledge_deities"] == [{"display_name": "祭神A", "sort_order": 0, "confidence": ""}]
    assert cand["knowledge_histories"][0]["content"] == "内容A"


@pytest.mark.django_db
def test_candidates_exclude_non_fact_ready_knowledge(shrine_factory):
    # usable_knowledge=False にした上で、eligibilityはusable History Factで
    # 満たす。これによりcandidateには載るが、draft Deityはknowledge_deitiesへ
    # 現れない -- Evidence Gateのusable判定がeligibility gateとは独立に
    # 効いていることを示す。
    shrine = shrine_factory(
        name="Draft神社", latitude=35.0, longitude=139.0, usable_knowledge=False
    )
    attach_usable_history_fact(shrine)
    source = _create_source("source_confirmed")

    deity = ShrineDeity.objects.create(
        shrine=shrine, display_name="下書き祭神", sort_order=0, verification_status="draft",
    )
    deity.sources.add(source)

    cands = build_chat_candidates(lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="test")
    cand = next(c for c in cands if c["name"] == "Draft神社")

    assert cand["knowledge_deities"] == []


@pytest.mark.django_db
def test_candidates_knowledge_lookup_does_not_scale_query_count_with_shrine_count(shrine_factory):
    source = _create_source("source_confirmed")
    for i in range(10):
        shrine = shrine_factory(name=f"多数神社{i}", latitude=35.0, longitude=139.0)
        deity = ShrineDeity.objects.create(
            shrine=shrine, display_name=f"祭神{i}", sort_order=0, verification_status="source_confirmed",
            verified_at=timezone.now(),
        )
        deity.sources.add(source)

    with CaptureQueriesContext(connection) as ctx:
        cands = build_chat_candidates(lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="test")

    assert len(cands) >= 10
    # Knowledge selectorはshrine数によらず一定数のクエリ(deity/history各1本)のみ発行する。
    # 全体のクエリ数がshrine数に比例して増えていないことを確認する（目安として30件未満）。
    assert len(ctx.captured_queries) < 30, (
        f"expected knowledge lookup to avoid N+1, got {len(ctx.captured_queries)} queries"
    )


@pytest.mark.django_db
def test_candidates_exclude_known_qa_fixture_naming_patterns(shrine_factory):
    """
    Knowledge Coverage Shadow Audit (audit/knowledge-coverage-shadow-105) で、
    実DB上のid=101-105（「承認テスト神社」「admin承認テスト神社」「重複検証神社」
    「重複検証神社（別宮）」）が既存のnoisy_shrine_names / テストprefix除外の
    いずれにも一致せず、live candidate poolへ混入することを確認した。

    これらは「テスト」で始まらず、「test」でも始まらないため、既存の
    startswith系除外では捕捉できない。本testはこの実在するfixture命名を
    再現し、候補から除外されることを保証する。
    """

    shrine_factory(name="承認テスト神社", latitude=35.0, longitude=139.0)
    shrine_factory(name="admin承認テスト神社", latitude=35.0, longitude=139.0)
    shrine_factory(name="重複検証神社", latitude=35.0, longitude=139.0)
    shrine_factory(name="重複検証神社（別宮）", latitude=35.0, longitude=139.0)
    shrine_factory(name="実在神社", latitude=35.0, longitude=139.0)

    cands = build_chat_candidates(
        lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="test",
    )
    names = [c["name"] for c in cands]

    assert "承認テスト神社" not in names
    assert "admin承認テスト神社" not in names
    assert "重複検証神社" not in names
    assert "重複検証神社（別宮）" not in names
    assert "実在神社" in names


@pytest.mark.django_db
def test_candidates_do_not_over_exclude_shrines_with_mid_name_test_substring(shrine_factory):
    """
    修正がid依存や「テスト」の広範な部分一致に頼っていないことを保証する
    negative guard。「テスト」を名前の途中に含むが実際には除外対象ではない
    shrine（既存の他test（例: test_candidates_include_distance_m）が使う
    命名規約と同様）が、誤って除外されないことを確認する。
    """

    shrine_factory(name="距離テスト神社", latitude=35.0, longitude=139.0)
    shrine_factory(name="place_idテスト神社", latitude=35.0, longitude=139.0)

    cands = build_chat_candidates(
        lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="test",
    )
    names = [c["name"] for c in cands]

    assert "距離テスト神社" in names
    assert "place_idテスト神社" in names


# ---------------------------------------------------------------------------
# F-7: Shrine Identity invariant
# docs/audit/shrine-identity-compass-concierge-contract.md
#
#   SHRINE_IDENTITY_AUTHORITY = Shrine.id
#   PUBLIC_IDENTITY_KEY       = shrine_id
#
# 候補emission（concierge_chat_candidates.py の `"id": s.id` /
# `"shrine_id": s.id`）は Compass と Concierge が共有する唯一の identity 発生点
# である。両surfaceはここから下流で選抜ロジックだけを変え、identityは変えない。
#
# この不変条件はこれまで実装上は真だったが、専用のregression testが無かった。
# 以下はその境界を直接固定する。
# ---------------------------------------------------------------------------


def _persisted_pk_by_name() -> dict[str, int]:
    """候補payloadではなく、永続化されたShrine行からname->PKを引き直す。

    assertionのright-hand sideをpayload由来にしないための補助。
    """
    return {s.name_jp: s.pk for s in Shrine.objects.all()}


@pytest.mark.django_db
def test_candidate_identity_id_equals_shrine_id_equals_persisted_shrine_pk(shrine_factory):
    """F-7: candidate["id"] == candidate["shrine_id"] == 永続化されたShrine.id。

    右辺はDBから読み直したPKであり、candidate payloadから導出しない。
    どちらかのfieldが独立に書き換えられた時点で落ちる。
    """

    shrine_factory(name="識別子神社A", latitude=35.0, longitude=139.0)
    shrine_factory(name="識別子神社B", latitude=35.1, longitude=139.1)
    shrine_factory(name="識別子神社C", latitude=35.2, longitude=139.2)

    expected_pk = _persisted_pk_by_name()

    cands = build_chat_candidates(
        lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="test",
    )

    audited = [c for c in cands if c["name"] in expected_pk]
    assert len(audited) == 3, "3件すべてが候補に載っていること（前提条件）"

    for cand in audited:
        pk = expected_pk[cand["name"]]

        assert cand["shrine_id"] == pk, (
            f"shrine_id が永続化PKと乖離: name={cand['name']} "
            f"shrine_id={cand['shrine_id']!r} Shrine.id={pk!r}"
        )
        assert cand["id"] == pk, (
            f"id が永続化PKと乖離: name={cand['name']} "
            f"id={cand['id']!r} Shrine.id={pk!r}"
        )
        assert cand["id"] == cand["shrine_id"], (
            f"id と shrine_id が独立に書き換えられている: name={cand['name']} "
            f"id={cand['id']!r} shrine_id={cand['shrine_id']!r}"
        )

        # payload -> DB の逆引きでも同一Shrineに解決すること。
        # id が rank / result id に化けた場合、別のShrineか存在しない行を指す。
        resolved = Shrine.objects.filter(pk=cand["shrine_id"]).first()
        assert resolved is not None, f"shrine_id={cand['shrine_id']!r} がShrine行へ解決しない"
        assert resolved.name_jp == cand["name"]


@pytest.mark.django_db
def test_candidate_identity_is_not_rank_or_list_index(shrine_factory):
    """F-7: `id` が rank / list index / 連番へ退化していないこと。

    除外されるdecoyを先に作ってPKを押し上げ、さらにpopular_score降順で
    「PKが減少しながらindexは増加する」並びを作る。これにより
    emitted id列は 0..n-1 でも 1..n でもありえない。
    """

    # 候補に載らないdecoy（座標欠損）。後続ShrineのPKを押し上げるためだけに作る。
    shrine_factory(name="採番押し上げdecoy", latitude=None, longitude=None)

    # 作成順 = PK昇順。popular_scoreは逆順にして、出力順でPKが減少するようにする。
    shrine_factory(name="順位神社_低", latitude=35.0, longitude=139.0, popular_score=10)
    shrine_factory(name="順位神社_中", latitude=35.0, longitude=139.0, popular_score=20)
    shrine_factory(name="順位神社_高", latitude=35.0, longitude=139.0, popular_score=30)

    expected_pk = _persisted_pk_by_name()

    cands = build_chat_candidates(
        lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="test",
    )
    audited = [c for c in cands if c["name"].startswith("順位神社_")]
    assert len(audited) == 3

    # 前提: popular_score降順 = PK降順
    assert [c["name"] for c in audited] == ["順位神社_高", "順位神社_中", "順位神社_低"]
    emitted_ids = [c["id"] for c in audited]
    assert emitted_ids == sorted(emitted_ids, reverse=True), "前提: 出力順でPKが減少する"

    assert emitted_ids != list(range(len(audited))), "id が 0-based list index へ退化している"
    assert emitted_ids != list(range(1, len(audited) + 1)), "id が 1-based rank へ退化している"

    for cand in audited:
        assert cand["id"] == expected_pk[cand["name"]]
        assert cand["shrine_id"] == expected_pk[cand["name"]]


@pytest.mark.django_db
def test_identity_invariant_holds_at_shared_candidate_emission_boundary(shrine_factory):
    """F-7: Concierge経路とCompass経路で同一のidentityが得られること。

    Concierge : api_views_concierge.py   -> build_chat_candidates()
    Compass   : compass_recommendation_orchestrator.py
                                        -> build_chat_candidates_with_eligibility()

    本testはCompass固有コードもConcierge固有UIもimportしない。identityが
    共有emission境界だけで決まり、どちらのsurfaceにも依存しないことを示す。
    """

    shrine_factory(name="共有境界神社A", latitude=35.0, longitude=139.0, popular_score=30)
    shrine_factory(name="共有境界神社B", latitude=35.1, longitude=139.1, popular_score=20)

    expected_pk = _persisted_pk_by_name()

    concierge_entry = build_chat_candidates(
        lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="test",
    )
    compass_entry = build_chat_candidates_with_eligibility(
        lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="test",
    ).candidates

    def identity_map(candidates):
        return {
            c["name"]: (c["id"], c["shrine_id"])
            for c in candidates
            if c["name"].startswith("共有境界神社")
        }

    concierge_identity = identity_map(concierge_entry)
    compass_identity = identity_map(compass_entry)

    assert len(concierge_identity) == 2
    assert concierge_identity == compass_identity, (
        "Concierge経路とCompass経路でShrine identityが乖離している: "
        f"concierge={concierge_identity!r} compass={compass_identity!r}"
    )

    for name, (emitted_id, emitted_shrine_id) in compass_identity.items():
        assert emitted_id == emitted_shrine_id == expected_pk[name]
