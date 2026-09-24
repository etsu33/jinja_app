from __future__ import annotations

from typing import Any, Dict, List, Optional

from temples.domain.shrine_identity import resolve_shrine_id, resolve_shrine_identity
from temples.services.concierge_candidate_utils import _normalize_candidate_fields


def _seed_recs_from_candidates(
    candidates: Optional[List[Dict[str, Any]]],
    size: int = 12,
) -> Dict[str, Any]:
    safe_candidates = [
        _normalize_candidate_fields(c)
        for c in (candidates or [])
        if isinstance(c, dict)
    ]
    return {
        "recommendations": safe_candidates[:size],
        "_seed": True,
    }


def _ensure_pool_size(
    recs: Dict[str, Any],
    *,
    candidates: List[Dict[str, Any]],
    size: int = 12,
) -> Dict[str, Any]:
    # F-5B #2 #3: identity は **正規化前の raw mapping** から解決する。
    # _normalize_candidate_fields() は shrine_id / id を _to_int_or_none() で
    # 潰すため、先に normalize すると malformed な identity 情報（"bad" や
    # 1.5 が None になる）が消え、invalid を absent と誤認してしまう。
    #
    #   raw -> identity 解決
    #   raw -> presentation / candidate field の正規化（別々に行う）
    raw_current = [r for r in (recs.get("recommendations") or []) if isinstance(r, dict)]
    raw_candidates = [c for c in candidates if isinstance(c, dict)]

    current: List[Dict[str, Any]] = [_normalize_candidate_fields(r) for r in raw_current]

    seen_ids = set()
    seen_names = set()

    # current は raw_current から 1:1 で作られるため長さは必ず一致する。
    for raw_row, row in zip(raw_current, current, strict=True):
        rid = resolve_shrine_id(raw_row, policy="live_candidate")
        if rid is not None:
            seen_ids.add(rid)

        name = str(row.get("name") or "").strip()
        if name:
            seen_names.add(name)

    for raw_cand in raw_candidates:
        if len(current) >= size:
            break

        cand = _normalize_candidate_fields(raw_cand)
        cid = resolve_shrine_id(raw_cand, policy="live_candidate")
        cname = str(cand.get("name") or "").strip()

        if cid is not None and cid in seen_ids:
            continue
        # name による重複排除は identity とは独立した既存の pool 規則であり、
        # F-5B では変更しない。
        if cname and cname in seen_names:
            continue

        # identity が解決できないだけの行を落とすことはしない。本 task は
        # identity の使い方を厳格にするものであり、新しい候補除外規則を
        # 導入するものではない。
        current.append(cand)

        if cid is not None:
            seen_ids.add(cid)
        if cname:
            seen_names.add(cname)

    out = dict(recs)
    out["recommendations"] = current
    return out


def _merge_candidate_fields(
    recs: Dict[str, Any],
    *,
    candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    # F-5B #4 #5: identity は raw mapping から解決する（#2 #3 と同じ理由）。
    raw_candidates = [c for c in candidates if isinstance(c, dict)]

    by_id: Dict[int, Dict[str, Any]] = {}
    by_name: Dict[str, Dict[str, Any]] = {}

    for raw_cand in raw_candidates:
        c = _normalize_candidate_fields(raw_cand)

        # invalid / conflict な identity は Shrine-id key にしない。
        cid = resolve_shrine_id(raw_cand, policy="live_candidate")
        if cid is not None:
            by_id[cid] = c

        # name は identity-absent 経路のために従来どおり保持する。
        name = str(c.get("name") or "").strip()
        if name:
            by_name[name] = c

    merged: List[Dict[str, Any]] = []

    for r in recs.get("recommendations") or []:
        if not isinstance(r, dict):
            continue

        row_input = _normalize_candidate_fields(r)
        base = None

        # F-3.1 detailHref の backend 版。identity が主張されているのに
        # 使えない場合（invalid / conflict）は name 突合へ落とさない。
        #
        #   resolved -> Shrine id で lookup。一致が無くても name へ落とさない
        #   absent   -> 既存の name fallback を使ってよい
        #   invalid  -> name fallback を使わない
        #   conflict -> name fallback を使わない
        identity = resolve_shrine_identity(r, policy="live_candidate")

        if identity.status == "resolved":
            base = by_id.get(identity.shrine_id)
        elif identity.status == "absent":
            name = str(row_input.get("name") or "").strip()
            if name:
                base = by_name.get(name)

        if base is not None:
            row = dict(base)
            for k, v in row_input.items():
                if v is not None:
                    row[k] = v
            merged.append(row)
        else:
            merged.append(row_input)

    out = dict(recs)
    out["recommendations"] = merged
    return out
