import pytest

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.recommendation_quality_measurement import (
    aggregate_measurements,
    build_recommendation_quality_measurement_report,
    build_shrine_reason_provenance,
    classify_provenance,
)


def _candidate(**overrides):
    base = {
        "id": 1,
        "shrine_id": 1,
        "name": "テスト神社",
        "sajin": None,
        "description": None,
        "history_theme": "",
        "knowledge_deities": [],
        "knowledge_histories": [],
    }
    base.update(overrides)
    return base


# --- classify_provenance: 4分類の純粋関数テスト -----------------------------


def test_classify_provenance_fully_knowledge_backed_deity_only():
    assert classify_provenance("KNOWLEDGE_USED", "EMPTY") == "FULLY_KNOWLEDGE_BACKED"


def test_classify_provenance_fully_knowledge_backed_history_only():
    assert classify_provenance("EMPTY", "KNOWLEDGE_USED") == "FULLY_KNOWLEDGE_BACKED"


def test_classify_provenance_fully_knowledge_backed_both():
    assert classify_provenance("KNOWLEDGE_USED", "KNOWLEDGE_USED") == "FULLY_KNOWLEDGE_BACKED"


def test_classify_provenance_partially_knowledge_backed():
    assert classify_provenance("KNOWLEDGE_USED", "LEGACY_USED") == "PARTIALLY_KNOWLEDGE_BACKED"
    assert classify_provenance("LEGACY_USED", "KNOWLEDGE_USED") == "PARTIALLY_KNOWLEDGE_BACKED"


def test_classify_provenance_legacy_backed():
    assert classify_provenance("LEGACY_USED", "EMPTY") == "LEGACY_BACKED"
    assert classify_provenance("EMPTY", "LEGACY_USED") == "LEGACY_BACKED"
    assert classify_provenance("LEGACY_USED", "LEGACY_USED") == "LEGACY_BACKED"


def test_classify_provenance_unknown_when_both_empty():
    assert classify_provenance("EMPTY", "EMPTY") == "UNKNOWN"


# --- build_shrine_reason_provenance: 実際のcandidate dictからの分類 ----------


def test_provenance_empty_facts_is_unknown():
    p = build_shrine_reason_provenance(_candidate())
    assert p.deity_status == "EMPTY"
    assert p.history_status == "EMPTY"
    assert p.classification == "UNKNOWN"


def test_provenance_legacy_only_is_legacy_backed():
    c = _candidate(sajin="天照大神", description="由緒本文レガシー")
    p = build_shrine_reason_provenance(c)
    assert p.deity_status == "LEGACY_USED"
    assert p.history_status == "LEGACY_USED"
    assert p.classification == "LEGACY_BACKED"


def test_provenance_deity_only_knowledge_high_confidence_is_fully_backed():
    c = _candidate(
        knowledge_deities=[{"display_name": "経津主大神", "sort_order": 0, "confidence": "high"}],
    )
    p = build_shrine_reason_provenance(c)
    assert p.deity_status == "KNOWLEDGE_USED"
    assert p.history_status == "EMPTY"
    assert p.classification == "FULLY_KNOWLEDGE_BACKED"


def test_provenance_history_only_knowledge_high_confidence_is_fully_backed():
    c = _candidate(
        knowledge_histories=[
            {
                "history_type": "founding",
                "title": "創建",
                "content": "由緒本文",
                "period_text": "",
                "sort_order": 0,
                "confidence": "high",
            }
        ],
    )
    p = build_shrine_reason_provenance(c)
    assert p.deity_status == "EMPTY"
    assert p.history_status == "KNOWLEDGE_USED"
    assert p.classification == "FULLY_KNOWLEDGE_BACKED"


def test_provenance_mixed_knowledge_deity_and_legacy_history_is_partial():
    c = _candidate(
        description="由緒本文レガシー",
        knowledge_deities=[{"display_name": "祭神A", "sort_order": 0, "confidence": "high"}],
    )
    p = build_shrine_reason_provenance(c)
    assert p.deity_status == "KNOWLEDGE_USED"
    assert p.history_status == "LEGACY_USED"
    assert p.classification == "PARTIALLY_KNOWLEDGE_BACKED"


def test_provenance_low_confidence_knowledge_deity_is_suppressed_not_legacy():
    """confidence=lowはreason生成でsuppressされ、fact["deity"]=Noneになる。
    これは"Legacyが使われた"ことにはならない（Knowledgeが存在したが表示されなかった、
    というEMPTY扱いになる）。suppressed Knowledgeを誤ってLEGACY_USEDへ分類しない
    ことを固定化する。"""
    c = _candidate(
        knowledge_deities=[{"display_name": "祭神B", "sort_order": 0, "confidence": "low"}],
    )
    p = build_shrine_reason_provenance(c)
    assert p.deity_status == "EMPTY"
    assert p.classification == "UNKNOWN"


def test_provenance_mixed_sentinel_confidence_is_suppressed():
    c = _candidate(
        knowledge_deities=[
            {"display_name": "祭神C", "sort_order": 0, "confidence": "high"},
            {"display_name": "祭神D", "sort_order": 1, "confidence": "low"},
        ],
    )
    p = build_shrine_reason_provenance(c)
    assert p.deity_status == "EMPTY"


# --- history_theme 名称衝突ガード（重要回帰ポイント） -----------------------


def test_history_theme_alone_does_not_count_as_history_provenance():
    """Legacy history_theme（分類タグ）のみが存在し、Knowledge ShrineHistoryも
    Legacy descriptionも存在しない場合、history_statusはEMPTYのままであること
    （history_themeがshrine_history由来と誤認されないこと）を固定化する。"""
    c = _candidate(history_theme="学び")
    p = build_shrine_reason_provenance(c)
    assert p.history_status == "EMPTY"
    assert p.classification == "UNKNOWN"


def test_knowledge_shrine_history_is_distinguished_from_history_theme():
    """history_themeとKnowledge ShrineHistoryが両方存在する場合でも、
    分類はKnowledge ShrineHistory側の由来だけで正しく決まることを固定化する。"""
    c = _candidate(
        history_theme="学び",
        knowledge_histories=[
            {
                "history_type": "founding",
                "title": "創建",
                "content": "由緒本文",
                "period_text": "",
                "sort_order": 0,
                "confidence": "high",
            }
        ],
    )
    p = build_shrine_reason_provenance(c)
    assert p.history_status == "KNOWLEDGE_USED"
    assert p.classification == "FULLY_KNOWLEDGE_BACKED"


def test_history_theme_with_legacy_description_is_legacy_backed_not_confused():
    c = _candidate(history_theme="縁", description="由緒本文レガシー")
    p = build_shrine_reason_provenance(c)
    assert p.history_status == "LEGACY_USED"
    assert p.classification == "LEGACY_BACKED"


# --- aggregate_measurements: 決定論的集計 -----------------------------------


def test_aggregate_measurements_counts_and_rates():
    records = [
        build_shrine_reason_provenance(_candidate(id=1, shrine_id=1, sajin="A", description="a")),
        build_shrine_reason_provenance(
            _candidate(
                id=2,
                shrine_id=2,
                knowledge_deities=[{"display_name": "B", "sort_order": 0, "confidence": "high"}],
            )
        ),
        build_shrine_reason_provenance(
            _candidate(
                id=3,
                shrine_id=3,
                sajin="C",
                knowledge_histories=[
                    {
                        "history_type": "founding",
                        "title": "t",
                        "content": "c",
                        "period_text": "",
                        "sort_order": 0,
                        "confidence": "high",
                    }
                ],
            )
        ),
        build_shrine_reason_provenance(_candidate(id=4, shrine_id=4)),
    ]
    report = aggregate_measurements(records)

    assert report["sample_count"] == 4
    assert report["legacy_backed"] == 1
    assert report["fully_knowledge_backed"] == 1
    assert report["partially_knowledge_backed"] == 1
    assert report["unknown"] == 1
    # UNKNOWNは分母から除外しない（sample_count全体を分母に固定する設計）
    assert report["knowledge_backed_rate"] == round(2 / 4, 4)
    assert report["legacy_backed_rate"] == round(1 / 4, 4)
    assert report["unknown_rate"] == round(1 / 4, 4)


def test_aggregate_measurements_is_deterministic():
    records = [
        build_shrine_reason_provenance(_candidate(id=1, shrine_id=1, sajin="A")),
        build_shrine_reason_provenance(_candidate(id=2, shrine_id=2)),
    ]
    first = aggregate_measurements(records)
    second = aggregate_measurements(records)
    assert first == second


def test_aggregate_measurements_empty_sample_does_not_divide_by_zero():
    report = aggregate_measurements([])
    assert report["sample_count"] == 0
    assert report["knowledge_backed_rate"] == 0.0
    assert report["unknown_rate"] == 0.0


# --- build_recommendation_quality_measurement_report: DB統合・read-only ----


@pytest.mark.django_db
def test_report_builder_is_read_only_and_classifies_db_backed_shrines():
    complete = Shrine.objects.create(
        name_jp="完全神社", kind="shrine", address="東京都完全区1-1-1"
    )
    partial_deity_only = Shrine.objects.create(
        name_jp="部分神社（祭神のみ）", kind="shrine", address="東京都部分区1-1-1"
    )
    legacy_only = Shrine.objects.create(
        name_jp="レガシーのみ神社",
        kind="shrine",
        address="東京都レガシー区1-1-1",
        sajin="伝統祭神",
        description="伝統由緒",
    )
    none_shrine = Shrine.objects.create(
        name_jp="無データ神社", kind="shrine", address="東京都無データ区1-1-1"
    )

    source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="公式Source",
        url="https://example-measurement-test.jp/",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )

    deity1 = ShrineDeity.objects.create(
        shrine=complete,
        display_name="祭神甲",
        role="primary",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    deity1.sources.set([source])
    history1 = ShrineHistory.objects.create(
        shrine=complete,
        history_type="founding",
        title="創建",
        content="由緒本文",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    history1.sources.set([source])

    deity2 = ShrineDeity.objects.create(
        shrine=partial_deity_only,
        display_name="祭神乙",
        role="primary",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    deity2.sources.set([source])

    shrine_count_before_report = Shrine.objects.count()
    deity_count_before_report = ShrineDeity.objects.count()
    history_count_before_report = ShrineHistory.objects.count()

    target_ids = [complete.id, partial_deity_only.id, legacy_only.id, none_shrine.id]
    report = build_recommendation_quality_measurement_report(shrine_ids=target_ids)

    assert report["sample_count"] == 4
    by_shrine = {row["shrine_id"]: row for row in report["classification_by_shrine"]}
    assert by_shrine[complete.id]["classification"] == "FULLY_KNOWLEDGE_BACKED"
    assert by_shrine[partial_deity_only.id]["classification"] == "FULLY_KNOWLEDGE_BACKED"
    assert by_shrine[legacy_only.id]["classification"] == "LEGACY_BACKED"
    assert by_shrine[none_shrine.id]["classification"] == "UNKNOWN"

    # deity1 + history1（complete） + deity2（partial_deity_only） = 3件
    assert report["source_confirmed_fact"]["fact_ready_total"] == 3
    assert report["source_confirmed_fact"]["source_confirmed_count"] == 3
    assert report["source_confirmed_fact"]["source_confirmed_fact_rate"] == 1.0

    # read-only: build_recommendation_quality_measurement_report() の呼び出し
    # 前後でレコード数が完全に不変であること（SELECTのみ、writeが一切ないこと）
    assert Shrine.objects.count() == shrine_count_before_report
    assert ShrineDeity.objects.count() == deity_count_before_report
    assert ShrineHistory.objects.count() == history_count_before_report


@pytest.mark.django_db
def test_report_builder_defaults_to_qa_fixture_excluded_all_shrines():
    Shrine.objects.create(name_jp="通常神社", kind="shrine", address="東京都通常区1-1-1")
    Shrine.objects.create(name_jp="テスト神社", kind="shrine", address="東京都テスト区1-1-1")

    report = build_recommendation_quality_measurement_report()

    names = {row["name"] for row in report["classification_by_shrine"]}
    assert "通常神社" in names
    assert "テスト神社" not in names
