#!/usr/bin/env python
"""Read-only audit simulation: geographic availability impact of a proposed
Knowledge eligibility gate.

Compares two candidate populations:

    Baseline .... 103 canonical shrines
                  (backend/temples/data/shrines_seed_clean.json)
    Gated ....... 89 Knowledge-usable shrines
                  (the same 103 minus the 14 shrines documented as having no
                  Knowledge in docs/audit/shrine-geographic-knowledge-coverage.md
                  Section 6, unchanged by Batch 17 per
                  docs/audit/shrine-geographic-batch18-candidate-selection.md)

This script NEVER writes to the database, never queries the database, and
never modifies Recommendation / Ranking / Direction / Distance logic. Every
piece of filtering logic it exercises is IMPORTED from production modules
rather than reimplemented:

    temples.services.concierge_chat_candidates._distance_m
    temples.services.compass_direction_filter.filter_candidates_by_direction
    temples.services.compass_recommendation_orchestrator._apply_compass_distance_stage
    temples.services.direction_reference._DIRECTION_LABELS
    temples.management.commands.backfill_goriyaku_tags.parse_goriyaku
    temples.domain.need_to_goriyaku_tag_ids.need_tags_to_goriyaku_ids
    temples.domain.need_tags.NEED_TAGS

The 89-shrine restriction is applied ONLY inside this simulation.

Usage:
    DJANGO_SETTINGS_MODULE=shrine_project.settings \
    PYTHONPATH=backend USE_GIS=0 \
    python scripts/audit_recommendation_eligibility_geographic_impact.py \
        [--json OUT.json]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shrine_project.settings")
os.environ.setdefault("USE_GIS", "0")
os.environ.setdefault("USE_SQLITE", "0")
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "dummy")
os.environ.setdefault("GOOGLE_PLACES_API_KEY", "dummy")
os.environ.setdefault("ROUTE_PROVIDER", "dummy")

import django  # noqa: E402

django.setup()

from temples.domain.need_tags import NEED_TAGS  # noqa: E402
from temples.domain.need_to_goriyaku_tag_ids import (  # noqa: E402
    need_tags_to_goriyaku_ids,
)
from temples.management.commands.backfill_goriyaku_tags import (  # noqa: E402
    parse_goriyaku,
)
from temples.services.compass_direction_filter import (  # noqa: E402
    filter_candidates_by_direction,
)
from temples.services.compass_recommendation_orchestrator import (  # noqa: E402
    DEFAULT_CANDIDATE_POOL_LIMIT,
    DISTANCE_STAGE_1_KM,
    DISTANCE_STAGE_2_KM,
    DISTANCE_STAGE_3_KM,
    DISTANCE_STAGE_EXPANSION_THRESHOLD,
    _apply_compass_distance_stage,
)
from temples.services.concierge_chat_candidates import (  # noqa: E402
    DEFAULT_LIMIT as CONCIERGE_DEFAULT_LIMIT,
)
from temples.services.concierge_chat_candidates import _distance_m  # noqa: E402
from temples.services.direction_reference import _DIRECTION_LABELS  # noqa: E402

# --------------------------------------------------------------------------
# Versioned repository data sources (no invented values)
# --------------------------------------------------------------------------

SEED_PATH = BACKEND / "temples" / "data" / "shrines_seed_clean.json"
USER_ORIGIN_TS = REPO_ROOT / "packages" / "shared" / "userOrigin.ts"

# docs/audit/shrine-geographic-knowledge-coverage.md Section 6 ("Knowledge
# 未投入Shrine地域分布（14件）"). Confirmed unchanged by Batch 17 in
# docs/audit/shrine-geographic-batch18-candidate-selection.md Section 2
# ("Knowledgeなし総数 14（不変）").
KNOWLEDGE_ABSENT_SHRINES: tuple[str, ...] = (
    "千住神社",
    "鳥越神社",
    "花園神社",
    "靖國神社",
    "愛宕神社",
    "長太稲荷神社",
    "赤城神社",
    "冠稲荷神社",
    "榛名神社",
    "調神社",
    "武蔵一宮 氷川女體神社",
    "古峯神社",
    "千葉神社",
    "高千穂神社",
)

# docs/audit/goriyaku-mapping-master-integrity.md Section 4 ("Canonical
# Master", 39 rows, contiguous ids 1-39). This table is the id<->label
# authority NEED_TO_GORIYAKU_IDS is pinned against by
# backend/temples/tests/test_need_to_goriyaku_tag_ids.py
# (CANONICAL_MASTER_ID_RANGE = range(1, 40)).
CANONICAL_GORIYAKU_MASTER: dict[int, str] = {
    1: "縁結び", 2: "厄除け", 3: "交通安全", 4: "商売繁盛", 5: "五穀豊穣",
    6: "開運", 7: "家内安全", 8: "福徳", 9: "学業成就", 10: "合格祈願",
    11: "勝運", 12: "仕事運", 13: "航海安全", 14: "海上安全", 15: "武運長久",
    16: "安産", 17: "八方除", 18: "夫婦円満", 19: "八難除", 20: "恋愛成就",
    21: "導き", 22: "美容", 23: "方除け", 24: "健康長寿", 25: "芸能",
    26: "家庭円満", 27: "出世運", 28: "金運", 29: "芸能運", 30: "強運厄除け",
    31: "技芸上達", 32: "八方除け", 33: "病気平癒", 34: "火防", 35: "子宝",
    36: "心願成就", 37: "延命長寿", 38: "足腰健康", 39: "農業守護",
}
LABEL_TO_GID = {label: gid for gid, label in CANONICAL_GORIYAKU_MASTER.items()}

# docs/audit/shrine-geographic-knowledge-coverage.md Section "2. 地方別"
REGIONS: dict[str, tuple[str, ...]] = {
    "北海道": ("北海道",),
    "東北": ("青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県"),
    "関東": ("茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県"),
    "中部": (
        "新潟県", "富山県", "石川県", "福井県", "山梨県",
        "長野県", "岐阜県", "静岡県", "愛知県",
    ),
    "近畿": ("三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県"),
    "中国": ("鳥取県", "島根県", "岡山県", "広島県", "山口県"),
    "四国": ("徳島県", "香川県", "愛媛県", "高知県"),
    "九州・沖縄": (
        "福岡県", "佐賀県", "長崎県", "熊本県",
        "大分県", "宮崎県", "鹿児島県", "沖縄県",
    ),
}
PREFECTURE_TO_REGION = {
    pref: region for region, prefs in REGIONS.items() for pref in prefs
}

# The 2 known Google-Maps-format addresses documented by
# docs/audit/shrine-geographic-knowledge-coverage.md ("address前方一致、
# Google Maps形式2件の既知例外処理"). Same normalization, not a new parser.
_GMAPS_PREFIX_RE = re.compile(r"^日本、〒?[0-9\-－]*\s*")


def load_prefecture_origins() -> list[dict[str, Any]]:
    """Parse PREFECTURE_ORIGINS out of packages/shared/userOrigin.ts.

    This is the origin corpus the product itself uses when a user picks a
    prefecture as their origin (source: "prefecture"). Versioned in the
    repository; no origin is invented here.
    """
    text = USER_ORIGIN_TS.read_text(encoding="utf-8")
    rows = re.findall(r'\["([^"]+)",\s*([0-9.\-]+),\s*([0-9.\-]+)\]', text)
    origins = [
        {"name": name, "lat": float(lat), "lng": float(lng)}
        for name, lat, lng in rows
    ]
    if len(origins) != 47:
        raise SystemExit(
            f"expected 47 prefecture origins in {USER_ORIGIN_TS}, got {len(origins)}"
        )
    return origins


def prefecture_of(address: str) -> str | None:
    normalized = _GMAPS_PREFIX_RE.sub("", str(address or "")).strip()
    for pref in PREFECTURE_TO_REGION:
        if normalized.startswith(pref):
            return pref
    return None


def load_populations() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict]:
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    baseline: list[dict[str, Any]] = []
    unmapped_labels: dict[str, int] = {}
    for row in seed:
        labels = parse_goriyaku(row.get("goriyaku") or "")
        gids = sorted(
            {LABEL_TO_GID[label] for label in labels if label in LABEL_TO_GID}
        )
        for label in labels:
            if label not in LABEL_TO_GID:
                unmapped_labels[label] = unmapped_labels.get(label, 0) + 1
        pref = prefecture_of(row.get("address"))
        baseline.append(
            {
                # build_chat_candidates() candidate shape (subset used by the
                # imported filters: lat/lng/latitude/longitude, distance_m).
                "name": row["name_jp"],
                "address": row.get("address"),
                "lat": row.get("latitude"),
                "lng": row.get("longitude"),
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude"),
                "goriyaku": row.get("goriyaku"),
                "goriyaku_tag_ids": gids,
                "goriyaku_labels": labels,
                "prefecture": pref,
                "region": PREFECTURE_TO_REGION.get(pref) if pref else None,
                "knowledge_usable": row["name_jp"] not in KNOWLEDGE_ABSENT_SHRINES,
            }
        )

    gated = [s for s in baseline if s["knowledge_usable"]]
    meta = {
        "seed_rows": len(seed),
        "baseline_count": len(baseline),
        "gated_count": len(gated),
        "unmapped_goriyaku_labels": unmapped_labels,
        "unresolved_prefecture": [
            s["name"] for s in baseline if s["prefecture"] is None
        ],
        "missing_coordinates": [
            s["name"] for s in baseline if s["lat"] is None or s["lng"] is None
        ],
    }
    return baseline, gated, meta


# --------------------------------------------------------------------------
# Concierge
# --------------------------------------------------------------------------


def concierge_report(
    baseline: list[dict[str, Any]], gated: list[dict[str, Any]]
) -> dict[str, Any]:
    """Concierge candidate availability, baseline vs gated.

    Two distinct quantities are measured, deliberately kept separate:

    1. pool: the shrine population that reaches build_chat_candidates()'s
       pool slice. build_chat_candidates uses
       pool_limit = max(limit * 5, 50); Concierge's DEFAULT_LIMIT is 20, so
       pool_limit = 100 and a 103-row population is truncated to 100 before
       distance sorting. Which 3 rows are dropped is decided by
       `-popular_score, id` ordering, and popular_score is a runtime-computed
       field absent from the versioned seed -- so the identity of the dropped
       rows is NOT determinable from repository data and is reported as a
       bounded uncertainty, never guessed.

    2. need evidence: per Need tag, how many shrines carry at least one
       GoriyakuTag id in NEED_TO_GORIYAKU_IDS[need] (the `matched_by_gid`
       evidence channel of C1). A need with 0 such shrines has no GID
       evidence anywhere in the population.
    """
    pool_limit = max(CONCIERGE_DEFAULT_LIMIT * 5, 50)

    by_pref: dict[str, dict[str, int]] = {}
    for pref in PREFECTURE_TO_REGION:
        b = sum(1 for s in baseline if s["prefecture"] == pref)
        g = sum(1 for s in gated if s["prefecture"] == pref)
        by_pref[pref] = {"baseline": b, "gated": g, "delta": g - b}

    by_region: dict[str, dict[str, int]] = {}
    for region in REGIONS:
        b = sum(1 for s in baseline if s["region"] == region)
        g = sum(1 for s in gated if s["region"] == region)
        by_region[region] = {"baseline": b, "gated": g, "delta": g - b}

    needs: dict[str, dict[str, Any]] = {}
    for need in NEED_TAGS:
        expected = need_tags_to_goriyaku_ids([need])
        b_hits = [s for s in baseline if expected & set(s["goriyaku_tag_ids"])]
        g_hits = [s for s in gated if expected & set(s["goriyaku_tag_ids"])]
        needs[need] = {
            "expected_gids": sorted(expected),
            "expected_labels": [
                CANONICAL_GORIYAKU_MASTER[g]
                for g in sorted(expected)
                if g in CANONICAL_GORIYAKU_MASTER
            ],
            "baseline": len(b_hits),
            "gated": len(g_hits),
            "delta": len(g_hits) - len(b_hits),
            "zero_baseline": len(b_hits) == 0,
            "zero_gated": len(g_hits) == 0,
            "newly_zero": len(b_hits) > 0 and len(g_hits) == 0,
            "lost_shrines": sorted(
                {s["name"] for s in b_hits} - {s["name"] for s in g_hits}
            ),
        }

    need_pref: dict[str, dict[str, dict[str, int]]] = {}
    for need in NEED_TAGS:
        expected = need_tags_to_goriyaku_ids([need])
        per_pref: dict[str, dict[str, int]] = {}
        for pref in PREFECTURE_TO_REGION:
            b = sum(
                1
                for s in baseline
                if s["prefecture"] == pref and expected & set(s["goriyaku_tag_ids"])
            )
            g = sum(
                1
                for s in gated
                if s["prefecture"] == pref and expected & set(s["goriyaku_tag_ids"])
            )
            if b or g:
                per_pref[pref] = {"baseline": b, "gated": g, "delta": g - b}
        need_pref[need] = per_pref

    return {
        "pool_limit": pool_limit,
        "concierge_default_limit": CONCIERGE_DEFAULT_LIMIT,
        "pool_baseline": min(len(baseline), pool_limit),
        "pool_gated": min(len(gated), pool_limit),
        "pool_truncated_baseline": max(0, len(baseline) - pool_limit),
        "population_baseline": len(baseline),
        "population_gated": len(gated),
        "by_prefecture": by_pref,
        "by_region": by_region,
        "need_evidence": needs,
        "need_evidence_by_prefecture": need_pref,
        "zero_prefectures_baseline": sorted(
            p for p, v in by_pref.items() if v["baseline"] == 0
        ),
        "zero_prefectures_gated": sorted(
            p for p, v in by_pref.items() if v["gated"] == 0
        ),
        "newly_zero_prefectures": sorted(
            p for p, v in by_pref.items() if v["baseline"] > 0 and v["gated"] == 0
        ),
        "newly_zero_regions": sorted(
            r for r, v in by_region.items() if v["baseline"] > 0 and v["gated"] == 0
        ),
        "newly_zero_needs": sorted(n for n, v in needs.items() if v["newly_zero"]),
    }


# --------------------------------------------------------------------------
# Compass
# --------------------------------------------------------------------------


def _with_distance(
    population: list[dict[str, Any]], origin: dict[str, Any]
) -> list[dict[str, Any]]:
    """Attach distance_m exactly as build_chat_candidates() does."""
    out = []
    for shrine in population:
        record = dict(shrine)
        record["distance_m"] = _distance_m(
            origin["lat"], origin["lng"], shrine["lat"], shrine["lng"]
        )
        out.append(record)
    # build_chat_candidates sorts by distance when lat/lng are supplied.
    out.sort(key=lambda c: float(c.get("distance_m") or 1e12))
    # pool_limit = max(limit * 5, 50); Compass passes limit=60 -> 300.
    pool_limit = max(DEFAULT_CANDIDATE_POOL_LIMIT * 5, 50)
    return out[:pool_limit]


def _within_km(candidates: list[dict[str, Any]], km: int) -> int:
    limit_m = km * 1000
    return sum(
        1
        for c in candidates
        if isinstance(c.get("distance_m"), (int, float))
        and not isinstance(c.get("distance_m"), bool)
        and c["distance_m"] <= limit_m
    )


def compass_report(
    baseline: list[dict[str, Any]],
    gated: list[dict[str, Any]],
    origins: list[dict[str, Any]],
) -> dict[str, Any]:
    cells: list[dict[str, Any]] = []

    for origin in origins:
        pool_b = _with_distance(baseline, origin)
        pool_g = _with_distance(gated, origin)
        for direction in _DIRECTION_LABELS:
            row: dict[str, Any] = {
                "origin": origin["name"],
                "region": PREFECTURE_TO_REGION.get(origin["name"]),
                "direction": direction,
            }
            for label, pool in (("baseline", pool_b), ("gated", pool_g)):
                filtered = filter_candidates_by_direction(
                    pool,
                    origin={"lat": origin["lat"], "lng": origin["lng"]},
                    reference_directions=[direction],
                )
                filtered = list(filtered or [])
                staged, stage_km = _apply_compass_distance_stage(filtered)
                row[label] = {
                    "direction_candidates": len(filtered),
                    "within_15km": _within_km(filtered, DISTANCE_STAGE_1_KM),
                    "within_30km": _within_km(filtered, DISTANCE_STAGE_2_KM),
                    "within_60km": _within_km(filtered, DISTANCE_STAGE_3_KM),
                    "stage_km": stage_km,
                    "stage_candidates": len(staged),
                    "direction_zero": len(filtered) == 0,
                    "distance_zero": len(filtered) > 0 and len(staged) == 0,
                    "final_zero": len(staged) == 0,
                }
            row["newly_direction_zero"] = (
                not row["baseline"]["direction_zero"] and row["gated"]["direction_zero"]
            )
            row["newly_final_zero"] = (
                not row["baseline"]["final_zero"] and row["gated"]["final_zero"]
            )
            cells.append(row)

    def _agg(label: str, key: str) -> int:
        return sum(1 for c in cells if c[label][key])

    total = len(cells)
    summary = {
        "origins": len(origins),
        "directions": len(_DIRECTION_LABELS),
        "cells": total,
        "baseline": {
            "direction_zero": _agg("baseline", "direction_zero"),
            "distance_zero": _agg("baseline", "distance_zero"),
            "final_zero": _agg("baseline", "final_zero"),
            "stage_15": sum(1 for c in cells if c["baseline"]["stage_km"] == 15),
            "stage_30": sum(1 for c in cells if c["baseline"]["stage_km"] == 30),
            "stage_60": sum(1 for c in cells if c["baseline"]["stage_km"] == 60),
            "zero_within_15km": sum(
                1 for c in cells if c["baseline"]["within_15km"] == 0
            ),
            "zero_within_30km": sum(
                1 for c in cells if c["baseline"]["within_30km"] == 0
            ),
            "zero_within_60km": sum(
                1 for c in cells if c["baseline"]["within_60km"] == 0
            ),
        },
        "gated": {
            "direction_zero": _agg("gated", "direction_zero"),
            "distance_zero": _agg("gated", "distance_zero"),
            "final_zero": _agg("gated", "final_zero"),
            "stage_15": sum(1 for c in cells if c["gated"]["stage_km"] == 15),
            "stage_30": sum(1 for c in cells if c["gated"]["stage_km"] == 30),
            "stage_60": sum(1 for c in cells if c["gated"]["stage_km"] == 60),
            "zero_within_15km": sum(1 for c in cells if c["gated"]["within_15km"] == 0),
            "zero_within_30km": sum(1 for c in cells if c["gated"]["within_30km"] == 0),
            "zero_within_60km": sum(1 for c in cells if c["gated"]["within_60km"] == 0),
        },
        "newly_direction_zero": sum(1 for c in cells if c["newly_direction_zero"]),
        "newly_final_zero": sum(1 for c in cells if c["newly_final_zero"]),
        "newly_final_zero_cells": [
            {"origin": c["origin"], "direction": c["direction"]}
            for c in cells
            if c["newly_final_zero"]
        ],
        "distance_stage_constants": {
            "stage_1_km": DISTANCE_STAGE_1_KM,
            "stage_2_km": DISTANCE_STAGE_2_KM,
            "stage_3_km": DISTANCE_STAGE_3_KM,
            "expansion_threshold": DISTANCE_STAGE_EXPANSION_THRESHOLD,
            "candidate_pool_limit": DEFAULT_CANDIDATE_POOL_LIMIT,
        },
    }

    by_origin: dict[str, dict[str, Any]] = {}
    for origin in origins:
        rows = [c for c in cells if c["origin"] == origin["name"]]
        by_origin[origin["name"]] = {
            "region": PREFECTURE_TO_REGION.get(origin["name"]),
            "baseline_final_zero_directions": sum(
                1 for r in rows if r["baseline"]["final_zero"]
            ),
            "gated_final_zero_directions": sum(
                1 for r in rows if r["gated"]["final_zero"]
            ),
            "baseline_max_within_60km": max(
                (r["baseline"]["within_60km"] for r in rows), default=0
            ),
            "gated_max_within_60km": max(
                (r["gated"]["within_60km"] for r in rows), default=0
            ),
            "newly_final_zero_directions": sum(
                1 for r in rows if r["newly_final_zero"]
            ),
        }

    return {"summary": summary, "by_origin": by_origin, "cells": cells}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", dest="json_out", default=None)
    args = parser.parse_args()

    baseline, gated, meta = load_populations()
    origins = load_prefecture_origins()

    report = {
        "meta": meta,
        "origin_corpus": {
            "source": "packages/shared/userOrigin.ts PREFECTURE_ORIGINS",
            "count": len(origins),
        },
        "concierge": concierge_report(baseline, gated),
        "compass": compass_report(baseline, gated, origins),
    }

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    c = report["concierge"]
    s = report["compass"]["summary"]
    print(f"seed rows                 : {meta['seed_rows']}")
    print(f"baseline / gated          : {meta['baseline_count']} / {meta['gated_count']}")
    print(f"unmapped goriyaku labels  : {meta['unmapped_goriyaku_labels']}")
    print(f"unresolved prefecture     : {meta['unresolved_prefecture']}")
    print(f"concierge pool (base/gate): {c['pool_baseline']} / {c['pool_gated']}")
    print(f"newly zero prefectures    : {c['newly_zero_prefectures']}")
    print(f"newly zero needs          : {c['newly_zero_needs']}")
    print(f"compass cells             : {s['cells']}")
    print(f"baseline final_zero       : {s['baseline']['final_zero']}")
    print(f"gated final_zero          : {s['gated']['final_zero']}")
    print(f"newly final_zero          : {s['newly_final_zero']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
