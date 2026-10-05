from __future__ import annotations

import copy
import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import GoriyakuTag, Shrine, ShrineSourceFact
from temples.services.channel_b_reason_copy import (
    render_channel_b_reason,
    select_channel_b_reason_match,
)
from temples.services import concierge_chat
from temples.services.channel_b_typed_need_match import (
    CHANNEL_B_REASON_PROVENANCE_KEY,
    CHANNEL_B_TYPED_NEED_MATCHES_KEY,
    fetch_typed_need_matches,
)
from temples.services.concierge_chat_candidates import (
    build_chat_candidates,
    build_chat_candidates_with_eligibility,
)
from temples.services.concierge_chat import build_chat_recommendations
from temples.tests.test_bootstrap_goriyaku_master_exact39_contract import (
    CANONICAL_MASTER,
)

pytestmark = pytest.mark.django_db

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
BASE_SEED_PATH = DATA_DIR / "shrines_seed_clean.json"
KNOWLEDGE_SEED_PATH = DATA_DIR / "knowledge_seeds" / "wave0_batch_04_seed.json"
SOURCE_FACTS_SEED_PATH = (
    DATA_DIR / "knowledge_seeds" / "wave0_batch_04_source_facts_seed.json"
)

EXECUTION_SHRINE_NAMES = {
    "建勲神社",
    "大阪天満宮",
    "大崎八幡宮",
}
ELIGIBILITY_TARGET_NAMES = {"大阪天満宮", "大崎八幡宮"}
# PR-D / PR-E の data から決まる Channel B typed match の件数（SP3 の修正で変わらない）。
EXPECTED_TYPED_MATCH_COUNTS = {"大阪天満宮": 7, "大崎八幡宮": 14}
# 根拠のない神社固有の御利益の断定（SP3）。
UNSUPPORTED_BENEFIT_CLAIMS = ("ご利益で知られる", "のご利益がある")
# MS-5: request の Need（study）に Channel B だけが一致するときに選ばれる Source Fact と理由文。
MS5_REQUEST_NEED = "study"
EXPECTED_MS5_SOURCE_FACT_KEY = {
    "大阪天満宮": "osaka_tenmangu__prayer_and_current_guidance__gakugyo_joju",
    "大崎八幡宮": "osaki_hachimangu__prayer__gakugyo_joju",
}
EXPECTED_MS5_SIGNAL_TYPE = {
    "大阪天満宮": "official_prayer_and_current_guidance_list_level",
    "大崎八幡宮": "official_prayer_supported",
}
EXPECTED_MS5_REASON = {
    "大阪天満宮": (
        "大阪天満宮の公式の祈願・現在の案内の一覧に『学業成就』が含まれています。"
        "今の悩みや願いに合わせて参拝先の候補に入れています。"
    ),
    "大崎八幡宮": (
        "大崎八幡宮の公式の祈願案内に『学業成就』の記載があります。"
        "今の悩みや願いに合わせて参拝先の候補に入れています。"
    ),
}


def _assert_sp3_safe(recommendation: dict, reason_text: str) -> None:
    """fallback sentinel を Need evidence として扱わず、根拠のない御利益の断定を作らない。"""
    reason_facts = recommendation.get("_reason_facts") or []
    fallback_facts = [fact for fact in reason_facts if fact.get("type") == "fallback"]
    # sentinel 自体は変えない（evidence がない、という判定はそのまま）。
    assert recommendation.get("_primary_reason_source") == "fallback"
    assert recommendation.get("_primary_reason_label") == "fallback"
    assert len(fallback_facts) == 1 and not fallback_facts[0].get("evidence")
    assert not (recommendation.get("breakdown") or {}).get("matched_need_tags")
    # sentinel を Need label として文にしない。
    assert "fallback" not in reason_text
    for claim in UNSUPPORTED_BENEFIT_CLAIMS:
        assert claim not in reason_text


def test_wave0_db04_g6_runtime_imports_isolated_seed_and_passes_shared_eligibility(
    tmp_path,
    monkeypatch,
):
    # 公開の出口（strip_channel_b_carrier）の直前の recommendation を記録する（内部 provenance の確認用）。
    pre_strip_rows: list[dict] = []
    real_strip = concierge_chat.strip_channel_b_carrier

    def _capture_before_strip(recs):
        pre_strip_rows[:] = [copy.deepcopy(r) for r in recs.get("recommendations") or []]
        return real_strip(recs)

    monkeypatch.setattr(concierge_chat, "strip_channel_b_carrier", _capture_before_strip)

    def _internal_row(row_name: str) -> dict:
        return next(row for row in pre_strip_rows if row.get("name") == row_name)

    base_rows = json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))
    execution_rows = [
        row for row in base_rows if row.get("name_jp") in EXECUTION_SHRINE_NAMES
    ]
    assert len(execution_rows) == len(EXECUTION_SHRINE_NAMES)
    assert {row["name_jp"] for row in execution_rows} == EXECUTION_SHRINE_NAMES

    isolated_base_path = tmp_path / "wave0_db04_base_seed.json"
    isolated_base_path.write_text(
        json.dumps(execution_rows, ensure_ascii=False),
        encoding="utf-8",
    )

    output = io.StringIO()
    call_command(
        "import_shrines_seed",
        source=str(isolated_base_path),
        stdout=output,
    )
    call_command(
        "import_shrine_knowledge",
        str(KNOWLEDGE_SEED_PATH),
        stdout=output,
    )
    call_command(
        "import_shrine_knowledge",
        str(SOURCE_FACTS_SEED_PATH),
        stdout=output,
    )

    imported_shrines = Shrine.objects.filter(name_jp__in=EXECUTION_SHRINE_NAMES)
    assert imported_shrines.count() == len(EXECUTION_SHRINE_NAMES)
    assert set(imported_shrines.values_list("name_jp", flat=True)) == EXECUTION_SHRINE_NAMES

    for name in ELIGIBILITY_TARGET_NAMES:
        shrine = Shrine.objects.get(name_jp=name)
        assert shrine.address.strip()
        assert shrine.latitude is not None
        assert shrine.longitude is not None
        assert shrine.goriyaku_tags.count() == 0

    for tag_id, tag_name in CANONICAL_MASTER:
        GoriyakuTag.objects.update_or_create(id=tag_id, defaults={"name": tag_name})

    result = build_chat_candidates_with_eligibility(
        lat=None,
        lng=None,
        area=None,
        trace_id="wave0-db04-g6-runtime-qa",
    )
    candidates_by_name = {candidate["name"]: candidate for candidate in result.candidates}

    for name in ELIGIBILITY_TARGET_NAMES:
        candidate = candidates_by_name[name]
        assert candidate["knowledge_deities"] or candidate["knowledge_histories"]

    base_rows_by_name = {row["name_jp"]: row for row in execution_rows}
    source_facts_seed = json.loads(SOURCE_FACTS_SEED_PATH.read_text(encoding="utf-8"))
    source_fact_keys_by_name = {
        entry["shrine_ref"]["name_jp"]: {
            fact["stable_key"] for fact in entry.get("source_facts", [])
        }
        for entry in source_facts_seed["shrines"]
    }
    for name in sorted(ELIGIBILITY_TARGET_NAMES):
        base_row = base_rows_by_name[name]
        candidates = build_chat_candidates(
            lat=base_row["latitude"],
            lng=base_row["longitude"],
            trace_id=f"wave0-db04-g6-runtime-{name}",
        )
        candidate = next(
            (row for row in candidates if row["name"] == name),
            None,
        )
        assert candidate is not None
        assert candidate["goriyaku_tag_ids"] == []
        assert not candidate["goriyaku"]

        shrine = Shrine.objects.get(name_jp=name)
        typed_matches = fetch_typed_need_matches([shrine.id])[shrine.id]
        assert typed_matches
        assert all(match.source_fact_key for match in typed_matches)
        assert all(match.canonical_concept_name for match in typed_matches)
        assert {
            match.source_fact_key for match in typed_matches
        } <= source_fact_keys_by_name[name]
        assert {
            match.canonical_concept_name for match in typed_matches
        } <= {tag_name for _, tag_name in CANONICAL_MASTER}
        shrine.refresh_from_db()
        assert shrine.goriyaku_tags.count() == 0

        recommendations = build_chat_recommendations(
            query="",
            language="ja",
            candidates=[candidate],
            bias={"lat": base_row["latitude"], "lng": base_row["longitude"]},
            public_mode="need",
            flow="A",
            need_tags=[],
            llm_enabled=False,
        )
        recommendation = next(
            row
            for row in recommendations["recommendations"]
            if row.get("name") == name
        )
        reason_facts = recommendation.get("_reason_facts") or []
        source_fact_keys = sorted({match.source_fact_key for match in typed_matches})
        reason_text = str(recommendation.get("reason") or "")
        reason_blob = json.dumps(
            [reason_text, reason_facts],
            ensure_ascii=False,
            default=str,
        )
        source_markers = {
            marker
            for match in typed_matches
            for marker in (
                match.source_fact_key,
                match.canonical_concept_name,
                match.source_attested_wording,
            )
            if marker
        }
        source_fact_used_by_reason = any(
            marker in reason_blob for marker in source_markers
        )
        assert typed_matches
        assert len(typed_matches) == EXPECTED_TYPED_MATCH_COUNTS[name]
        # request の Need が無いときは Channel B の理由文を作らない（MS-5）。
        assert not source_fact_used_by_reason
        _assert_sp3_safe(recommendation, reason_text)
        sp3_reproduced = False
        # Channel B の理由文を使わないので、内部 provenance も無い。
        assert CHANNEL_B_REASON_PROVENANCE_KEY not in _internal_row(name)

        # MS-5: request の Need に Channel B だけが一致するとき、Source-backed の理由文になる。
        ms5_recommendations = build_chat_recommendations(
            query="",
            language="ja",
            candidates=[candidate],
            bias={"lat": base_row["latitude"], "lng": base_row["longitude"]},
            public_mode="need",
            flow="A",
            need_tags=[MS5_REQUEST_NEED],
            llm_enabled=False,
        )
        ms5_recommendation = next(
            row
            for row in ms5_recommendations["recommendations"]
            if row.get("name") == name
        )
        ms5_reason_text = str(ms5_recommendation.get("reason") or "")
        selected = select_channel_b_reason_match(
            {CHANNEL_B_TYPED_NEED_MATCHES_KEY: typed_matches}, [MS5_REQUEST_NEED], []
        )
        assert selected is not None
        assert selected.source_fact_key == EXPECTED_MS5_SOURCE_FACT_KEY[name]
        assert ms5_reason_text == render_channel_b_reason(selected, name=name)
        assert ms5_reason_text == EXPECTED_MS5_REASON[name]
        assert f"『{selected.source_attested_wording}』" in ms5_reason_text
        # 内部 provenance（公開の出口の前）は、理由文に使った match と同じ Source Fact を指す。
        provenance = _internal_row(name)[CHANNEL_B_REASON_PROVENANCE_KEY]
        assert provenance == {
            "channel": "channel_b",
            "type": "channel_b_source_fact",
            "source_fact_key": selected.source_fact_key,
            "signal_type": selected.signal_type,
            "need": MS5_REQUEST_NEED,
        }
        assert provenance["source_fact_key"] == EXPECTED_MS5_SOURCE_FACT_KEY[name]
        assert provenance["signal_type"] == EXPECTED_MS5_SIGNAL_TYPE[name]
        # 公開の出口の後には、provenance・carrier・source_fact_key のいずれも残らない。
        public_blob = json.dumps(ms5_recommendations, ensure_ascii=False, default=str)
        assert CHANNEL_B_REASON_PROVENANCE_KEY not in public_blob
        assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in public_blob
        assert "source_fact_key" not in public_blob
        assert selected.source_fact_key not in public_blob
        # Channel A の evidence は無いまま（primary reason は fallback sentinel、matched_need_tags は空）。
        _assert_sp3_safe(ms5_recommendation, ms5_reason_text)
        # Channel B の数値は PR-F のまま（B だけの Need 1件 = +2.0）。
        ms5_need = ms5_recommendation["breakdown_detail"]["features"]["need"]
        assert ms5_need["rank_raw"] == 0
        assert ms5_need["rank_weighted"] == pytest.approx(2.0)
        assert len(fetch_typed_need_matches([shrine.id])[shrine.id]) == len(typed_matches)
        shrine.refresh_from_db()
        assert shrine.goriyaku_tags.count() == 0
        assert candidate["goriyaku_tag_ids"] == []
        print(
            "G6_REASON_OBSERVATION",
            {
                "shrine": name,
                "primary_reason_label": recommendation.get("_primary_reason_label"),
                "reason_text": reason_text,
                "channel_b_typed_match": bool(typed_matches),
                "channel_b_typed_match_count": len(typed_matches),
                "source_fact_keys": source_fact_keys,
                "source_fact_used_by_reason": source_fact_used_by_reason,
                "sp3_reproduced": sp3_reproduced,
                "ms5_request_need": MS5_REQUEST_NEED,
                "ms5_selected_source_fact_key": selected.source_fact_key,
                "ms5_signal_type": selected.signal_type,
                "ms5_reason_text": ms5_reason_text,
                "ms5_reason_provenance": provenance,
                "ms5_reason_provenance_matches_selected": (
                    provenance["source_fact_key"] == selected.source_fact_key
                ),
            },
        )

    shrine = Shrine.objects.get(name_jp="建勲神社")
    eligibility_candidate = candidates_by_name.get("建勲神社")
    assert eligibility_candidate is not None
    base_row = base_rows_by_name["建勲神社"]
    candidate = next(
        (
            row
            for row in build_chat_candidates(
                lat=base_row["latitude"],
                lng=base_row["longitude"],
                trace_id="wave0-db04-g6-runtime-建勲神社",
            )
            if row["name"] == "建勲神社"
        ),
        None,
    )
    assert candidate is not None
    typed_matches = fetch_typed_need_matches([shrine.id]).get(shrine.id, ())
    recommendations = build_chat_recommendations(
        query="",
        language="ja",
        candidates=[candidate],
        bias={"lat": base_row["latitude"], "lng": base_row["longitude"]},
        public_mode="need",
        flow="A",
        need_tags=[],
        llm_enabled=False,
    )
    recommendation = next(
        row
        for row in recommendations["recommendations"]
        if row.get("name") == "建勲神社"
    )
    preview = next(
        (
            row.get("preview")
            for row in recommendations.get("_debug", {}).get("reason_v4_preview", [])
            if row.get("name") == "建勲神社"
        ),
        {},
    )
    reason_v4_text = str(preview.get("reason_text") or "")
    used_fact = preview.get("used_fact") or {}
    stored_deity_names = {
        item["display_name"] for item in candidate.get("knowledge_deities", [])
    }
    deity_used_by_reason = str(used_fact.get("deity") or "")
    shared_eligibility_passed = bool(
        eligibility_candidate.get("knowledge_deities")
        or eligibility_candidate.get("knowledge_histories")
    )
    source_fact_count = ShrineSourceFact.objects.filter(shrine=shrine).count()
    safe_recommendation_evidence_path = (
        shared_eligibility_passed
        and source_fact_count == 0
        and not typed_matches
        and bool(stored_deity_names)
        and all(name in deity_used_by_reason for name in stored_deity_names)
        and deity_used_by_reason in reason_v4_text
        and "補助情報であり、今回の順位根拠ではありません" in reason_v4_text
        and recommendation.get("recommendation_reason_quality", {}).get(
            "deity_knowledge_used"
        )
        is True
    )
    assert shared_eligibility_passed
    assert source_fact_count == 0
    assert not typed_matches
    assert shrine.goriyaku == ""
    assert list(shrine.goriyaku_tags.values_list("name", flat=True)) == []
    assert candidate["goriyaku_tag_ids"] == []
    assert not candidate["goriyaku"]
    assert safe_recommendation_evidence_path
    _assert_sp3_safe(recommendation, str(recommendation.get("reason") or ""))
    # MS-5: Source Fact も typed match も無いので、request の Need があっても Channel B の
    # 理由文は作らない（既存の generic fallback のまま）。
    kenkun_ms5 = next(
        row
        for row in build_chat_recommendations(
            query="",
            language="ja",
            candidates=[candidate],
            bias={"lat": base_row["latitude"], "lng": base_row["longitude"]},
            public_mode="need",
            flow="A",
            need_tags=[MS5_REQUEST_NEED],
            llm_enabled=False,
        )["recommendations"]
        if row.get("name") == "建勲神社"
    )
    assert not candidate.get(CHANNEL_B_TYPED_NEED_MATCHES_KEY)
    assert CHANNEL_B_REASON_PROVENANCE_KEY not in _internal_row("建勲神社")
    assert kenkun_ms5["reason"] == "建勲神社は、今の悩みや願いに合わせて参拝先の候補に入れています。"
    assert "公式の" not in kenkun_ms5["reason"] and "『" not in kenkun_ms5["reason"]
    _assert_sp3_safe(kenkun_ms5, kenkun_ms5["reason"])
    print(
        "G6_WAVE0_019_OBSERVATION",
        {
            "shared_eligibility": "PASS" if shared_eligibility_passed else "FAIL",
            "candidate_universe": candidate is not None,
            "goriyaku": shrine.goriyaku,
            "goriyaku_tags": list(shrine.goriyaku_tags.values_list("name", flat=True)),
            "source_fact_count": source_fact_count,
            "channel_b_typed_match_count": len(typed_matches),
            "primary_reason_label": recommendation.get("_primary_reason_label"),
            "reason_text": recommendation.get("reason"),
            "ms5_reason_text": kenkun_ms5["reason"],
            "ms5_reason_provenance": _internal_row("建勲神社").get(
                CHANNEL_B_REASON_PROVENANCE_KEY
            ),
            "reason_facts": recommendation.get("_reason_facts"),
            "reason_v4_text": reason_v4_text,
            "evidence_used_by_reason": {
                "deity": used_fact.get("deity"),
                "shrine_history": used_fact.get("shrine_history"),
            },
            "recommendation_reason_quality": recommendation.get(
                "recommendation_reason_quality"
            ),
            "safe_recommendation_evidence_path": (
                "PASS" if safe_recommendation_evidence_path else "FAIL"
            ),
        },
    )
