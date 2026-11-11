"""本番の相談の順位を、データベースに書き込まずに読むための管理コマンド。

Render の Shell から打つ。Web の画面や API からは呼べない（URL を持たない管理コマンド）。

相談の API（/api/concierge/chat/、api_views_concierge.ConciergeChatView）が中で呼ぶ関数を、
同じ順で呼ぶ:

  1. interpret_consultation（相談の読み取り）
  2. build_chat_candidates（候補を集める）
  3. filter_recommendation_eligible_candidates → _dedupe_candidates（推薦対象の判定・重複の除去）
  4. bias（緯度・経度があるときだけ。半径は API の既定と同じ 8000m）
  5. build_chat_recommendations（順位付け。OpenAI は使わない: llm_enabled=False）

API のビューが行う書き込み（無料回数の消費 consume_quota・相談の記録の保存）は、
ビューを通らないので起きない。

書き込み・外部の呼び出しが起きないようにする仕組み:

- 全体を、データベースの「読むだけの取引」（Postgres の SET TRANSACTION READ ONLY）の中で
  動かし、最後は必ず取り消す。書き込みが起きるとデータベースがエラーで止める。
- 実行した SQL を数え、読むだけの文（SELECT など）以外が0件であることを最後に表示する。
- キャッシュへの書き込みは、起きたら止める。
- Python の通信（OpenAI・Nominatim・Google などが使う道）は、起きたら止める。
  データベースの接続は、止める前に開いておく。

画面に出るのは上位3社。4位以降は、このコマンドの中だけで3社で切る処理を外して出す
（順位の付け方そのものは変えない。上位3社の並びは API と同じ）。

例:
  python manage.py inspect_concierge_ranking --query "休みたい" \\
      --lat 35.681236 --lng 139.767125 --include-no-location
"""

from __future__ import annotations

import json
import re
import socket
from collections import Counter
from contextlib import ExitStack, contextmanager
from typing import Any, Dict, Iterator, List, Optional
from unittest import mock

from django.conf import settings
from django.core.cache import caches
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from temples.models import Shrine
from temples.services import concierge_chat
from temples.services.concierge_candidate_utils import _dedupe_candidates
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_candidates import (
    build_chat_candidates,
    filter_recommendation_eligible_candidates,
)
from temples.services.concierge_chat_ranking import _resolve_public_mode
from temples.services.consultation_interpreter import interpret_consultation

# API の既定（api_views_concierge._parse_radius）と同じ。
DEFAULT_RADIUS_M = 8000
DISPLAYED_COUNT = 3
DEFAULT_TOP = 5

# 読むだけの文。SAVEPOINT などは取引の中の区切りで、データを変えない。
READ_ONLY_SQL = re.compile(
    r"^\s*(SELECT|WITH|SHOW|SET\s+TRANSACTION|SAVEPOINT|RELEASE\s+SAVEPOINT|ROLLBACK\s+TO\s+SAVEPOINT|EXPLAIN)\b",
    re.IGNORECASE,
)
CACHE_WRITE_METHODS = ("set", "add", "incr", "decr", "delete", "set_many", "delete_many", "touch", "clear", "get_or_set")


class ReadOnlyViolation(RuntimeError):
    """書き込み・外部の呼び出しが起きようとした。"""


class _Guard:
    def __init__(self) -> None:
        self.statements = 0
        self.write_statements: List[str] = []
        self.cache_writes: List[str] = []
        self.network_attempts: List[str] = []

    # --- SQL ---
    def sql_recorder(self, execute, sql, params, many, context):
        self.statements += 1
        text = sql if isinstance(sql, str) else str(sql)
        if not READ_ONLY_SQL.match(text):
            self.write_statements.append(text.strip().split("\n", 1)[0][:200])
        return execute(sql, params, many, context)

    # --- cache ---
    def cache_blocker(self, name: str):
        def _blocked(*args, **kwargs):
            self.cache_writes.append(name)
            raise ReadOnlyViolation(f"cache write blocked: {name}")

        return _blocked

    # --- network ---
    def network_blocker(self, name: str):
        def _blocked(*args, **kwargs):
            target = args[1] if len(args) > 1 else (args[0] if args else "")
            self.network_attempts.append(f"{name}:{target!r}")
            raise ReadOnlyViolation(f"network access blocked: {name} {target!r}")

        return _blocked

    @property
    def ok(self) -> bool:
        return not (self.write_statements or self.cache_writes or self.network_attempts)

    def summary(self) -> Dict[str, Any]:
        return {
            "sql_statements": self.statements,
            "non_read_sql_statements": len(self.write_statements),
            "non_read_sql_samples": self.write_statements[:5],
            "cache_write_attempts": len(self.cache_writes),
            "network_attempts": len(self.network_attempts),
            "network_samples": self.network_attempts[:5],
            "transaction": "read only, rolled back" if connection.vendor == "postgresql" else "rolled back",
        }


@contextmanager
def read_only_guard() -> Iterator[_Guard]:
    """読むだけの取引・SQL の記録・キャッシュと通信の遮断をまとめて掛ける。最後は必ず取り消す。"""
    guard = _Guard()
    connection.ensure_connection()  # 通信を止める前にデータベースの接続を開く
    with ExitStack() as stack:
        stack.enter_context(transaction.atomic())
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
        stack.enter_context(connection.execute_wrapper(guard.sql_recorder))
        cache_class = type(caches["default"])
        for method in CACHE_WRITE_METHODS:
            if hasattr(cache_class, method):
                stack.enter_context(mock.patch.object(cache_class, method, guard.cache_blocker(method)))
        stack.enter_context(mock.patch.object(socket.socket, "connect", guard.network_blocker("socket.connect")))
        stack.enter_context(mock.patch.object(socket.socket, "connect_ex", guard.network_blocker("socket.connect_ex")))
        stack.enter_context(mock.patch.object(socket, "create_connection", guard.network_blocker("create_connection")))
        stack.enter_context(mock.patch.object(socket, "getaddrinfo", guard.network_blocker("getaddrinfo")))
        try:
            yield guard
        finally:
            transaction.set_rollback(True)


def _keep_all_recommendations(recs: Dict[str, Any]) -> None:
    """3社で切る処理の代わり（並びは変えない）。このコマンドの中だけで使う。"""
    return None


def run_inspection(
    *,
    query: str,
    lat: Optional[float],
    lng: Optional[float],
    top: int = DEFAULT_TOP,
) -> Dict[str, Any]:
    """相談の API と同じ道筋で候補を集めて順位を付け、上位 top 社の内訳を返す（書き込まない）。"""
    interpretation_profile = interpret_consultation(query=query, need_tags=[], selected_goriyaku_tag_ids=[])
    raw_candidates = build_chat_candidates(
        goriyaku_tag_ids=None,
        area=None,
        lat=lat,
        lng=lng,
        trace_id="inspect_concierge_ranking",
        interpretation_profile=interpretation_profile,
    )
    candidates = _dedupe_candidates(filter_recommendation_eligible_candidates(raw_candidates))
    bias = None
    if lat is not None and lng is not None:
        bias = {"lat": lat, "lng": lng, "radius": DEFAULT_RADIUS_M, "radius_m": DEFAULT_RADIUS_M}

    with mock.patch.object(concierge_chat, "_trim_to_top3_and_fill_message", _keep_all_recommendations):
        recs = build_chat_recommendations(
            query=query,
            language="ja",
            candidates=candidates,
            bias=bias,
            birthdate=None,
            goriyaku_tag_ids=None,
            extra_condition=None,
            visit_preferences=None,
            public_mode=_resolve_public_mode(mode=None, birthdate=None, query=query),
            flow="A",
            user=None,
            profile_context=None,
            interpretation_profile=interpretation_profile,
            llm_enabled=False,
        )

    debug = recs.get("_debug") or {}
    filter_context = ((debug.get("candidate_pool_observation") or {}).get("filter_context")) or {}
    rows = []
    for rank, rec in enumerate((recs.get("recommendations") or [])[:top], start=1):
        features = (rec.get("breakdown_detail") or {}).get("features") or {}
        need = features.get("need") or {}
        visit = features.get("visit_style") or {}
        implied = features.get("implied_visit_style") or {}
        distance = features.get("distance") or {}
        popular = features.get("popular") or {}
        element = features.get("element") or {}
        behavior = features.get("behavior") or {}
        distance_m = rec.get("distance_m")
        rows.append(
            {
                "rank": rank,
                "displayed": rank <= DISPLAYED_COUNT,
                "id": rec.get("id"),
                "name": rec.get("name"),
                "distance_km": round(float(distance_m) / 1000, 1) if distance_m is not None else None,
                "primary_reason": f"{rec.get('_primary_reason_source')}:{rec.get('_primary_reason_label')}",
                "visit_style_tags": list(rec.get("visit_style_tags") or []),
                "matched_need_tags": list((rec.get("breakdown") or {}).get("matched_need_tags") or []),
                "contributions": {
                    "distance": round(float(distance.get("contribution") or 0.0), 3),
                    "need": round(float(need.get("rank_weighted_contribution") or 0.0), 3),
                    "visit_style": round(float(visit.get("contribution") or 0.0), 3),
                    "implied_visit_style": round(float(implied.get("contribution") or 0.0), 3),
                    "popular": round(float(popular.get("contribution") or 0.0), 3),
                    "element": round(float(element.get("contribution") or 0.0), 3),
                    "behavior": round(float(behavior.get("capped_contribution") or 0.0), 3),
                },
                "visit_style_matched": list(visit.get("matched_tags") or []),
                "implied_visit_style_matched": list(implied.get("matched_tags") or []),
                "popular_raw": round(float(popular.get("raw") or 0.0), 3),
                "score_total": round(float(rec.get("_score_total") or 0.0), 3),
            }
        )
    return {
        "query": query,
        "location": {"lat": lat, "lng": lng} if lat is not None and lng is not None else None,
        "need_tags": list(filter_context.get("need_tags") or []),
        "consultation_axis": filter_context.get("consultation_axis"),
        "visit_style_tags": list(filter_context.get("visit_style_tags") or []),
        "implied_visit_style_tags": list(filter_context.get("implied_visit_style_tags") or []),
        "candidate_count": len(candidates),
        "rows": rows,
    }


def dataset_overview() -> Dict[str, Any]:
    """本番のデータの様子（参拝の好みの件数・人気の点がある社数など）。"""
    visit = Counter()
    popular_nonzero = 0
    themes = 0
    total = 0
    for tags, popular, theme in Shrine.objects.values_list("visit_style_tags", "popular_score", "history_theme"):
        total += 1
        for tag in tags or []:
            visit[tag] += 1
        if popular:
            popular_nonzero += 1
        if theme:
            themes += 1
    return {
        # 本番で LLM が有効だと、相談の API は LLM が選んだ候補から順位を付ける。
        # このコマンドは外部を呼ばないため、LLM が無効（または失敗した）ときの道筋で順位を付ける。
        "concierge_use_llm": bool(getattr(settings, "CONCIERGE_USE_LLM", False)),
        "shrines": total,
        "visit_style_tag_counts": dict(visit.most_common()),
        "shrines_with_popular_score": popular_nonzero,
        "shrines_with_history_theme": themes,
    }


def _format_row(row: Dict[str, Any]) -> str:
    c = row["contributions"]
    dist = f"{row['distance_km']}km" if row["distance_km"] is not None else "-"
    mark = "" if row["displayed"] else "（画面外）"
    return (
        f"  {row['rank']}. {row['name']}{mark} 距離={dist} 主な根拠={row['primary_reason']} 合計={row['score_total']:.3f}\n"
        f"     内訳: 距離 {c['distance']:.3f} / 相談の種類 {c['need']:.3f} / "
        f"参拝の好み {c['visit_style']:.3f}{row['visit_style_matched']} / "
        f"自動で足した好み {c['implied_visit_style']:.3f}{row['implied_visit_style_matched']} / "
        f"人気 {c['popular']:.3f}（popular_raw={row['popular_raw']}） / 生年月日 {c['element']:.3f} / 行動 {c['behavior']:.3f}\n"
        f"     神社の参拝の好み={row['visit_style_tags']} 一致した相談の種類={row['matched_need_tags']}"
    )


class Command(BaseCommand):
    help = (
        "相談の API と同じ道筋で順位を付け、上位の神社と点数の内訳を出す（読むだけ。"
        "データベース・キャッシュに書き込まず、外部のサービスも呼ばない）。"
    )

    def add_arguments(self, parser):
        parser.add_argument("--query", action="append", required=True, help="相談文。繰り返し指定できる。")
        parser.add_argument("--lat", type=float, default=None, help="緯度（--lng と一緒に指定）。")
        parser.add_argument("--lng", type=float, default=None, help="経度（--lat と一緒に指定）。")
        parser.add_argument(
            "--include-no-location",
            action="store_true",
            help="緯度・経度を指定したとき、場所なしの結果も一緒に出す。",
        )
        parser.add_argument("--top", type=int, default=DEFAULT_TOP, help=f"出す社数（既定 {DEFAULT_TOP}）。")
        parser.add_argument(
            "--expect",
            default=None,
            help="比べたい上位の神社名（カンマ区切り）。最初の --query と、緯度・経度ありの結果と比べる。",
        )
        parser.add_argument("--json", action="store_true", help="結果を JSON で出す。")

    def handle(self, *args, **options):
        lat, lng = options["lat"], options["lng"]
        if (lat is None) != (lng is None):
            raise CommandError("--lat と --lng は一緒に指定してください。")
        if options["top"] < 1:
            raise CommandError("--top は1以上にしてください。")

        locations: List[tuple[Optional[float], Optional[float]]] = []
        if lat is not None:
            locations.append((lat, lng))
            if options["include_no_location"]:
                locations.append((None, None))
        else:
            locations.append((None, None))

        expect = [name.strip() for name in (options["expect"] or "").split(",") if name.strip()]

        with read_only_guard() as guard:
            overview = dataset_overview()
            results = [
                run_inspection(query=query, lat=loc_lat, lng=loc_lng, top=options["top"])
                for query in options["query"]
                for loc_lat, loc_lng in locations
            ]

        comparison = None
        if expect:
            target = next((r for r in results if r["location"] is not None), results[0])
            actual = [row["name"] for row in target["rows"]]
            comparison = {
                "query": target["query"],
                "location": target["location"],
                "expected": expect,
                "actual": actual[: len(expect)],
                "matches": [
                    {"rank": i + 1, "expected": name, "actual": actual[i] if i < len(actual) else None,
                     "same": i < len(actual) and actual[i] == name}
                    for i, name in enumerate(expect)
                ],
            }

        payload = {"overview": overview, "results": results, "comparison": comparison, "read_only": guard.summary()}

        if options["json"]:
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=1))
        else:
            self._write_text(payload)

        if not guard.ok:
            raise CommandError("書き込み・外部の呼び出しが起きようとしました（上の read_only を見てください）。")

    def _write_text(self, payload: Dict[str, Any]) -> None:
        overview = payload["overview"]
        w = self.stdout.write
        w("== 本番のデータ")
        w(f"  神社 {overview['shrines']}社 / 人気の点がある神社 {overview['shrines_with_popular_score']}社 / "
          f"歴史のテーマがある神社 {overview['shrines_with_history_theme']}社")
        w(f"  参拝の好みの件数: {overview['visit_style_tag_counts']}")
        w(f"  CONCIERGE_USE_LLM={overview['concierge_use_llm']}（このコマンドは LLM を使わない道筋で順位を付ける）")
        for result in payload["results"]:
            loc = result["location"]
            where = f"緯度 {loc['lat']}・経度 {loc['lng']}" if loc else "場所なし"
            w("")
            w(f"== 相談「{result['query']}」 / {where}")
            w(f"  相談の種類={result['need_tags']} 相談の軸={result['consultation_axis']} "
              f"相談文から拾った好み={result['visit_style_tags']} 自動で足した好み={result['implied_visit_style_tags']} "
              f"推薦対象の候補={result['candidate_count']}社")
            for row in result["rows"]:
                w(_format_row(row))
        comparison = payload["comparison"]
        if comparison:
            w("")
            w(f"== 期待との比較（相談「{comparison['query']}」）")
            for item in comparison["matches"]:
                w(f"  {item['rank']}. 期待={item['expected']} 実際={item['actual']} {'一致' if item['same'] else '不一致'}")
        ro = payload["read_only"]
        w("")
        w("== 読むだけの確認")
        w(f"  SQL {ro['sql_statements']}件のうち、読むだけでない文 {ro['non_read_sql_statements']}件 / "
          f"キャッシュへの書き込み {ro['cache_write_attempts']}件 / 外部への接続 {ro['network_attempts']}件 / "
          f"取引: {ro['transaction']}")
        for sample in ro["non_read_sql_samples"] + ro["network_samples"]:
            w(f"  - {sample}")
