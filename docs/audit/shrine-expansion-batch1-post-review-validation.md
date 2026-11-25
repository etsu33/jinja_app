> **Status: `POST_HUMAN_REVIEW_VALIDATION_PASS_25_FACTS_NO_STOP_PRODUCTION_IMPORT_NOT_DECIDED`。**
>
> 本監査はread-only + scratch DB限定の技術検証である。Production DBへの
> 接続・書き込み、Production Shrine Seed/Knowledge Seedへの変更、Model/
> Migration/Evidence Gate/Recommendation/Source Contract/Knowledge
> Contractの変更は一切行っていない。**Production Importを実行するか否かは
> 本監査では判断しない。**
>
> **要旨**: `docs/audit/shrine-expansion-batch1-human-review.md`
> （PR #2536・#2538・#2540、develop反映済み）を最新正本として、北海道神宮・
> 建部大社・波上宮の最終Fact構造（Deity 12・History 13・Total 25）を
> 既存Knowledge Seed Schemaへ機械的に変換した。既存`import_shrine_knowledge`
> の`--validate-only`・`--dry-run`はいずれもPASS（エラー0件）。既存
> `decide_fact_usability()`を25 Factへ適用した結果、23 Factが`usable=True`、
> 建部大社H2-A/H2-B（disputed + confidence: high）のみ`usable=False`と
> なり、confidence=highがdisputedを上書きしないことを実測で確認した。
> `decide_detail_display_state()`もH2-A/H2-Bをいずれも`"disputed"`と判定し、
> Recommendation側の抑制とDetail側の個別表示という既存の責務分離が
> 期待どおり維持されることを確認した。STOP/HOLDは0件。

# Shrine Expansion Batch 1 — Post Human Review Validation

## Scope

- Human Review Closure後に確定した北海道神宮・建部大社・波上宮の最終Factを、
  既存Shrine Knowledge Seed Schemaへ機械的に変換し、
  validate-only・dry-run・Evidence Gate・Detail Display Stateを検証する
- Production DB / Production Seedへの書き込みは行わない
- Production Importへ進める技術的条件が満たされているかを事実として
  母艦へ返す。**Production Import可否そのものは判断しない**

## 作業ブランチ / worktree（Phase 0）

| 項目 | 結果 |
|---|---|
| メインworking tree | 変更なし（`docs/shrine-geographic-expansion-rollout-plan`branch、touchしていない） |
| 既存worktree（`shrine-human-review`・`naminoue-human-review`） | 変更なし。いずれもtouchしていない |
| `origin/develop`最新化 | `git fetch origin`実行、`origin/develop` SHA=`59f92640` |
| PR #2540のdevelop反映確認 | `git show origin/develop:docs/audit/shrine-expansion-batch1-human-review.md`でH5-B最終内容（「境内整備」除去済み、`REVISE → PASS`）を直接確認済み |
| `audit/shrine-expansion-batch1-post-review-validation`branch/worktree衝突 | なし（事前確認、衝突0件） |
| worktree作成 | `git worktree add ../jinja_app-batch1-validation audit/shrine-expansion-batch1-post-review-validation`（`origin/develop`起点で新規branch作成後） |
| worktree内working tree | clean（作成直後に確認） |
| Compass branch/worktreeへの変更 | 0（一切touchしていない） |

STOP条件（#2540未反映、branch/worktree衝突、unrelated変更、他branchへの
変更が必要）はいずれも該当しなかった。

## Source of Truth

`docs/audit/shrine-expansion-batch1-human-review.md`（develop反映済み、
PR #2536・#2538・#2540を経て確定）を最終Fact構造の唯一の正本として使用した。
旧Pilot（`docs/audit/shrine-knowledge-fact-generation-pilot.md`、PR #2533）
と内容が異なる箇所は、すべてHuman Review Auditを優先した（禁止事項22）。

`content`フィールドの再構成方針（Human Review Auditの表には
`history_type`/`period_text`/`event_date`/`verification_status`/
`confidence`/Sourceのみが記載され、`content`本文は literal に再掲されて
いないため）:

- 変更なしのFact（北海道神宮H2・H3、建部大社D1・D2・H1・H3、波上宮
  Deity 6件・H1〜H4）: このセッションのscratchpadに残存していた
  Fact Generation Pilot時点の元scratch Seed JSON
  （`/tmp/.../scratchpad/fact_pilot_knowledge_seed.json`、Pilot当時に
  実際に`validate-only`/`dry-run`/Evidence Gate 23/23 usableを通過した
  実物）から`content`をそのまま転記した
- 北海道神宮H1: 元Pilotの`content`から、Human Review Auditが明示的に
  指摘した不支持表現「北海道神宮はこれを創祀としている」のみを機械的に
  除去した
- 波上宮H1: 元Pilotの`content`をそのまま使用し、`history_type`のみ
  `regional_context`→`founding`へ変更した（Audit§5.2の指示どおり）
- 波上宮H5-A/H5-B: 元Pilotの単一History（「波上宮は先の大戦で被災し、
  昭和28年に本殿と社務所、昭和36年に拝殿を再建し、平成5年には平成の
  御造営による社殿が竣工した。」）を、Human Review Auditが指定した
  被災／戦後再建の境界でそのまま分割した。新しい情報は追加していない。
  H5-Bの「境内整備」相当の記述はPR #2540のClosureにより既に除去済み
- 建部大社H2-A/H2-B: Human Review Auditは`title`相当の短い記述
  （「白鳳4年（675年）に瀬田へ遷し祀られたとする由緒」「天武天皇4年
  （676年）に現在地へ移されたと伝わる」、§4.3・§4.5に記載）のみを与えており、
  独立した`content`文は記載されていない。Contractは`content`を必須
  フィールドとするため、Audit記載の`title`相当の文言と、同じくAudit記載の
  Source名（建部大社公式「見どころ」／日本遺産ポータル）のみを使い、
  「〈Source名〉は、〈Audit記載の記述〉としている」という機械的な文型で
  `content`を構成した。**Source本文の新規調査・新しい事実の追加は一切
  行っていない**——使用した語はすべてAuditが既に確定した要素（Source名・
  claim文言）のみである

## Final Fact Structure（Phase 2・3: Count Gate）

| Shrine | Deity | History | Total |
|---|---:|---:|---:|
| 北海道神宮 | 4 | 3 | 7 |
| 建部大社 | 2 | 4 | 6 |
| 波上宮 | 6 | 6 | 12 |
| **Total** | **12** | **13** | **25** |

期待値（25 Facts）と実際に生成したscratch Seedの実測件数（Deity 12・
History 13・Total 25、`python3 -c "..."`でJSONを直接集計して確認）が
完全一致した。旧Pilot（23 Facts）との差分理由:

- 建部大社 H2分離（1 Fact → H2-A/H2-B 2 Fact）: +1
- 波上宮 History再粒度化（旧History-5 1件 → H5-A/H5-B 2 Fact）: +1
- 北海道神宮: Fact数変更なし（H1のhistory_typeのみ変更）

**23 → 25の差分理由が正確に一致したため、Count GateはPASS。** 期待値へ
合わせるための新規Fact生成は行っていない。

## Scratch Seed（Phase 4）

- path: `/tmp/kami-musubi-batch1-post-review/knowledge_seed.json`
  （scratch-only、repositoryへ配置していない、`git add`していない）
- `schema_version: "1.0"`（既存Schemaのまま）
- Source: 5件（旧Pilot4件 + 建部大社公式「見どころ」1件新規）
  - 新規Source（`takebe-taisha-official-highlights`）のURLは、Human
    Review Audit§9が既に記録した既知の未解決事項（URL未指定）を継承し、
    空文字のまま。新規に推測URLを補完していない
- `verified_at`/`accessed_at`は、既存Pilot・既存Batch運用パターン
  （同一Source/同一セッション内で固定UTC timestampを使う）をそのまま
  踏襲し、`2026-08-23T07:00:00+00:00`／`2026-08-23`を機械的に付与した。
  不明なtimestampの推測は行っていない
- JSON構文: 有効（`python3 -c "import json; json.load(...)"`で確認）
- Shrine数: 3、Source数: 5、Deity数: 12、History数: 13、Total: 25
- source_keys解決: 全25 FactのSource参照が5 Source key内で解決すること
  をスクリプトで確認済み（unresolved 0件）

## validate-only（Phase 5）

```
$ python manage.py import_shrine_knowledge /tmp/kami-musubi-batch1-post-review/knowledge_seed.json --validate-only
validate-only: OK, no errors
```

**結果: PASS。** 3 Shrineとも一意にidentity解決（`resolve_shrine`）、
構造検証（schema_version・必須field・source_keys・値enum・
`verified_at`整合性）ともにエラー0件。既存commandのCLI usage
（`add_arguments`、`seed_path`位置引数 + `--validate-only`/`--dry-run`
フラグ）はコードから直接確認した上で実行した（コード変更なし）。

## dry-run（Phase 6）

```
$ python manage.py import_shrine_knowledge /tmp/kami-musubi-batch1-post-review/knowledge_seed.json --dry-run
[source] CREATE ×5
[deity] CREATE ×12
[history] CREATE ×13
plan summary: {'source_CREATE': 5, 'deity_CREATE': 12, 'history_CREATE': 13}
dry-run: OK, no DB writes performed
```

**結果: PASS。** 全25 Fact + 5 SourceがすべてCREATE判定（SKIP_EXISTS /
CONFLICT / AMBIGUOUS 0件）、エラー0件、DB書き込み0件。scratch DB
（このセッション専用のlocal PostgreSQL。Fact Generation Pilot・Discovery
Pilotから継続使用している既存環境で、3 Shrine base行は既に存在済み。
既存手順の再利用のみで新規手順は作っていない）以外への接続・書き込みは
一切行っていない。

## Evidence Gate（Phase 7）

既存`evidence_gate.decide_fact_usability()`（コード変更なし）を、
パース済みscratch Seedの全25 Factに対し実際に呼び出した。

```
total facts: 25, usable: 23, suppressed: 2
```

| Shrine | Fact | verification_status | confidence | usable |
|---|---|---|---|---|
| 建部大社 | 白鳳4年（675年）に瀬田へ遷し祀られたとする由緒（H2-A） | disputed | high | **False** |
| 建部大社 | 天武天皇4年（676年）に現在地へ移されたと伝わる（H2-B） | disputed | high | **False** |
| その他23 Fact | （全件） | source_confirmed | high | **True** |

**H2-A/H2-Bはいずれも`usable=False`、`display_mode=hidden`、
`reason_strength=suppressed`、`reason=fact_not_ready`。confidence=highが
disputedを上書きしていないことを実測で確認した。** 「23 usable」を
先に決めつけず、既存Evidence Gateの実行結果をそのまま記録している
（実測値と期待値が一致した結果として23件になった）。

## Detail Display State（Phase 8）

既存`evidence_gate.decide_detail_display_state()`（コード変更なし）が
利用可能であることを確認し、H2-A/H2-Bについて実際に呼び出した。

| Shrine | Fact | detail_display_state |
|---|---|---|
| 建部大社 | 白鳳4年（675年）に瀬田へ遷し祀られたとする由緒（H2-A） | `disputed` |
| 建部大社 | 天武天皇4年（676年）に現在地へ移されたと伝わる（H2-B） | `disputed` |

**Contract期待値（disputed + fact-ready Source → detail display state =
disputed）と一致した。** Recommendation側（`usable=False`、非表示）と
Detail側（`disputed`状態で個別Fact表示可能）という既存の責務分離が、
コード変更なしに維持されていることを実測で確認した。

## Production Safety

| 項目 | 結果 |
|---|---|
| Production DB接続 | 0（scratch DBのみ。接続先は`127.0.0.1:5432/jinja_db`、このセッション専用のlocal PostgreSQL） |
| Production Shrine Seed変更 | 0 |
| Production Knowledge Seed変更 | 0 |
| Model / Migration変更 | 0 |
| Evidence Gate変更 | 0 |
| Recommendation変更 | 0 |
| Source Contract変更 | 0 |
| Knowledge Contract変更 | 0 |
| 新規Importer / 新規Validation tooling / 新規Evidence Gate | 0（既存`import_shrine_knowledge`・既存`evidence_gate.py`をそのまま使用） |
| scratch artifact | `/tmp/kami-musubi-batch1-post-review/`配下のみに存在、repositoryへcommitしていない |

## STOP / HOLD

STOP/HOLDは0件。以下、参考記録のみ（新規のSTOP事項ではない）:

- 建部大社Source B（見どころ）のURL未確認は、Human Review Audit§9が
  既に記録済みの継続事項。本監査で新たに発見したものではなく、また
  本監査のいずれのcheck（validate-only/dry-run/Evidence Gate）も
  URLの有無に依存しないため、技術的な妨げにはならなかった
- H2-B「天武天皇4年（676年）」の「伝わる」という伝承性は、引き続き
  `event_date`へ確定していない（禁止事項19に従う）
- 建部大社H2-A/H2-Bの`content`は、Human Review Auditが与えた
  `title`相当の記述とSource名のみから機械的に構成したものであり
  （§Source of Truth参照）、Human Reviewの場でこの具体的な文言まで
  逐語承認されたわけではない。Production Seed化の際は、この`content`
  文言自体についてもHuman Reviewでの再確認を推奨する

## Mother Ship Decision Inputs

以下を事実として返す。**Production Importを実行するかは判断しない。**

- **Schema validation結果**: PASS（`validate-only`、3 Shrineとも識別解決・
  構造検証エラー0件）
- **dry-run結果**: PASS（Source 5・Deity 12・History 13、全件CREATE、
  エラー0件）
- **Evidence Gate結果**: 25 Fact中23 Factが`usable=True`、建部大社
  H2-A/H2-Bの2 Factが`usable=False`（disputed、confidence=highに
  よる上書きなし）
- **disputed期待挙動**: Recommendation側`usable=False`・Detail側
  `detail_display_state=disputed`という既存Contractの責務分離が
  実測で確認された
- **unresolved issues**: 建部大社Source BのURL未確認、H2-A/H2-Bの
  `content`文言がHuman Reviewで逐語承認されたものではない機械的構成
  である点（上記STOP/HOLD参照）。技術的な妨げにはなっていないが、
  Production Seed化前に確認を推奨する
- **Production変更0**: DB接続0・Seed変更0・Model/Migration変更0・
  Evidence Gate/Recommendation/Contract変更0

## Validation（Phase 10）

```
$ git diff --check
（無出力 = 問題なし）
$ git status --short
```

の結果を確認する（コミット時に併記）。変更ファイルはAudit document
1件のみであり、scratch Seed（`/tmp/kami-musubi-batch1-post-review/`）は
repository差分に含まれていない。コード/Seed変更は0件のためDjango test
は実行していない。
