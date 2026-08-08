> **Status: Active — Stop Gate 1 発動、Phase 2以降は未着手**
>
> 本ドキュメントはVercel APIによる実際のdeploy設定確認、およびそれに伴う
> Stop Gate 1の発動記録である。**productionへのwriteは一切行っていない。**
> 読み取り専用のAPI呼び出し・公開URLへのGETリクエストのみを実施した。

# Production Reality Audit / Stop Gate 1

## Mother Ship Decision（記録）

| 項目 | 状態 |
|---|---|
| PR #2314 | MERGED（2026-08-08T14:39:53Z、merge commit `4b8894ab`） |
| Batch 8 | PAUSE（確定） |
| Score refinement | PAUSE継続（確定） |
| PER_FACT_RENDERING | PAUSE継続（確定） |
| Source UI | PAUSE継続（確定） |
| Ranking Explainability | PAUSE継続（確定） |

## Phase 0 — Base

| 項目 | 値 |
|---|---|
| develop HEAD | `4b8894abb0ed2153e5ed67b0e518db5916adb066` |
| working tree | clean |
| PR #2314 | develop反映済み |
| `docs/audit/knowledge-production-readiness-audit.md` | 正本として確認済み（Phase 1で一部訂正が入る、後述） |
| Knowledge Coverage | 41/100（変更なし） |

---

## Phase 1 — Production Reality Audit

### 使用した確認手段

- **Vercel**: 本session環境に既に設定されているVercel MCP tool（`list_teams`/
  `get_project`/`list_deployments`）経由で、実際のdeployment履歴を直接取得した。
  これは読み取り専用APIであり、writeは一切行っていない。
- **Render**: 同等のMCP toolは存在しない。公開URL（`jinja-backend.onrender.com`）
  への読み取り専用GETリクエスト（`/api/schema/`、`/api/health/`、`/`）を試行した
  （一般ユーザーがブラウザでアクセスするのと同じ操作であり、認証情報の使用や
  production writeには該当しない）。

### 決定的な発見: Vercel productionは`develop`ブランチ

`list_deployments`で取得した直近20件のdeploymentのうち、`target: "production"`が
付いた10件は**すべて`branch: develop`**だった。`docs/*`等のPRブランチによる
deploymentは全て`target: null`（Preview）だった。

```
target: production の10件、いずれも branch: develop
（本session中にmergeした全PR — Batch 5〜Knowledge Production Readiness Audit
  まで — のdevelop mergeが、それぞれ実際にVercel productionへ反映されていた）
```

**これは`infra/README.md`が明記する「`main`が本番デプロイ対象ブランチ」という
記述と直接矛盾する。** `infra/README.md`の記述だけでproduction実態を確定しては
いけない、というStop Gate 1の前提が、まさにここで実証された。

### 分類: Frontend = `PRODUCTION_DEVELOP_CONFIRMED`

Vercel（frontend）については、直接APIで確認した事実として
`PRODUCTION_DEVELOP_CONFIRMED`と分類する。**推測ではなく、実際のdeployment
履歴から直接確認した。**

### Backend（Render）: `PRODUCTION_STATE_UNKNOWN`

Render用の同等API/MCP toolは本session環境に存在しない。公開URL
（`https://jinja-backend.onrender.com/`、`/api/schema/`、`/api/health/`）へ
読み取り専用のGETリクエストを3回試行したが、**いずれも`503 Service
Unavailable`（`Retry-After: 5`）が返り、到達できなかった。** サービスが
一時停止中・スリープ中・障害中のいずれかである可能性があるが、原因の特定は
本Auditのスコープ外（Renderダッシュボードへのアクセス手段がないため）。

この結果、Renderのデプロイ対象ブランチを直接確認する手段が尽きたため、
**Backendについては`PRODUCTION_STATE_UNKNOWN`のまま確定させず、これ以上の
推測は行わない。**

---

## Stop Gate 1（発動）

> production deploy branchを確認できなければ停止。「infra/README.mdにmainと
> 書いてある」だけでproduction実態を確定しない。

**Stop Gate 1を発動する。** 理由:

- Frontend（Vercel）の実態は`develop`であると直接確認できたが、これは
  `infra/README.md`の記述（`main`）と矛盾する
- Backend（Render）の実態は、利用可能な手段を尽くしても確認できなかった
  （`PRODUCTION_STATE_UNKNOWN`）
- Knowledge Data（本Auditシリーズの主題）はBackend/PostgreSQLに属する
  問題であり、Frontendの確認結果だけでは代替できない

したがって、**Phase 2（Branch Gap Audit）以降は「productionが`main`である」
という前提に基づいており、この前提自体が確認できていないため着手しない。**
Phase 2-9はすべて保留とする。

### 重要な訂正: 前回Audit（`docs/audit/knowledge-production-readiness-audit.md`）の記述について

前回Auditは「`main`が本番デプロイ対象ブランチである」という`infra/README.md`の
記述を根拠に、「`main`は5ヶ月停滞し、Knowledge機能自体を含まない」という
結論を導いた。**この技術的事実（`main`が3088 commit遅れ、Knowledge modelsを
含まない）自体は今回も変更していない（`git`で再確認可能な客観的事実であり、
今回のVercel APIの発見と矛盾しない）。しかし、「この`main`が実際に
productionへデプロイされている」という前提は、Frontendについては誤りだった
ことが判明した。** Backendについても同様に`main`ではなく`develop`が
実際のデプロイ対象である可能性があり、その場合、前回Auditの
「production未実装」という結論は**訂正が必要**になる。

**この可能性は未確認のままである。** 今回のAuditはこれを断定せず、
「前回の前提が今回の証拠と矛盾するため、Phase 2以降は着手できない」という
事実だけを記録する。

---

## Repository Changes

- `docs/audit/production-reality-audit-stop-gate-1.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Model/Service/Migration/DB書き込み: すべて変更なし。
  Render/Vercelへのproduction writeも一切行っていない）

## Stop

Stop Gate 1発動により、Phase 2以降（Branch Gap Audit、Migration Gap、Release
Strategy Candidates、Knowledge Data Reproducibility、Import Contract
Requirements、Staging Requirement、Release Acceptance Criteria、Batch 8
Re-entry Gate）はいずれも着手していない。

Mother Shipへ返す確認事項:

- [ ] Backend（Render）の実際のデプロイ対象ブランチを、Renderダッシュボード
      またはアカウントを持つ人物から直接確認できるか
- [ ] `jinja-backend.onrender.com`が503を返す原因（スリープ・停止・障害）を
      確認できるか
- [ ] Frontend/Backendのデプロイ対象ブランチが異なる状態（Frontend=develop、
      Backend=main等）が意図的な設計か、それとも単なる設定の食い違いか
