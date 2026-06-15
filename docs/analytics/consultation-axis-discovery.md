# Consultation Axis Discovery

## 目的

直近100件の相談ログから user role の相談文のみを抽出し、今後 `consultation_axis` 候補を発見するための監査用データセットを作る。

このドキュメントでは taxonomy は確定しない。LLMクラスタ分析の実API実行も行わない。

## 取得元

- 主取得元: `temples_conciergemessage` / `temples_conciergethread`
- 相談文: `ConciergeMessage.role = user` の `content`
- `need_tags`: `temples_concierge_recommendation_log.need_tags` を優先。未取得時は `ConciergeThread.tags` を補助参照。
- `matched_need_tags`: `ConciergeThread.recommendations_v2` または `recommendations` 内の `breakdown.matched_need_tags` / `_explanation_payload.matched_need_tags`
- `history_theme`: `ConciergeThread.recommendations_v2` または `recommendations` 内の `history_theme` / `_explanation_payload.history_context.theme`
- 実行DB alias: `default`（実データDBの環境変数で実行する。SQLite固定ではない）
- 抽出上限: `100`

## 抽出条件

- user role の発話のみを抽出する。
- 新しい順に `created_at DESC, id DESC` で最大100件を対象にする。
- docsにはユーザーID、anonymous_id、thread_id、message_id、メールアドレス等の識別情報を出さない。
- 取得できない項目は `未取得` と記録する。
- DBスキーマ、migration、recommendation score 実装は変更しない。

## 取得状況

- `temples_conciergemessage`: `未確認`
- `temples_conciergethread`: `未確認`
- `temples_concierge_recommendation_log`: `未確認`
- `ConciergeThread.recommendations_v2`: `未確認`
- `ConciergeThread.recommendations`: `未確認`
- `ConciergeRecommendationLog.need_tags`: `未確認`
- 抽出件数: `未取得`
- 備考: ローカルSQLiteではなく、実データDBに接続した環境で再生成する。

## 直近相談ログ一覧

実データDBで再生成するまでは未取得。

| # | 相談文 | need_tags | matched_need_tags | history_theme |
|---:|---|---|---|---|
| - | 未取得 | 未取得 | 未取得 | 未取得 |

## consultation_axis候補欄

LLMクラスタ分析前のため未確定。現時点では候補を固定せず、下記の観点で後続分析する。

| candidate | 根拠相談文 | 関連need_tags | 備考 |
|---|---|---|---|
| 未確定 | 未取得 | 未取得 | LLMクラスタ分析後に記入 |

## 次にLLMクラスタ分析で見る観点

- 相談文が表す主目的: 仕事、金運、恋愛、人間関係、学業、健康、厄除け、移動安全など。
- 感情状態: 不安、疲労、迷い、背中を押してほしい、落ち着きたいなど。
- 時間軸: 今すぐの解決、節目、再出発、継続的な改善。
- 行動意図: 参拝先探し、気持ちの整理、意思決定、守り・浄化、縁づくり。
- 既存 `need_tags` と相談文のズレ: タグ化できていない自然文のまとまり。
- `history_theme` との混同リスク: 神社側の文脈タグとユーザー相談軸を分離できるか。

## 再生成コマンド

```bash
cd backend && ../.venv/bin/python manage.py export_consultation_axis_discovery --limit 100 --output ../docs/analytics/consultation-axis-discovery.md
```
