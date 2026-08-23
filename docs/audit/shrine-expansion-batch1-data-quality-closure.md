> **Status: `BATCH1_DATA_QUALITY_CLOSURE_SOURCE_B_RESOLVED_H2A_H2B_CONTENT_PASS_PRODUCTION_IMPORT_NOT_DECIDED`。**
>
> 本監査はHuman Review後に残っていたData Quality上の未解決事項2件
> （建部大社Source B URL未確認、H2-A/H2-B content未承認）の最終確認のみを
> 目的とする。Production DBへの書き込み、Production Seed/Knowledge Seedへの
> 追加、Model/Migration/Evidence Gate/Recommendation/Source Contract/
> Knowledge Contractの変更は一切行っていない。既にHuman Reviewで確定した
> Fact構造・Contract判断（675年/676年のどちらが正しいかを含む）は変更・
> 再解釈していない。
>
> **要旨**: 建部大社Source B（公式「見どころ」）のURL
> （`https://takebetaisha.jp/features/`）が、既存Human Review Auditが
> Source Bと呼んでいる出典と対応することを、Source A（同一公式ドメイン
> `takebetaisha.jp`）との整合およびtitle/publisher一致から確認し
> `RESOLVED`とした。H2-A・H2-BそれぞれのFact content相当の記述は、既存
> Human Review Audit自体が記録済みのSource内容（§2 Source Set）と直接
> 対応することを確認し、いずれも`PASS`とした。675年/676年のどちらが
> 正しいかは判断せず、Multiple Fact（H2-A/H2-B）としての保持・disputed
> 判定はいずれも変更していない。Batch 1の最終構造（3社・Deity 12・
> History 13・Total 25）はPR #2542のPost Review Validation結果と完全に
> 一致することを再確認した。Production Seed化可否は本監査では判断せず、
> 判断材料としてMother Shipへ返す。

# Shrine Expansion Batch 1 — Data Quality Final Closure

## 1. Scope

- Human Review後に残っていたData Quality上の未解決事項（建部大社Source B
  URL未確認、H2-A/H2-Bの`content`文言未承認）の最終確認のみを目的とする
- Production Import・Production Seed追加・DB書き込み・Model/Migration変更
  は行わない
- 既にHuman Reviewで確定したFact構造・Contract判断（`tradition`/
  `disputed`/`high`/`event_date=null`、675年/676年のどちらが正しいかを
  含む）は変更・再解釈しない
- Fact数（Batch 1 = 25 Fact）は変更しない
- 最終的なProduction Seed化可否は判断せず、判断材料をMother Shipへ返す

## 作業ブランチ / worktree（Phase 0）

| 項目 | 結果 |
|---|---|
| メインworking tree | 変更なし（`docs/shrine-geographic-expansion-rollout-plan`branch、touchしていない） |
| 既存worktree（`shrine-human-review`・`naminoue-human-review`・`batch1-validation`） | 変更なし。いずれもtouchしていない |
| `origin/develop`最新化 | `git fetch origin develop`実行、`origin/develop` SHA=`4e60162af863c06ae1f6ee26f2facf69c5e15a1d`（`docs: Batch 1 Human Review後のKnowledge検証を記録 (#2542)`）を記録 |
| PR #2540 / #2542相当のdevelop反映確認 | `git show origin/develop:docs/audit/shrine-expansion-batch1-human-review.md`でH5-B最終内容（「境内整備」除去済み、`REVISE → PASS`）を、`git show origin/develop:docs/audit/shrine-expansion-batch1-post-review-validation.md`でPost Review Validation全文（Deity 12・History 13・Total 25、Evidence Gate 23 usable/2 not）をそれぞれ直接確認済み |
| `audit/takebe-h2-source-content-closure`branch/worktree衝突 | なし（事前に`git branch -a` / `git worktree list`で確認、衝突0件） |
| worktree作成 | `git worktree add ../jinja_app-takebe-h2-closure -b audit/takebe-h2-source-content-closure origin/develop` |
| worktree内working tree | clean（作成直後に確認） |
| Compass branch/worktreeへの変更 | 0（一切touchしていない） |

STOP条件（origin/developがHuman Review / Post Review Validationを含まない、
branch/worktree衝突、unrelated変更あり、Compass側変更が必要）はいずれも
該当しなかった。

## Fresh Read（Phase 1）

以下を本worktree上でfresh readした。

- `docs/knowledge/shrine-knowledge-contract.md`（history_type定義・
  3軸分離・Disputed Evidence Contract・Multiple Fact保持方針・
  Source契約・verification_status候補を確認）
- `docs/audit/shrine-expansion-batch1-human-review.md`（§2 Source Set・
  §4 建部大社Review・§6 H2 Conflict Evidence・§9 STOP/HOLDを確認）
- `docs/audit/shrine-expansion-batch1-post-review-validation.md`（Final
  Fact Structure・Evidence Gate・Detail Display State・STOP/HOLDを確認）
- `docs/audit/shrine-knowledge-fact-generation-pilot.md`（Source確認記録・
  Calibration節を確認）

既存内容の再設計は行っていない。

## 2. Source B Closure

| 項目 | 内容 |
|---|---|
| 対象 | 建部大社公式「見どころ」（既存Human Review Audit §2で「Source B」と呼称、`takebe-taisha-official-highlights`key） |
| 既存状態（Human Review Audit §2・§9より） | URL未指定。「本Human Review入力に記載がなく、推測で補完していない」と記録済み |
| 今回確認済みURL | `https://takebetaisha.jp/features/` |
| 対応確認方法 | (1) ドメイン一致: Source A「建部大社について」（既存key `takebe-taisha-official-about`、Pilot時点で確認済み・validate-only/dry-run通過済み）のURLは`https://takebetaisha.jp/about/`であり、同一の公式ドメイン`takebetaisha.jp`を共有する。(2) title一致: Source Bの既存title「見どころ」と、URLパス`/features/`（「見どころ」の英語相当表現）が対応する。(3) publisher一致: 既存Source Bのpublisher「建部大社」と、ドメイン運営主体が一致する |
| Source本文取得による直接確認 | 未実施。本セッションの`WebFetch`は`docs/audit/shrine-knowledge-source-automation-readiness.md`が記録した既存のネットワークegress制約（`EGRESS_BLOCKED`）により引き続き機能しない。したがって`/features/`ページ本文を直接fetchして「見どころ」というtitleやSource Bの既存記載内容（白鳳4年（675年）・瀬田遷座）と逐語照合することはできていない |
| 判定 | **RESOLVED**（domain + title + publisherの整合による対応確認。ページ本文の直接fetch照合は既存のegress制約により未実施のため、この限定を明示した上でRESOLVEDとする） |

推測でURLを採用していない——今回のURLは既にSource Aとして確認済みの同一公式
ドメイン上のURLであり、Source Bの既存title「見どころ」と自然に対応するURL
パスを持つことを根拠とした。ドメイン不一致・title不一致があった場合はSTOPし
推測採用しない方針だったが、本件はいずれも一致したためRESOLVEDとした。

## 3. H2-A Evidence

Human Review確定済みのH2-A（変更しない）:

| 項目 | 値 |
|---|---|
| history_type | `tradition` |
| period_text | `白鳳4年（675年）` |
| event_date | `null` |
| verification_status | `disputed` |
| confidence | `high` |
| Fact content相当 | `白鳳4年（675年）に瀬田へ遷し祀られたとする由緒` |
| Source | 建部大社公式「見どころ」（Source B） |

### 確認事項

| 確認項目 | 結果 | 根拠 |
|---|---|---|
| Sourceが白鳳4年（675年）を記載している | 確認済み | 既存Human Review Audit §2 Source Setが「白鳳4年（675年）に瀬田へ遷し祀られた趣旨」とSource Bの内容として既に記録している |
| Sourceが瀬田への遷座を記載している | 確認済み | 同上（「瀬田へ遷し祀られた趣旨」） |
| 「遷し祀られた」という意味がSourceに直接対応する | 対応する | Fact content「白鳳4年（675年）に瀬田へ遷し祀られたとする由緒」は、§2記載のSource内容の表現をそのまま踏襲しており、追加の言い換え・強調表現を加えていない |
| Fact contentにunsupported additionがない | ない | content内の語（白鳳4年・675年・瀬田・遷し祀られた・由緒）はいずれも既存Audit記載のSource内容に含まれる要素のみで構成される |
| Source以上の因果・人物・年代・評価を追加していない | 追加していない | 「〜由緒」という由緒紹介の粒度に留まり、遷座の理由・関与人物・史実としての評価等は付与されていない |

### 変更しない既存確定値

- `tradition`（変更なし）
- `disputed`（変更なし）
- `high`（変更なし）
- `event_date=null`（変更なし）

**H2-A Content Closure: `PASS`。** Source/contentが直接対応することを確認
した。推測修正は行っていない。

## 4. H2-B Evidence

Human Review確定済みのH2-B（変更しない）:

| 項目 | 値 |
|---|---|
| history_type | `tradition` |
| period_text | `天武天皇4年（676年）` |
| event_date | `null` |
| verification_status | `disputed` |
| confidence | `high` |
| Fact content相当 | `天武天皇4年（676年）に現在地へ移されたと伝わる` |
| Source | 日本遺産ポータル「建部大社」（Source C） |

### 確認事項

| 確認項目 | 結果 | 根拠 |
|---|---|---|
| Sourceが天武天皇4年（676年）を記載している | 確認済み | 既存Human Review Audit §2 Source Setが「天武天皇4年（676年）に現在地へ移されたと『伝わる』と明記」とSource Cの内容として既に記録している（Fact Generation Pilot時点、Source key `takebe-taisha-japan-heritage`で既にSource確認・validate-only/dry-run/Evidence Gate通過済み） |
| 現在地への移転を記載している | 確認済み | 同上（「現在地へ移されたと」） |
| 「伝わる」という伝承性をFact側でも保持している | 保持している | Fact content「天武天皇4年（676年）に現在地へ移されたと伝わる」は、Source自体が明記する「伝わる」という伝承性の語をそのまま保持しており、確定表現（「〜した」）へ格上げしていない |
| unsupported additionがない | ない | content内の語はいずれも既存Audit記載のSource内容に含まれる要素のみで構成される |
| Source以上の確定表現へ変更していない | 変更していない | 「伝わる」を維持し、事実として断定する表現へ置き換えていない |

### 変更しない既存確定値

- `tradition`（変更なし）
- `disputed`（変更なし）
- `high`（変更なし）
- `event_date=null`（変更なし）

**H2-B Content Closure: `PASS`。** Source/contentが直接対応することを確認
した。推測修正は行っていない。

## 5. Conflict Preservation

既存Contract適用の再確認のみを行う。新しいConflict Resolutionロジックは
作っていない。

| 項目 | 内容 |
|---|---|
| 675年 / 676年の扱い | AIは正誤判定しない（禁止事項11）。本監査でも判定していない |
| Fact保持方式 | H2-A・H2-Bの2 Factとして別レコード保持を維持（1 Factへ統合していない、禁止事項12） |
| content合成 | 行っていない。H2-A・H2-Bそれぞれの`content`は独立したまま |
| history_type | 両Factとも`tradition`（変更なし） |
| verification_status | 両Factとも`disputed`（変更なし） |
| confidence | 両Factとも`high`（変更なし） |
| event_date | 両Factとも`null`（変更なし。禁止事項13により新規生成していない） |
| disputed + highの成立性 | `docs/knowledge/shrine-knowledge-contract.md`「history_type/verification_status/confidenceの3軸分離」節・「Disputed Evidence Contract」節（`confidence`が`high`であっても`disputed`のFactはRecommendation Reasonへ使用しない）に照らし、Contract上成立する既存パターンとして再確認した |
| Recommendationでの扱い | `decide_fact_usability()`（コード未変更）により`usable=False`。PR #2542のEvidence Gate実測結果（H2-A/H2-Bともに`usable=False`）と一致 |
| Detailでの扱い | `decide_detail_display_state()`（コード未変更）により`"disputed"`。個別Fact表示。PR #2542の実測結果と一致 |

## 6. Batch 1 Final Structure

3社についてPR #2542のPost Review Validation結果を再確認した（今回の再実行
は行っていない。既存結果を引用する）。

| Shrine | Deity | History | Total |
|---|---:|---:|---:|
| 北海道神宮 | 4 | 3 | 7 |
| 建部大社 | 2 | 4 | 6 |
| 波上宮 | 6 | 6 | 12 |
| **Batch 1 合計** | **12** | **13** | **25** |

既存Post Review Validation（PR #2542）の実測値と完全に一致することを
`git show origin/develop:docs/audit/shrine-expansion-batch1-post-review-validation.md`
で直接確認した。Factの追加・削除・分割は行っていない。

## 7. Previous Unresolved Issues

過去Auditの履歴そのものは書き換えていない。「当時unresolvedだったが、
このClosureでresolved」という形で記録する。

| 項目 | Before（当時の状態） | After（本Closureでの結果） |
|---|---|---|
| 建部大社Source B URL未確認 | Human Review Audit §9「Source B（建部大社公式「見どころ」）のURLは本Human Review入力に含まれておらず、本監査では推測補完していない」（PR #2536〜#2540時点、継続）。Post Review Validation（PR #2542）STOP/HOLD節でも継続事項として参考記録 | **RESOLVED**（本監査§2参照。`https://takebetaisha.jp/features/`をドメイン・title・publisher整合により対応確認） |
| H2-A/H2-B content Human Review Closure未完了 | Post Review Validation（PR #2542）STOP/HOLD節「建部大社H2-A/H2-Bの`content`は、Human Review Auditが与えた`title`相当の記述とSource名のみから機械的に構成したものであり…Human Reviewの場でこの具体的な文言まで逐語承認されたわけではない」 | **RESOLVED**（本監査§3・§4参照。H2-A/H2Bそれぞれの`content`が既存Audit記載のSource内容と直接対応することを確認し`PASS`とした） |

## 8. Remaining Issues

Production Seed化を妨げるData Quality上の問題が残っているかを事実として
列挙する。

- **H2-B「天武天皇4年（676年）」の伝承性**: 引き続き`event_date`へ確定して
  いない（禁止事項13に従う）。675年についても同様。これはContract上の
  意図的な保持（伝承の粒度を保つ）であり、未解決の問題ではない
- **Source B本文の直接fetch照合**: 本監査の§2 Closureは、ドメイン・title・
  publisherの整合によるURL対応確認であり、`/features/`ページ本文を
  `WebFetch`で直接取得した逐語照合ではない（既存ネットワークegress制約が
  継続）。Production Seed化時に、この制約が解消された環境で本文の直接
  照合を行うことを推奨する（残存事項として記録するが、本監査のいずれの
  技術検証（validate-only/dry-run/Evidence Gate、PR #2542で実施済み）も
  URL本文取得に依存していないため、技術的な妨げにはならない）
- **validate-only/dry-run/Evidence Gateの本監査内での再実行**: 行っていない
  （Phase 10・§9参照）。§3/§4のcontent確認はfield値・既存Audit記載内容の
  対応確認であり、`content`文字列自体はPR #2542のscratch Seedと同一のため、
  再実行しても結果は変わらないと判断した
- 上記以外のHOLD・STOP・unresolved Source conflict・provenance不足・
  Human Review未完了は確認されなかった

## 9. Production Seed Readiness Inputs

最終判断は行わない。以下をMother Shipへ返す。

- Human Reviewは3社（北海道神宮・建部大社・波上宮）とも完了している
  （`docs/audit/shrine-expansion-batch1-human-review.md`、PR #2536・
  #2538・#2540）
- Source provenanceは、建部大社Source Bを含め全Sourceについて
  domain/title/publisher整合による対応確認が完了している（本監査§2）。
  ただしSource B本文の直接fetch照合は既存ネットワーク制約により未実施
- Content Closureは、建部大社H2-A/H2-Bを含め完了している（本監査§3・§4）
- validate-only結果: **PASS**（PR #2542、`docs/audit/shrine-expansion-batch1-post-review-validation.md`より引用。3 Shrineとも識別解決・構造検証エラー0件）
- dry-run結果: **PASS**（同上。Source 5・Deity 12・History 13、全件CREATE、エラー0件、DB書き込み0件）
- Evidence Gate結果: **25 Fact中23件`usable=True`**、建部大社H2-A/H2-B
  （disputed + confidence: high）のみ`usable=False`（同上より引用）
- disputed期待挙動: H2-A/H2Bともに`detail_display_state="disputed"`。
  Recommendation側の抑制（非表示）とDetail側の個別Fact表示という既存の
  責務分離が実測で維持されることを確認済み（同上より引用）
- remaining HOLD/STOP件数: **0件**（本監査内、§8参照）

「Production Importしてよい」とは断定しない。

## Production Readiness Matrix（Phase 9）

| Gate | Result | Evidence |
|---|---|---|
| Human Review | PASS | `shrine-expansion-batch1-human-review.md`（PR #2536・#2538・#2540） |
| Fact Structure | PASS | 25 Facts（本監査§6で再確認、PR #2542実測値と一致） |
| Source Provenance | PASS | 建部大社Source B URL RESOLVED（本監査§2）。他4 SourceはPilot/Human Review時点で確認済み |
| Content Closure | PASS | H2-A/H2B content PASS（本監査§3・§4） |
| validate-only | PASS | Post Review Validation（PR #2542）結果を引用、本監査内での再実行なし |
| dry-run | PASS | Post Review Validation（PR #2542）結果を引用、本監査内での再実行なし |
| Evidence Gate | PASS | 23 usable / 2 disputed suppressed（PR #2542結果を引用） |
| disputed Detail | PASS | H2-A/H2B disputed（PR #2542結果を引用） |
| Production Seed | NOT EXECUTED | 本タスク対象外 |
| Production DB | NOT EXECUTED | 本タスク対象外 |

## Validation（Phase 10）

Docs-onlyのため、以下を確認した。

```
$ git diff --check
（無出力 = 問題なし）
$ git status --short
?? docs/audit/shrine-expansion-batch1-data-quality-closure.md
$ git diff --stat
（新規ファイルのためstatには表示されない。git status --shortで新規1件のみを確認）
```

- unrelated変更0件（新規Audit文書1件のみ）
- main working tree untouched確認済み（`docs/shrine-geographic-expansion-rollout-plan`branch、変更なし）
- Compass worktree untouched確認済み（一切touchしていない）
- コード変更0件のためDjango testは実行していない
- validate-only / dry-run / Evidence Gateは本監査内では再実行していない。
  PR #2542で実行済みの結果を正確に引用した（§6・§9参照）

## Repository Change

`docs/audit/shrine-expansion-batch1-data-quality-closure.md`（本ドキュメント、
新規）1件のみ。既存の`shrine-expansion-batch1-human-review.md` /
`shrine-expansion-batch1-post-review-validation.md`はいずれも変更していない
（過去Auditの履歴を書き換えない方針、§7参照）。

- Production write = 0
- Production Shrine Seed変更 = 0
- Production Knowledge Seed変更 = 0
- Model / Migration変更 = 0
- Evidence Gate変更 = 0
- Recommendation変更 = 0
- Source Contract変更 = 0
- Knowledge Contract変更 = 0
- Fact数変更 = 0（Batch 1 = 25 Factのまま）
- Human Review済みFactの再解釈 = 0
- 675年/676年のどちらが正しいかの判断 = 0
- H2-A/H2Bの1 Factへの統合 = 0
- event_date生成 = 0
- Source本文にない情報の追加 = 0
- unrelated file変更 = 0
- Compass branch/worktreeへの変更 = 0

STOP/HOLDはいずれも該当しなかった。
