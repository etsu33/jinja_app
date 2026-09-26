"""Compass runtime の実DB query数を計測する（measurement / audit 専用）。

目的:
    Compass の1 action が実際に何本の SQL を発行するかを、実ORM実行から
    ``django.test.utils.CaptureQueriesContext`` で記録する。
    結果の読み方と分類は ``docs/audit/compass-db-query-budget.md`` を正本とする。

このfileを既存の API contract test と分けた理由:
    ``test_compass_recommendations_api.py`` / ``test_compass_weekly_api.py`` は
    HTTP契約（state / shape / snapshot semantics）の正本であり、Monthly と
    Weekly を横断する「query数の計測」と「Compass 1 action 合算」を片方へ
    入れると、どちらの file の責務にも収まらない。fixture と request helper は
    既存 file から import して再利用し、計測経路は既存 test と同じにする。

計測の規約:
    - fixture / setup の query（Shrine作成・User作成・事前のMISS request）は
      すべて ``CaptureQueriesContext`` の外で行う。
    - Recommendation pipeline / Shrine query / Knowledge selector /
      Snapshot lookup / hydration は mock しない。
    - Weekly の「今日」は既存 test と同じく ``timezone.localdate`` を固定する
      （``_post_on``）。これは時刻の固定であり、DB経路には影響しない。
    - LLM は無効（Compass は ``llm_enabled=False`` 固定）。外部HTTPは
      ``http_mock`` 上で 0 回であることを assert する。

exact な query数の assert（regression budget）はここでは置かない。
計測済みの baseline とその根拠は audit 文書に記録し、budget を pin するかは
audit 文書の Mother Ship decision point で判断する。ここで assert するのは、
計測そのものが正しいこと（HIT/MISS の区別、setup除外、外部HTTP 0、
候補件数に比例しないこと）だけである。
"""

from __future__ import annotations

import json
import os
import re
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from temples.models_weekly_presentation import WeeklyPresentationSnapshot
from temples.tests.api.test_compass_recommendations_api import (
    BIRTHDATE as MONTHLY_BIRTHDATE,
)
from temples.tests.api.test_compass_recommendations_api import (
    ORIGIN as MONTHLY_ORIGIN,
)
from temples.tests.api.test_compass_recommendations_api import TARGET_DATE
from temples.tests.api.test_compass_recommendations_api import URL as MONTHLY_URL
from temples.tests.api.test_compass_weekly_api import (  # noqa: F401  (fixtures)
    REFERENCE_DATE,
    _jwt_client,
    _post_on,
    northwest_shrines,
    shrine_factory,
)

pytestmark = pytest.mark.django_db

SNAPSHOT_TABLE = WeeklyPresentationSnapshot._meta.db_table

# 計測結果を JSON で書き出す先（任意）。audit 文書の数値はこの出力から転記する。
REPORT_ENV = "COMPASS_QUERY_AUDIT_REPORT"
# report に残す SQL の長さ（既定は先頭のみ。全文が要る時は環境変数で広げる）
SQL_PREVIEW_CHARS = int(os.getenv("COMPASS_QUERY_AUDIT_SQL_CHARS", "240"))

_BACKEND_ROOT = Path(__file__).resolve().parents[3]

# category: その query が「何を」取りに行くか。
# 最も内側の app frame（呼び出し元 module）で決める。上から順に評価する。
_ORIGIN_CATEGORY: list[tuple[str, str]] = [
    ("temples/services/shrine_knowledge_selector", "knowledge retrieval"),
    ("temples/services/recommendation_eligibility", "candidate retrieval"),
    ("temples/services/concierge_chat_candidates", "candidate retrieval"),
    # Recommendation 組み立て（理由文の goriyaku tag label 解決）。
    # 指定の6分類のどれにも当たらないため、独立した分類として記録する。
    ("temples/services/concierge_chat", "recommendation build"),
    ("temples/services/weekly_presentation_snapshot", "snapshot"),
    ("temples/services/weekly_featured_shrines", "hydration"),
    ("temples/services/billing", "billing"),
    ("temples/services/entitlements", "billing"),
    ("temples/services/quota", "billing"),
    ("rest_framework_simplejwt", "auth"),
    ("temples/services/anonymous_id", "auth"),
]

# stage: その query が pipeline のどの段階で出たか（stack 全体で判定）。
# 同じ knowledge selector の query でも、Recommendation 実行中か
# Weekly featured の hydration 中かを区別するために使う。
_STAGE_MARKERS: list[tuple[str, str]] = [
    ("temples/services/weekly_featured_shrines", "hydration"),
    ("temples/services/compass_recommendation_orchestrator", "recommendation"),
    ("temples/services/weekly_presentation_snapshot", "snapshot"),
    ("rest_framework_simplejwt", "auth"),
]


@dataclass
class CapturedQuery:
    sql: str
    operation: str
    table: str
    origin: str
    category: str
    stage: str
    also_touches: list[str] = field(default_factory=list)


@dataclass
class Measurement:
    label: str
    status_code: int
    state: str = ""
    direction_candidate_count: int | None = None
    distance_candidate_count: int | None = None
    returned_count: int | None = None
    queries: list[CapturedQuery] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.queries)

    def by(self, attr: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for q in self.queries:
            key = getattr(q, attr)
            out[key] = out.get(key, 0) + 1
        return dict(sorted(out.items()))

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "status_code": self.status_code,
            "state": self.state,
            "direction_candidate_count": self.direction_candidate_count,
            "distance_candidate_count": self.distance_candidate_count,
            "returned_count": self.returned_count,
            "count": self.count,
            "by_operation": self.by("operation"),
            "by_table": self.by("table"),
            "by_category": self.by("category"),
            "by_stage": self.by("stage"),
            "queries": [
                {
                    "operation": q.operation,
                    "table": q.table,
                    "category": q.category,
                    "stage": q.stage,
                    "also_touches": q.also_touches,
                    "origin": q.origin,
                    "sql": q.sql[:SQL_PREVIEW_CHARS],
                }
                for q in self.queries
            ],
        }


_TABLE_RE = re.compile(r'\b(FROM|INTO|UPDATE|JOIN)\s+"?([A-Za-z0-9_]+)"?', re.IGNORECASE)


def _tables_by_depth(sql: str) -> list[tuple[int, str, str]]:
    """(括弧の深さ, keyword, table) の一覧。SELECT句内の subquery を区別するため。"""
    depths = []
    depth = 0
    for ch in sql:
        depths.append(depth)
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
    return [(depths[m.start()], m.group(1).upper(), m.group(2)) for m in _TABLE_RE.finditer(sql)]


_TRANSACTION_CONTROL = {"BEGIN", "COMMIT", "ROLLBACK"}


def _operation(sql: str) -> str:
    head = sql.lstrip().split(None, 1)
    return head[0].upper() if head else "?"


def _primary_table(sql: str) -> str:
    """最上位（括弧の外）の FROM / INTO / UPDATE 対象。"""
    for depth, keyword, table in _tables_by_depth(sql):
        if depth == 0 and keyword != "JOIN":
            return table
    return "-"


def _secondary_tables(sql: str, primary: str) -> list[str]:
    """JOIN / subquery で同じ query に含まれる他の table（別 query ではない）。"""
    seen: list[str] = []
    for _depth, _keyword, table in _tables_by_depth(sql):
        if table != primary and table not in seen:
            seen.append(table)
    return seen


def _origin_frame(stack: list[traceback.FrameSummary]) -> str:
    """ORM/driver を除いた、最も内側の app code frame（file:function）。"""
    for frame in reversed(stack):
        path = frame.filename.replace(os.sep, "/")
        if "/site-packages/" in path:
            if "rest_framework_simplejwt" in path:
                return "rest_framework_simplejwt:" + frame.name
            continue
        if "/tests/" in path or path.endswith("/test_compass_db_query_budget.py"):
            continue
        try:
            rel = Path(frame.filename).resolve().relative_to(_BACKEND_ROOT)
        except ValueError:
            continue
        return f"{rel.as_posix().removesuffix('.py')}:{frame.name}"
    return "-"


def _stage(stack: list[traceback.FrameSummary]) -> str:
    paths = [f.filename.replace(os.sep, "/") for f in stack]
    for marker, stage in _STAGE_MARKERS:
        if any(marker in path for path in paths):
            return stage
    return "request"


def _category(origin: str, table: str) -> str:
    for prefix, category in _ORIGIN_CATEGORY:
        if origin.startswith(prefix):
            return category
    if table in {"users_user", "auth_user"} or table.startswith("token_blacklist"):
        return "auth"
    return "other"


def _measure(label: str, request: Callable[[], object]) -> Measurement:
    """``request`` 実行中の SQL だけを記録する（setup は呼び出し前に済ませる）。"""
    stacks: list[list[traceback.FrameSummary]] = []

    def _record_stack(execute, sql, params, many, context):
        stacks.append(traceback.extract_stack())
        return execute(sql, params, many, context)

    with CaptureQueriesContext(connection) as ctx, connection.execute_wrapper(_record_stack):
        response = request()

    captured = ctx.captured_queries
    # Django 4.2+ は transaction 管理（BEGIN / COMMIT / ROLLBACK）を cursor を
    # 通さずに query log へ記録するため、execute_wrapper には現れない。
    # それ以外の entry は execute_wrapper と1対1で対応する。
    executed = [e for e in captured if e["sql"].strip().upper() not in _TRANSACTION_CONTROL]
    assert len(stacks) == len(executed), (len(stacks), len(executed), len(captured))
    stack_iter = iter(stacks)

    measurement = Measurement(label=label, status_code=getattr(response, "status_code", 0))
    try:
        body = response.json()
    except Exception:  # noqa: BLE001 - 計測補助のため本文が読めなくても続行する
        body = {}
    measurement.state = str(body.get("state", ""))
    measurement.direction_candidate_count = body.get("direction_candidate_count")
    measurement.distance_candidate_count = body.get("distance_candidate_count")
    items = body.get("recommendations", body.get("featured_shrines"))
    measurement.returned_count = len(items) if isinstance(items, list) else None
    for entry in captured:
        sql = entry["sql"]
        if sql.strip().upper() in _TRANSACTION_CONTROL:
            measurement.queries.append(
                CapturedQuery(
                    sql=sql,
                    operation=sql.strip().upper(),
                    table="-",
                    origin="django.db.transaction",
                    category="transaction control",
                    stage="transaction",
                )
            )
            continue
        stack = next(stack_iter)
        table = _primary_table(sql)
        origin = _origin_frame(stack)
        measurement.queries.append(
            CapturedQuery(
                sql=sql,
                operation=_operation(sql),
                table=table,
                origin=origin,
                category=_category(origin, table),
                stage=_stage(stack),
                also_touches=_secondary_tables(sql, table),
            )
        )
    return measurement


def _write_report(measurements: list[Measurement], extra: dict | None = None) -> None:
    path = os.getenv(REPORT_ENV)
    if not path:
        return
    report_path = Path(path)
    existing = json.loads(report_path.read_text()) if report_path.exists() else {}
    for m in measurements:
        existing[m.label] = m.as_dict()
    if extra:
        existing.update(extra)
    report_path.write_text(json.dumps(existing, ensure_ascii=False, indent=1))


def _monthly(client):
    payload = {
        "purpose": "career",
        "origin": MONTHLY_ORIGIN,
        "birthdate": MONTHLY_BIRTHDATE,
        "target_date": TARGET_DATE,
    }
    return client.post(MONTHLY_URL, data=json.dumps(payload), content_type="application/json")


@pytest.fixture
def authenticated_client(django_user_model):
    user = django_user_model.objects.create_user(username="compass_query_budget_user", password="x")
    return user, _jwt_client(user)


# --------------------------------------------------------------------------
# Monthly recommendation_success
# --------------------------------------------------------------------------


def test_monthly_recommendation_success_query_count(
    client, authenticated_client, northwest_shrines, http_mock  # noqa: F811
):
    _user, api_client = authenticated_client

    anonymous = _measure("monthly_anonymous", lambda: _monthly(client))
    authenticated = _measure("monthly_authenticated", lambda: _monthly(api_client))

    for m in (anonymous, authenticated):
        assert m.status_code == 200
        assert m.state == "recommendation_success"
        assert m.count > 0
        # Monthly は読み取りのみ（Snapshot 等の書き込みを行わない）
        assert set(m.by("operation")) == {"SELECT"}, m.by("operation")
    # 同一 request の anonymous / authenticated 差分は auth だけで説明できる
    assert anonymous.by("category").get("auth", 0) == 0
    non_auth = {k: v for k, v in authenticated.by("category").items() if k != "auth"}
    assert non_auth == anonymous.by("category")
    assert len(http_mock.calls) == 0

    _write_report([anonymous, authenticated])


# --------------------------------------------------------------------------
# Weekly Snapshot MISS / HIT
# --------------------------------------------------------------------------


def _weekly_miss_then_hit(label_prefix: str, client) -> tuple[Measurement, Measurement]:
    assert WeeklyPresentationSnapshot.objects.count() == 0
    miss = _measure(f"{label_prefix}_miss", lambda: _post_on(client, REFERENCE_DATE))
    assert WeeklyPresentationSnapshot.objects.count() == 1
    hit = _measure(f"{label_prefix}_hit", lambda: _post_on(client, REFERENCE_DATE))
    assert WeeklyPresentationSnapshot.objects.count() == 1
    return miss, hit


def _assert_miss_hit_are_distinct(miss: Measurement, hit: Measurement) -> None:
    assert miss.status_code == hit.status_code == 200
    # MISS は Snapshot を確定させる（INSERT がある）。HIT は書き込まない。
    assert any(q.operation == "INSERT" and q.table == SNAPSHOT_TABLE for q in miss.queries), [
        (q.operation, q.table) for q in miss.queries
    ]
    assert set(hit.by("operation")) == {"SELECT"}, hit.by("operation")
    # HIT は Recommendation を実行しない（recommendation stage の query がない）。
    # HIT の knowledge query は featured hydration からだけ出る。
    assert hit.by("stage").get("recommendation", 0) == 0
    assert hit.by("category").get("candidate retrieval", 0) == 0
    assert miss.by("stage").get("recommendation", 0) > 0
    assert miss.by("category").get("candidate retrieval", 0) > 0


def test_weekly_anonymous_snapshot_miss_and_hit_query_count(
    client, northwest_shrines, http_mock  # noqa: F811
):
    miss, hit = _weekly_miss_then_hit("weekly_anonymous", client)

    _assert_miss_hit_are_distinct(miss, hit)
    for m in (miss, hit):
        assert m.by("category").get("auth", 0) == 0
    assert len(http_mock.calls) == 0

    _write_report([miss, hit])


def test_weekly_authenticated_snapshot_miss_and_hit_query_count(
    authenticated_client, northwest_shrines, http_mock  # noqa: F811
):
    user, api_client = authenticated_client

    miss, hit = _weekly_miss_then_hit("weekly_authenticated", api_client)

    _assert_miss_hit_are_distinct(miss, hit)
    for m in (miss, hit):
        assert m.by("category").get("auth", 0) > 0
    assert WeeklyPresentationSnapshot.objects.get().user_id == user.id
    assert len(http_mock.calls) == 0

    _write_report([miss, hit])


# --------------------------------------------------------------------------
# N+1: 候補件数を増やしても query 数が変わらないこと
# --------------------------------------------------------------------------

# Compass は candidate_pool_limit=60 を渡し、候補SQLは
# LIMIT max(60 * 5, 50) = 300 になる（concierge_chat_candidates の pool_limit）。
# その上限を超える件数まで増やし、上限の前後で query 数が変わらないことを見る。
N_PLUS_ONE_SIZES = (1, 5, 20, 75, 310)


def _add_northwest_shrines(factory, start: int, stop: int) -> None:
    """origin (35.0, 135.0) から北西・約25km以内に一直線に並べる（setup専用）。"""
    for index in range(start, stop):
        factory(
            name=f"北西の計測神社{index}",
            latitude=35.02 + index * 0.0005,
            longitude=134.98 - index * 0.0006,
        )


def _max_in_list_size(measurement: Measurement) -> int:
    """knowledge retrieval の IN (...) に載った id 数の最大値（行数の目安）。"""
    sizes = [0]
    for q in measurement.queries:
        if q.category != "knowledge retrieval":
            continue
        for match in re.finditer(r"IN \(([0-9, ]+)\)", q.sql):
            sizes.append(len(match.group(1).split(",")))
    return max(sizes)


def test_query_count_does_not_scale_with_candidate_count(
    client, shrine_factory, http_mock  # noqa: F811
):
    series: list[tuple[int, Measurement, Measurement, Measurement]] = []
    created = 0
    for size in N_PLUS_ONE_SIZES:
        # --- setup（計測外）: Shrine を追加し、前回の Snapshot を消して MISS を作る ---
        _add_northwest_shrines(shrine_factory, created, size)
        created = size
        WeeklyPresentationSnapshot.objects.all().delete()

        monthly = _measure(f"n_plus_one_monthly_{size}", lambda: _monthly(client))
        weekly_miss = _measure(
            f"n_plus_one_weekly_miss_{size}", lambda: _post_on(client, REFERENCE_DATE)
        )
        weekly_hit = _measure(
            f"n_plus_one_weekly_hit_{size}", lambda: _post_on(client, REFERENCE_DATE)
        )
        series.append((size, monthly, weekly_miss, weekly_hit))

    for _size, monthly, weekly_miss, weekly_hit in series:
        assert monthly.state == "recommendation_success"
        assert weekly_miss.state == weekly_hit.state == "weekly_success"

    # 候補件数は実際に増えている（計測が「同じ小さな集合」を見ていないことの確認）
    direction_counts = [m.direction_candidate_count for _s, m, _mi, _h in series]
    assert direction_counts == sorted(direction_counts)
    assert direction_counts[0] < direction_counts[-1], direction_counts

    # query 数は候補件数に依存しない（N+1 がない）
    for path_index, path in enumerate(("monthly", "weekly_miss", "weekly_hit"), start=1):
        counts = {row[0]: row[path_index].count for row in series}
        assert len(set(counts.values())) == 1, (path, counts)
    assert len(http_mock.calls) == 0

    _write_report(
        [m for _s, *ms in series for m in ms],
        extra={
            "n_plus_one_series": [
                {
                    "shrines": size,
                    "direction_candidate_count": monthly.direction_candidate_count,
                    "distance_candidate_count": monthly.distance_candidate_count,
                    "monthly_returned": monthly.returned_count,
                    "weekly_featured": weekly_miss.returned_count,
                    "monthly": monthly.count,
                    "weekly_miss": weekly_miss.count,
                    "weekly_hit": weekly_hit.count,
                    "knowledge_in_list_size": _max_in_list_size(monthly),
                }
                for size, monthly, weekly_miss, weekly_hit in series
            ]
        },
    )


# --------------------------------------------------------------------------
# 本番相当のtransaction境界での Weekly MISS
# --------------------------------------------------------------------------
#
# 通常の django_db test は test 全体を1つの transaction に包むため、
# get_or_create_weekly_snapshot() の transaction.atomic() は SAVEPOINT /
# RELEASE として記録される。本番（ATOMIC_REQUESTS 未設定・autocommit）では
# この atomic が最上位になり、Django の query log に SAVEPOINT は出ない。
# その差を実測で分けるため、transaction=True（autocommit）で同じ経路を測る。


@pytest.mark.django_db(transaction=True)
def test_weekly_anonymous_snapshot_miss_under_autocommit(
    client, northwest_shrines, http_mock  # noqa: F811
):
    miss, hit = _weekly_miss_then_hit("weekly_anonymous_autocommit", client)

    _assert_miss_hit_are_distinct(miss, hit)
    assert "SAVEPOINT" not in miss.by("operation"), miss.by("operation")
    assert len(http_mock.calls) == 0

    _write_report([miss, hit])
