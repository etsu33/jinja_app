> **Status: `KNOWLEDGE_ANALYTICS_READ_ACCESS_REQUIRED`。**
>
> Analytics providerはコードからPostHogとfresh特定できたが、本セッション
> には read/query 用のcredential・API・CLI・MCPツールのいずれも存在せず、
> リポジトリ内にも read-scoped credentialが一切provisionされていないこと
> を確認した。したがって**実データによるBaseline Reportは生成できない**
> （捏造しない）。Analytics mutation・event backfill・artificial
> Recommendation POST・Production DB write・secret/token commitは
> いずれも実行していない。

---

## 1. develop SHA

`80cf7b6dc1b0760fe1fa3497db7a77063acc4b58`（2026-08-12 15:33:58 +0900）

PR #2385（[knowledge-recommendation-analytics-observability.md](knowledge-recommendation-analytics-observability.md)）
merge確認済み。develop同期・working tree clean。

---

## 2. Analytics Provider（Phase 1）

`apps/web/src/lib/analytics/providers.ts`をfresh読み込みし、
`「以前PostHogだったはず」を信用せず`コードから直接確認した。

```ts
export class PostHogAnalyticsProvider implements AnalyticsProvider {
  private init() {
    ...
    const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
    if (!key) return false;
    posthog.init(key, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://app.posthog.com",
      capture_pageview: false,
    });
    ...
  }
  track(eventName: string, payload: AnalyticsPayload) {
    ...
    posthog.capture(eventName, payload);
  }
}
```

| 項目 | 値 |
|---|---|
| provider | PostHog（`posthog-js`パッケージ経由） |
| client | `PostHogAnalyticsProvider`（`providers.ts`）、Mobile側は`posthogAnalyticsProvider.ts`（`posthog-react-native`） |
| ingestion path | Browser → `posthog.capture()` → `api_host`（デフォルト`https://app.posthog.com`、`NEXT_PUBLIC_POSTHOG_HOST`で上書き可能。実際の本番host値はcredential shapeの範囲外のため未確認） |
| project/environment concept | PostHog Project（key単位）。本セッションからは対象Project IDを特定できない |
| read API availability | 3章参照 |
| dashboard availability | 3章参照 |

**分類: `ANALYTICS_BACKEND_IDENTIFIED`**（PostHog、曖昧性なし）。

---

## 3. Existing Access Path Inventory（Phase 2）＋ Credential / Permission Gate（Phase 3）

本セッションで確認した経路（値は一切表示せず、存在有無のみ）:

| 経路 | 状態 |
|---|---|
| CLI（posthog-cli等） | 未導入・未確認 |
| API token（Personal/Project API Key） | **リポジトリ内のいずれの`.env*`ファイル・example templateにも存在しない**（下記参照） |
| MCP/plugin | 本セッションのtool一覧にPostHog向けMCPツールは存在しない（`ToolSearch`で確認済み、[knowledge-recommendation-analytics-observability.md](knowledge-recommendation-analytics-observability.md)と同結果） |
| repo script | PostHogをread/queryするスクリプトはリポジトリ内に存在しない |
| dashboard export | 本セッションからPostHogダッシュボードへのログイン・アクセス手段なし |
| official API | 到達可能性は未検証（read-scoped credentialがないため試行不能） |
| connected tool | Vercel関連MCPツールは存在するが、PostHogとは無関係（別サービス） |

### Credential shape確認（値は表示しない）

```
apps/web/.env.local:
  NEXT_PUBLIC_POSTHOG_KEY=<redacted>
  NEXT_PUBLIC_POSTHOG_HOST=<redacted>
```

- `.env.example` / `.env.render.example` / `backend/.env.example`のいずれにも
  PostHog関連の変数は記載がない。
- `NEXT_PUBLIC_`prefixはNext.jsの規約上、**ブラウザバンドルへ埋め込まれ
  クライアントに公開される変数**であることを意味する。コード上の使われ方
  （`posthog.init(key, ...)`→`posthog.capture()`のみ）から、この
  `NEXT_PUBLIC_POSTHOG_KEY`はPostHogの「Project API Key」（**write専用の
  ingestion key**、PostHogの設計上read/queryには使えない）であると判断
  できる。
- read/query専用の「Personal API Key」に相当する変数名
  （例: `POSTHOG_PERSONAL_API_KEY`、`POSTHOG_API_KEY`（server-side）等）は、
  ローカル`.env*`・example template・Render example のいずれにも存在しない。

**分類: read-scoped credentialは本セッション・リポジトリのいずれにも
存在しない（`API_TOKEN_MISSING`）。mutation-onlyな過剰権限credentialも
存在しない（そもそも存在するのはwrite-only ingestion keyのみであり、
read/mutationいずれの権限も持たない）ため、STOP相当の危険な状態でも
ない。**

---

## 4. Post-Rollout Data Window（Phase 5）

PR #2384のProduction deploy時刻（[knowledge-recommendation-analytics-observability.md](knowledge-recommendation-analytics-observability.md)
2章、Vercel production deployment作成時刻）を起点とする:

- rollout timestamp: 2026-08-12T04:12:15Z（Vercel production deployment
  `dpl_AcehvHCZesf5j8xYqwqK4d7k9xwC`のcreated時刻）
- analysis start / end: 3章のAccess Gapにより設定不能
- elapsed time: rollout（04:12 UTC）から本監査時点（本doc作成時）まで
  約2〜3時間程度と推定されるが、実イベント数の裏付けがないため参考値
  にとどめる

**分類: `POST_ROLLOUT_WINDOW_NOT_QUERYABLE`**。

---

## 5. Event Count Baseline / Classification Distribution / Property Completeness（Phase 6-8）

3章のAccess Gapにより、いずれも取得不能。推測しない。

- `recommendation_quality` event count: 取得不能
- unique recommendation sessions / shrine impressions: 取得不能
- classification-present / missing count: 取得不能
- `knowledge_backing_class`/`deity_knowledge_used`/`history_knowledge_used`
  のpresence rate: 取得不能
- invalid enum / unexpected null / partial payload / older event
  compatibility: 取得不能

---

## 6. Funnel Join Validation（Phase 9）

3章のAccess Gapにより実データでのjoin実行はできない。コードレベルの
join key構造（`threadId`/`shrineId`/`recommendationRank`）は
[knowledge-recommendation-analytics-observability.md](knowledge-recommendation-analytics-observability.md)
7章で確認済みのまま不変（本PRでイベント関連コードへの変更はない）。

---

## 7. CTR / Save / Visit Intent Baseline（Phase 10-12）

いずれも3章のAccess Gapにより算出不能。

- CTR by `knowledge_backing_class`: 算出不能
- Save Rate by `knowledge_backing_class`: 算出不能
- Visit Intent Baseline: 算出不能。なお`visit_done`のrank/resultSetId
  欠落（既知gap、本PRでは修正しない）により、たとえAccess Gapが解消
  されても「Visit Intent」と「Actual Visit」を混同しないよう注意が
  必要（`VISIT_INTENT_BASELINE_AVAILABLE`と`ACTUAL_VISIT_ATTRIBUTION_LIMITED`
  は将来的に別分類として扱うべき点を記録するにとどめる）。

---

## 8. Confound Segmentation / Data Quality / Sample-size Status（Phase 13-15）

いずれも3章のAccess Gapにより確認不能。

- rank / hero-alternative / consultation_axis segmentation: 実データなし
- duplicate events / missing threadId・shrineId / invalid rank /
  invalid classification / inconsistent ordering: 確認不能
- sessions / impressions / clicks / saves / visit intents: 取得不能

**分類: `DATA_VOLUME_NOT_AVAILABLE`**（統計的有意差の話ではなく、
そもそも読み取れない）。

---

## 9. Baseline Report（Phase 16）

**作成しない。** 実データを取得できない状態でレポートを作成すると、
数値の捏造・誤解を招く「架空のBaseline」になってしまうため、本doc
自体をAccess Gap docとして扱う（Phase 16の指示通り）。

---

## 10. Access Gap Classification（Phase 17）

| ID | 分類 | 該当 |
|---|---|---|
| A. `PROVIDER_ACCESS_MISSING` | ○ | PostHogダッシュボードへのログイン・アカウントアクセス手段が本セッションにない |
| B. `API_TOKEN_MISSING` | ○ | read/query用のPersonal/Project API Keyがリポジトリ・環境のいずれにも存在しない |
| C. `READ_PERMISSION_MISSING` | Bに包含 | 存在するcredential自体がwrite専用のingestion keyのみで、read権限を持つcredentialが存在しないため、「権限不足」ではなく「該当credential自体が不在」 |
| D. `TOOLING_MISSING` | ○ | PostHog向けMCP/CLIツールが本セッションに存在しない |
| E. `QUERY_PATH_MISSING` | ○ | PostHogをread/queryするrepo scriptが存在しない |
| F. `DATA_NOT_YET_ACCUMULATED` | 判定不能 | A・B・D・Eによりそもそも確認不能なため、データが少ないのか無いのか自体を判別できない |

---

## 11. Smallest Valuable Next Action（Phase 18）

**read accessなし**のケースに該当するため:

→ **Analytics read-only access整備**（PostHog Personal API Key
（read-only scope限定）の安全な運用方法を確立すること）を、次に
着手すべき最小の作業として提示する。ただし本PRでは**設計のみ**
行い、実装・credential発行・repo変更は行わない。

---

## 12. Analytics Access Implementation Proposal（Phase 19、設計のみ）

**秘密情報をrepoへ保存する設計は提案しない。** 以下4案を比較する。

| 案 | 概要 | Security | Reproducibility | Ownership | Maintenance |
|---|---|---|---|---|---|
| A. PostHog read-only Personal API Key運用 | Read-only scope限定のPersonal API Keyを発行し、ローカル環境変数（credential file、repo外）として管理。既存の`scripts/migration_safety/`の資格情報ブリッジパターン（`~/.config/kami-musubi/production-db.env`相当）を踏襲 | 高（scope限定・repo外保管・既存パターンと同じ安全設計を再利用可能） | 高（誰でも同じ手順で再現可能） | Mother Ship（PostHogアカウント所有者）がkey発行 | Key rotation・失効管理が必要 |
| B. repo-local report script | Aの credential運用を前提に、read-only queryを実行しMarkdown/JSON出力するCLIスクリプトを追加（`scripts/analytics/`等） | Aに依存 | 高（再現可能な計測手順として固定化） | 開発者（実装・保守） | スクリプト自体の保守 |
| C. CI manual workflow | GitHub ActionsのSecrets機構でread-only Keyを保管し、手動トリガーのWorkflowでレポート生成 | 中〜高（GitHub Secretsは相応に安全だが、Actions実行ログへの値漏洩に注意が必要） | 高 | リポジトリ管理者（Secrets登録） | Workflow定義・Secrets更新の保守 |
| D. Dashboard export（手動） | Mother Ship自身がPostHog UIから手動でCSV/画面をエクスポートし、必要時にCodexへ共有 | 最高（credentialを一切コード・repoに置かない） | 低（毎回手動、手順のブレが出やすい） | Mother Ship | 都度の手作業 |

比較の要点: A+B（Personal API Key + repo-local script）が、既存の
Production DB read-onlyアクセス（`scripts/migration_safety/`）と同じ
設計思想（scope限定・repo外保管・read-only強制）を踏襲でき、
再現性・保守性のバランスが良い。Dは最も安全だが継続運用には向かない。
Cは中間案。**この比較は設計提案であり、どれを選ぶかはMother Ship
決定とする。**

---

## 13. Ownership / Operations（Phase 20、未確定はMother Ship決定として残す）

以下はいずれも本セッションからは確認・決定できない。Mother Ship
決定事項として明示的に残す。

- PostHog providerのアカウント所有者は誰か（不明）
- read tokenの発行・管理を誰が行うか（不明）
- token rotationの方針（不明）
- report実行のowner（Codexが定期実行するのか、人が手動実行するのか）（不明）
- report cadence（頻度）（不明）

---

## 14. Limitations

- 本監査はPostHogの「Project ID」や「本番host値」自体を特定していない
  （credential shapeの範囲を超えるため意図的に確認していない）。
- `.git`ログに存在した過去の未マージローカルブランチ
  （`audit/posthog-recommendation-events`、2026年6月時点）を参考として
  一瞥したが、これはBehavior Signal（Recommendation Score v2）向けの
  別トピックの未完成ドラフトであり、read access獲得の先例にはならない
  （当時も"本番環境で確認すべきこと"として人手でのダッシュボード確認を
  前提としており、プログラム的なread accessは当時から存在しなかった
  ことがうかがえる）。本監査の結論を裏付ける参考情報として記録するに
  とどめ、正本としては扱わない。

---

## 15. Final Classification

**`KNOWLEDGE_ANALYTICS_READ_ACCESS_REQUIRED`**

Analytics providerはPostHogとfresh特定できた（`ANALYTICS_BACKEND_IDENTIFIED`）。
しかし、read/query用credential・API・CLI・MCPツールのいずれも本
セッション・リポジトリに存在しないため、実データによるBaseline
Report生成は不可能であり、捏造もしていない。次の最小の作業は
「Analytics read-only access整備」であり、その実装方法の比較のみを
設計として提示した（実装はしない）。Ownershipに関する未確定事項は
Mother Ship決定として明示的に残す。

Production DB writes = 0
Analytics mutations = 0
Recommendation behavior changes = 0
Ranking changes = 0
