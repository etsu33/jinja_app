from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connections


OUTPUT_PATH = Path("docs/analytics/consultation-axis-discovery.md")


def _safe_json(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def _join_or_unfetched(values: Any) -> str:
    if values is None:
        return "未取得"
    if not values:
        return "-"
    if isinstance(values, (list, tuple, set)):
        joined = " / ".join(str(v).strip() for v in values if str(v).strip())
        return joined or "-"
    text = str(values).strip()
    return text or "-"


def _text_or_unfetched(value: Any) -> str:
    if value is None:
        return "未取得"
    text = str(value).strip()
    return text or "-"


def _escape_cell(value: Any) -> str:
    text = str(value).replace("\n", "<br>").replace("|", "\\|").strip()
    return text or "-"


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        item = str(value).strip()
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _collect_recommendation_meta(payload: Any) -> tuple[list[str] | None, list[str] | None]:
    if payload is None:
        return None, None
    if isinstance(payload, dict):
        recommendations = payload.get("recommendations_v2") or payload.get("recommendations") or []
    elif isinstance(payload, list):
        recommendations = payload
    else:
        recommendations = []

    matched_need_tags: list[str] = []
    history_themes: list[str] = []
    for item in recommendations:
        if not isinstance(item, dict):
            continue
        breakdown = item.get("breakdown")
        if isinstance(breakdown, dict):
            tags = breakdown.get("matched_need_tags")
            if isinstance(tags, list):
                matched_need_tags.extend(str(tag) for tag in tags)
        explanation_payload = item.get("_explanation_payload")
        if isinstance(explanation_payload, dict):
            tags = explanation_payload.get("matched_need_tags")
            if isinstance(tags, list):
                matched_need_tags.extend(str(tag) for tag in tags)
            history_context = explanation_payload.get("history_context")
            if isinstance(history_context, dict) and history_context.get("theme"):
                history_themes.append(str(history_context["theme"]))
        if item.get("history_theme"):
            history_themes.append(str(item["history_theme"]))

    return _unique(matched_need_tags), _unique(history_themes)


class Command(BaseCommand):
    help = "Export a privacy-minimized consultation text audit dataset for consultation_axis discovery."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--output", default=str(OUTPUT_PATH))
        parser.add_argument("--database", default="default")

    def handle(self, *args, **options):
        limit = max(1, int(options["limit"]))
        output_path = Path(options["output"])
        using = str(options["database"])
        connection = connections[using]

        tables = set(connection.introspection.table_names())
        has_messages = "temples_conciergemessage" in tables
        has_threads = "temples_conciergethread" in tables
        has_reco_logs = "temples_concierge_recommendation_log" in tables

        thread_columns = set(self._columns(connection, "temples_conciergethread")) if has_threads else set()
        message_columns = set(self._columns(connection, "temples_conciergemessage")) if has_messages else set()
        reco_columns = (
            set(self._columns(connection, "temples_concierge_recommendation_log"))
            if has_reco_logs
            else set()
        )

        rows: list[dict[str, Any]] = []
        if has_messages and has_threads and {"role", "content", "created_at", "thread_id"}.issubset(message_columns):
            rows = self._fetch_rows(
                connection=connection,
                limit=limit,
                thread_columns=thread_columns,
                reco_columns=reco_columns,
                has_reco_logs=has_reco_logs,
            )

        markdown = self._build_markdown(
            limit=limit,
            using=using,
            rows=rows,
            has_messages=has_messages,
            has_threads=has_threads,
            has_reco_logs=has_reco_logs,
            thread_columns=thread_columns,
            reco_columns=reco_columns,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"exported {len(rows)} consultations to {output_path}"))

    def _columns(self, connection, table_name: str) -> list[str]:
        with connection.cursor() as cursor:
            description = connection.introspection.get_table_description(cursor, table_name)
        return [column.name for column in description]

    def _fetch_rows(
        self,
        *,
        connection,
        limit: int,
        thread_columns: set[str],
        reco_columns: set[str],
        has_reco_logs: bool,
    ) -> list[dict[str, Any]]:
        thread_selects = []
        for column in ("recommendations_v2", "recommendations", "tags"):
            if column in thread_columns:
                thread_selects.append(f't."{column}" AS thread_{column}')
            else:
                thread_selects.append(f"NULL AS thread_{column}")

        sql = f"""
            SELECT
                m.content,
                m.created_at,
                m.thread_id,
                {", ".join(thread_selects)}
            FROM temples_conciergemessage m
            JOIN temples_conciergethread t ON t.id = m.thread_id
            WHERE m.role = %s
            ORDER BY m.created_at DESC, m.id DESC
            LIMIT %s
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, ["user", limit])
            columns = [col[0] for col in cursor.description]
            raw_rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        logs_by_thread = self._fetch_recommendation_logs(
            connection=connection,
            thread_ids=[row["thread_id"] for row in raw_rows],
            reco_columns=reco_columns,
            has_reco_logs=has_reco_logs,
        )

        rows: list[dict[str, Any]] = []
        for row in raw_rows:
            log = logs_by_thread.get(row["thread_id"])
            need_tags = None
            if log is not None:
                need_tags = _safe_json(log.get("need_tags")) or []
            elif row.get("thread_tags") is not None:
                need_tags = _safe_json(row.get("thread_tags")) or []

            recommendation_payload = _safe_json(row.get("thread_recommendations_v2"))
            if recommendation_payload is None:
                recommendation_payload = _safe_json(row.get("thread_recommendations"))
            matched_need_tags, history_themes = _collect_recommendation_meta(recommendation_payload)

            rows.append(
                {
                    "content": row.get("content"),
                    "need_tags": need_tags,
                    "matched_need_tags": matched_need_tags,
                    "history_theme": history_themes,
                }
            )
        return rows

    def _fetch_recommendation_logs(
        self,
        *,
        connection,
        thread_ids: list[int],
        reco_columns: set[str],
        has_reco_logs: bool,
    ) -> dict[int, dict[str, Any]]:
        if not has_reco_logs or not thread_ids or not {"thread_id", "need_tags", "created_at"}.issubset(reco_columns):
            return {}

        placeholders = ", ".join(["%s"] * len(thread_ids))
        sql = f"""
            SELECT thread_id, need_tags, created_at
            FROM temples_concierge_recommendation_log
            WHERE thread_id IN ({placeholders})
            ORDER BY created_at DESC, id DESC
        """
        out: dict[int, dict[str, Any]] = {}
        with connection.cursor() as cursor:
            cursor.execute(sql, thread_ids)
            columns = [col[0] for col in cursor.description]
            for raw in cursor.fetchall():
                row = dict(zip(columns, raw))
                thread_id = row.get("thread_id")
                if thread_id is not None and thread_id not in out:
                    out[int(thread_id)] = row
        return out

    def _build_markdown(
        self,
        *,
        limit: int,
        using: str,
        rows: list[dict[str, Any]],
        has_messages: bool,
        has_threads: bool,
        has_reco_logs: bool,
        thread_columns: set[str],
        reco_columns: set[str],
    ) -> str:
        lines = [
            "# Consultation Axis Discovery",
            "",
            "## 目的",
            "",
            "直近100件の相談ログから user role の相談文のみを抽出し、今後 `consultation_axis` 候補を発見するための監査用データセットを作る。",
            "",
            "このドキュメントでは taxonomy は確定しない。LLMクラスタ分析の実API実行も行わない。",
            "",
            "## 取得元",
            "",
            "- 主取得元: `temples_conciergemessage` / `temples_conciergethread`",
            "- 相談文: `ConciergeMessage.role = user` の `content`",
            "- `need_tags`: `temples_concierge_recommendation_log.need_tags` を優先。未取得時は `ConciergeThread.tags` を補助参照。",
            "- `matched_need_tags`: `ConciergeThread.recommendations_v2` または `recommendations` 内の `breakdown.matched_need_tags` / `_explanation_payload.matched_need_tags`",
            "- `history_theme`: `ConciergeThread.recommendations_v2` または `recommendations` 内の `history_theme` / `_explanation_payload.history_context.theme`",
            f"- 実行DB alias: `{using}`（実データDBの環境変数で実行する。SQLite固定ではない）",
            f"- 抽出上限: `{limit}`",
            "",
            "## 抽出条件",
            "",
            "- user role の発話のみを抽出する。",
            "- 新しい順に `created_at DESC, id DESC` で最大100件を対象にする。",
            "- docsにはユーザーID、anonymous_id、thread_id、message_id、メールアドレス等の識別情報を出さない。",
            "- 取得できない項目は `未取得` と記録する。",
            "- DBスキーマ、migration、recommendation score 実装は変更しない。",
            "",
            "## 取得状況",
            "",
            f"- `temples_conciergemessage`: `{ 'あり' if has_messages else '未取得' }`",
            f"- `temples_conciergethread`: `{ 'あり' if has_threads else '未取得' }`",
            f"- `temples_concierge_recommendation_log`: `{ 'あり' if has_reco_logs else '未取得' }`",
            f"- `ConciergeThread.recommendations_v2`: `{ 'あり' if 'recommendations_v2' in thread_columns else '未取得' }`",
            f"- `ConciergeThread.recommendations`: `{ 'あり' if 'recommendations' in thread_columns else '未取得' }`",
            f"- `ConciergeRecommendationLog.need_tags`: `{ 'あり' if 'need_tags' in reco_columns else '未取得' }`",
            f"- 抽出件数: `{len(rows)}`",
            "",
            "## 直近相談ログ一覧",
            "",
        ]

        if rows:
            lines.extend(
                [
                    "| # | 相談文 | need_tags | matched_need_tags | history_theme |",
                    "|---:|---|---|---|---|",
                ]
            )
            for index, row in enumerate(rows, start=1):
                lines.append(
                    "| "
                    f"{index} | "
                    f"{_escape_cell(_text_or_unfetched(row.get('content')))} | "
                    f"{_escape_cell(_join_or_unfetched(row.get('need_tags')))} | "
                    f"{_escape_cell(_join_or_unfetched(row.get('matched_need_tags')))} | "
                    f"{_escape_cell(_join_or_unfetched(row.get('history_theme')))} |"
                )
        else:
            lines.extend(
                [
                    "実データDBで再生成するまでは未取得。",
                    "",
                    "| # | 相談文 | need_tags | matched_need_tags | history_theme |",
                    "|---:|---|---|---|---|",
                    "| - | 未取得 | 未取得 | 未取得 | 未取得 |",
                ]
            )

        lines.extend(
            [
                "",
                "## consultation_axis候補欄",
                "",
                "LLMクラスタ分析前のため未確定。現時点では候補を固定せず、下記の観点で後続分析する。",
                "",
                "| candidate | 根拠相談文 | 関連need_tags | 備考 |",
                "|---|---|---|---|",
                "| 未確定 | 未取得 | 未取得 | LLMクラスタ分析後に記入 |",
                "",
                "## 次にLLMクラスタ分析で見る観点",
                "",
                "- 相談文が表す主目的: 仕事、金運、恋愛、人間関係、学業、健康、厄除け、移動安全など。",
                "- 感情状態: 不安、疲労、迷い、背中を押してほしい、落ち着きたいなど。",
                "- 時間軸: 今すぐの解決、節目、再出発、継続的な改善。",
                "- 行動意図: 参拝先探し、気持ちの整理、意思決定、守り・浄化、縁づくり。",
                "- 既存 `need_tags` と相談文のズレ: タグ化できていない自然文のまとまり。",
                "- `history_theme` との混同リスク: 神社側の文脈タグとユーザー相談軸を分離できるか。",
                "",
                "## 再生成コマンド",
                "",
                "```bash",
                "cd backend && ../.venv/bin/python manage.py export_consultation_axis_discovery --limit 100 --output ../docs/analytics/consultation-axis-discovery.md",
                "```",
                "",
            ]
        )
        return "\n".join(lines)
