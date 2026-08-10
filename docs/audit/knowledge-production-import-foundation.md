> **Status: `KNOWLEDGE_IMPORT_READY_WITH_LIMITATIONS`。**
>
> 本ドキュメントは、Batch 1〜7で作成済みのShrine Knowledge Data
> （`ShrineKnowledgeSource`/`ShrineDeity`/`ShrineHistory`）を
> Productionへ安全かつ再現可能に投入するためのfoundation（seed format・
> 識別戦略・importer・検証手順）の設計・実装・検証記録である。
>
> **本ドキュメント作成のセッションではProduction Knowledge Data write・
> Batch 8・Score/Ranking変更・Source UI・PER_FACT_RENDERINGのいずれも
> 実行していない。** Productionに対して実行したのは`readonly_query.sh`
> 経由のSELECTと、`import_shrine_knowledge --validate-only`/`--dry-run`
> （いずれもDB書き込みなし）のみ。Production Knowledge write可否は
> Mother Ship判断待ち。
>
> 責務境界: Knowledge Factの値の意味・Source契約・Evidence Gate要件は
> `docs/knowledge/shrine-knowledge-contract.md`が正本。本書はそれを
> 再定義せず、「既存契約に従うDataをどうやって安全にDBへ入れるか」
> という投入基盤のみを扱う。

# Knowledge Production Import Foundation

## 1. develop SHA

作業開始時点: `e1cc32f2`（PR #2340 反映済み、`origin/develop`と同期済み）。

---

## 2. Local Knowledge Inventory（Phase 1）

Local開発DB（Postgres）の実測（`readonly`ではなくORM経由のcount、DB書き込みなし）:

| 項目 | 件数 |
|---|---|
| `ShrineKnowledgeSource` | 61（うちFactへ実際にrelationされているのは59。2件は未使用） |
| `ShrineDeity` | 103 |
| `ShrineHistory` | 85 |
| Knowledge Dataを持つ神社数 | 41（全件id 1-100の範囲、重複名神社・QA fixture神社は0件） |

| 内訳 | 値 |
|---|---|
| Source `source_type` | `shrine_official`=47, `secondary_editorial`=5, `cultural_property`=4, `local_history`=2, `tourism_official`=1, `government`=1, `user_observation`=1 |
| Source `verification_status` | `source_confirmed`=60, `draft`=1 |
| Deity/History `verification_status` | 全件`source_confirmed` |
| Deity `confidence` | `high`=99, `medium`=4 |
| History `confidence` | `high`=71, `medium`=14 |

---

## 3. Reproducibility Gap（Phase 2）

Batch 1〜7の投入方法を`docs/audit/shrine-knowledge-rollout-batch-1.md`等で
確認した結果:

> 「データはDjango ORM経由（`full_clean()`によるmodel validationを実施）で
> 投入し」（batch-1.md、11行目）

**分類: `LOCAL_DB_ONLY`。** 投入はDjango shell経由のORM呼び出しで行われ、
再実行可能な構造化ファイル（JSON/CSV/fixture/management command）は
一切残されていない。手順（Contract Compatibility Gate・Admin QA等の
「工程」）はBatch各docに記録されているが、**実際に投入された値そのもの**
を再現できる正本はDB行自体のみだった。

本Foundationの`export_shrine_knowledge`コマンド（Section 5）で、この
DB行を`backend/temples/data/knowledge_seeds/batch_1_7_seed.json`へ
一度変換し、リポジトリへコミットすることで、以後は**`FULLY_REPRODUCIBLE`**
（正本ファイルからの再実行が可能）へ移行する。

---

## 4. Canonical Import Format（Phase 3）

Versioned JSON seed。トップレベル構造:

```json
{
  "schema_version": "1.0",
  "sources": [
    {
      "key": "src-1",
      "source_type": "shrine_official",
      "title": "...",
      "publisher": "", "url": "", "bibliography": "",
      "accessed_at": "2026-...", "verified_at": "2026-...T00:00:00+00:00",
      "verification_status": "source_confirmed", "confidence": "high",
      "language": "ja", "note": ""
    }
  ],
  "shrines": [
    {
      "shrine_ref": {"name_jp": "...", "address": "..."},
      "deities": [
        {"display_name": "...", "canonical_name": "...", "role": "primary",
         "sort_order": 0, "verification_status": "source_confirmed",
         "confidence": "high", "verified_at": "...", "note": "",
         "source_keys": ["src-1"]}
      ],
      "histories": [
        {"history_type": "official_origin", "title": "...", "content": "...",
         "period_text": "", "event_date": null, "sort_order": 0,
         "verification_status": "source_confirmed", "confidence": "high",
         "verified_at": "...", "note": "", "source_keys": ["src-1"]}
      ]
    }
  ]
}
```

`key`（Source）はこのファイル内でのみ有効な参照子であり、DBへ
永続化されない（Section 6参照）。**Production側のnumeric PKはseedの
どこにも登場しない。**

実装: `backend/temples/services/knowledge_seed.py`の`parse_seed()`が
構造的検証（enum妥当性・必須field・`source_keys`参照整合性・
`verification_status`と`verified_at`の整合性）を行う。1件のエラーで
停止せず、全エラーを収集して返す（`--validate-only`が一括報告できる
ため）。

---

## 5. Shrine Stable Identity（Phase 4、最重要）

`Shrine`にはslug・external_idのような専用の安定識別子field**が存在しない**。
`place_ref`（Google Places解決済みの場合のみ）はnullableで、Batch 1〜7の
対象神社（元々の100件カタログ由来）はいずれも`place_ref_id IS NULL`。

`name_jp`単独の解決は禁止（`docs/audit/temples-0091-production-remediation.md`
で実害化した`.first()`問題を踏まえる）。`resolve_shrine()`
（`knowledge_seed.py`）の解決順序:

1. `name_jp`で絞り込む
2. `address`が一致する行が1件に絞れればそれを採用
3. 複数残る場合（重複名神社、または0091と同じく重複行が同一addressを
   持つ場合）、`place_ref_id IS NULL`（元カタログ由来）を優先
4. それでも複数、または0件の場合は**解決不能**として
   `AMBIGUOUS`/`NOT_FOUND`を返す。呼び出し側は絶対に推測しない

**実測結果**: Batch 1〜7の41神社すべてが、production実dumpの復元DBに
対して`OK`（単一一致）で解決した。`AMBIGUOUS`/`NOT_FOUND`は0件
（Section 9参照）。曖昧解決ロジック自体は`test_resolve_shrine_ambiguous_when_both_canonical`
でユニットテスト済み。

### 5.1 Schema Drift再発の検出と修正

Production-equivalent testの初回実行で、`resolve_shrine()`が0091と
**同一クラスのバグ**を持っていたことが判明した: `Shrine.objects.filter(name_jp=...)`
が全column（`location`含む）をSELECTし、production実DBの`location`列が
`text`型（historical modelは`PointField`）であることから`GEOSException`が
発生した。`.only("id", "name_jp", "address", "place_ref_id")`で
`location`をSELECT対象から除外し修正（Section 9で再検証しPASS）。
regression test（`test_gis_knowledge_seed_shrine_identity.py`）を追加し、
修正前のコードに対して実際に同じ例外で失敗することを確認済み。

**この発見自体が、Production-equivalent testを本番投入前に必ず実施する
という本Foundationの方針の正当性を裏付けている。**

---

## 6. Importer Contract（Phase 5）

`backend/temples/management/commands/import_shrine_knowledge.py`

```bash
python manage.py import_shrine_knowledge <seed.json> --validate-only
python manage.py import_shrine_knowledge <seed.json> --dry-run
python manage.py import_shrine_knowledge <seed.json>
```

| mode | 内容 | DB書き込み |
|---|---|---|
| `--validate-only` | 構造検証 + shrine identity解決のみ | なし |
| `--dry-run` | 上記 + 既存行とのCREATE/SKIP計画を実DBに対して計算 | なし |
| （flagなし） | 上記planを計算し、エラー0件ならatomic transaction内で適用 | あり（全件成功時のみ） |

エラーが1件でもあれば、いずれのmodeでもexit非0。

### Natural key / Idempotency（Phase 6）

`ShrineKnowledgeSource`/`ShrineDeity`/`ShrineHistory`のいずれにも
専用のnatural key fieldが存在しない（追加は本Foundationのscope外——
schema変更を伴い、Batch 8相当の判断が必要なため）。既存fieldの内容から
導出する:

| Model | 既存行とみなす条件 |
|---|---|
| `ShrineKnowledgeSource`（URLあり） | `source_type` + normalized URL。重要metadata一致時だけ一意な既存Sourceを`REUSE_EXISTING` |
| `ShrineKnowledgeSource`（URLなし） | `source_type` + `title` + (`bibliography`があれば`bibliography`一致) |
| `ShrineDeity` | `shrine` + `display_name` |
| `ShrineHistory` | `shrine` + `history_type` + `title` |

URL normalizationはscheme/hostのcase、default port、fragment、非root末尾slash
のみを正規化する。http/httpsとquery stringは区別する。normalized URL一致が
複数なら`SOURCE_REUSE_AMBIGUOUS`、publisher/verification_status/confidence/
bibliography/languageが異なれば`SOURCE_REUSE_CONFLICT`として全importを停止する。

**CREATE/UPDATE policy**: 一致する既存Sourceは`REUSE_EXISTING`、既存Factは
`SKIP_EXISTS`（**silent overwriteしない**——内容が古くても上書きしない）。新規のみ`CREATE`。
既存Factの内容修正は本Foundationのimporterでは扱わない
（Section 12「Limitations」参照、既存のAdmin編集フローを使う）。

同一seedを2回実行しても新規作成は発生しないことを、local実データ
（Section 8）・production-equivalent復元DB（Section 9）の両方で実測確認済み。

### Transaction Boundary（Phase 7）

適用（flagなしmode）は単一の`transaction.atomic()`で全件を包む。
Sourceの作成からShrine identity解決・Deity/History作成・M2M linkまで
すべて同一transaction内。途中で1件でも`full_clean()`失敗等が発生すれば
全体がrollbackされ、部分的なSource/Deity/History/relationは残らない
（`test_import_blocks_entirely_on_ambiguous_shrine_no_partial_write`で
検証済み）。

### Validation Rules（Phase 8）

`parse_seed()`が構造検証を行う: `schema_version`一致、enum妥当性
（`source_type`/`verification_status`/`confidence`/`role`/`history_type`）、
必須field非空、`verification_status`が`source_confirmed`/`reviewed`の場合
`verified_at`必須、`source_keys`参照整合性。1件でもfailすればwriteしない
（`--validate-only`・`--dry-run`・適用のいずれでも同じ検証を通る）。

---

## 7. Export Command（Phase 9）

`backend/temples/management/commands/export_shrine_knowledge.py`

```bash
python manage.py export_shrine_knowledge <output.json>
```

Read-only。現在のDB内容を、`{name_jp, address}`をshrine identityとして
canonical seed formatへ変換する。QA fixture神社
（`temples.services.shrine_qa_fixture_exclusion.exclude_qa_fixture_shrines`が
除外する命名規約に一致する神社）にKnowledge Dataが存在する場合は
**exportを拒否する**（実運用のBatch 1〜7データに混入するのは想定外の
ため、投入元DBの調査を促す）。

Local開発DBに対して実行し、以下を取得した:

```
exported 59 sources, 41 shrines (103 deities, 85 histories) to
backend/temples/data/knowledge_seeds/batch_1_7_seed.json
```

（Section 2のFact件数と完全一致。credential・個人情報は含まれない
——公開されている神社の祭神・由緒情報のみ）

---

## 8. Local Import Test（Phase 10）

`backend/temples/data/knowledge_seeds/batch_1_7_seed.json`を、export元と
同一のlocal DBに対して`--dry-run`した結果:

```
plan summary: {'source_SKIP_EXISTS': 59, 'deity_SKIP_EXISTS': 103,
'history_SKIP_EXISTS': 85}
dry-run: OK, no DB writes performed
```

**全件`SKIP_EXISTS`、`CREATE`は0件、エラーは0件。** export→dry-run
round tripが完全に閉じており、identity解決・natural key matchingの
双方が実データで機能することを確認した。

自動テスト（`backend/temples/tests/test_knowledge_seed_import.py`、21件）
でも、合成データによるexport→wipe→import→再import（idempotency）の
round tripを含め、以下を検証済み:

- `parse_seed`の構造検証（schema_version・enum・必須field・
  `source_keys`参照）
- `resolve_shrine`のOK/NOT_FOUND/AMBIGUOUS/canonical-preferred分岐
- import各modeのDB書き込み有無
- 既存Sourceを跨いだDeity/Historyのsources relation付与
- 同一seed 2回実行での重複なし
- 曖昧shrineが1件でもあれば全体がatomicにblockされること

---

## 9. Production-Equivalent Test（Phase 11）

Production実dump（`temples 0093`適用済み、Knowledge table 5件とも
空——実際のProduction状態と完全一致）を新規取得し、隔離した
local PostgreSQL 18 + PostGISへ復元した（Productionへは一切書き込んでいない）。

| STEP | 結果 |
|---|---|
| 復元前state確認 | `temples`最新=`0093`、Knowledge 5 table=空、`shrine`=105件——想定通り |
| `--validate-only` | **初回、GEOSExceptionで失敗**（Section 5.1参照）。修正後、`OK` |
| `--dry-run` | `{'source_CREATE': 59, 'deity_CREATE': 103, 'history_CREATE': 85}`、エラー0件 |
| 適用（flagなし、この隔離DBに対してのみ） | exit 0、`sources created=59, deities created=103, histories created=85` |
| Knowledge table後件数 | `source=59`/`deity=103`/`history=85`/`deity_sources=116`/`history_sources=90` |
| 既存aggregate | `auth_user=1`/`shrine=105`/`goriyaku_relation=283`/`visit=2`/`favorite=0`——**完全不変** |
| 2回目`--dry-run`（idempotency再確認） | 全件`SKIP_EXISTS`、`CREATE`は0件 |
| `temples 0093`/`0092`/`0091`等の既存migration state | 無変更 |

この隔離DBはテスト後に削除した。**Productionには一切書き込んでいない。**

---

## 10. Dry-run Production Readiness（Phase 12）

Production credentialを使用したが、実行したのは`--validate-only`・
`--dry-run`のみ（いずれもDB書き込みなし、`transaction.atomic()`到達前に
returnする実装——Section 6参照）。

| 項目 | 結果 |
|---|---|
| `--validate-only` | `validate-only: OK, no errors` |
| `--dry-run` | `{'source_CREATE': 59, 'deity_CREATE': 103, 'history_CREATE': 85}`、エラー0件 |
| shrine identity解決 | 41神社すべて`OK`（`AMBIGUOUS`/`NOT_FOUND`は0件） |
| duplicate source conflict | 0件 |
| 期待件数とProduction-equivalent testとの一致 | 完全一致（59/103/85） |
| dry-run後のKnowledge table再確認（read-only） | `source=0`/`deity=0`/`history=0`/`deity_sources=0`/`history_sources=0`——**書き込みなしを実測確認** |
| fresh backup | dry-run直前に取得済み（`roles.sql`/`schema.sql`/`data.sql`いずれも0バイトでない、repo外保存、credential/hostname非露出） |

---

## 11. Import Acceptance Criteria（Phase 13、固定）

Production実施を検討する際の必須条件（本Foundationで全項目実測PASS）:

- [x] seed schema valid（`parse_seed`エラー0件）
- [x] 全shrine identityが一意（`AMBIGUOUS`/`NOT_FOUND`0件）
- [x] dry-run error = 0
- [x] duplicate source conflict = 0
- [x] 期待件数（Local export結果とProduction dry-run結果）が一致
- [x] isolated import（local実データ、export元DB） PASS
- [x] idempotency PASS（local実データ・production-equivalent双方で2回実行して確認）
- [x] Production-equivalent test PASS
- [x] fresh backup available

---

## 12. Recovery（Phase 14）

**Import失敗時**: `transaction.atomic()`により自動的に全rollback、
部分データは残らない（Section 6「Transaction Boundary」）。再実行は
seedまたはDB状態の問題を解消してから行う。同一seedの再実行は
idempotentなため、"どこまで通ったか"を気にせず単純に再実行してよい
——ただし、まず`--dry-run`で原因（`AMBIGUOUS`/`NOT_FOUND`/validation
error）を確認してから、である。

**Import後に論理的誤りが見つかった場合**: 本Foundationのimporterは
既存Factの内容を書き換えない（`SKIP_EXISTS`のみ、Section 6）。
訂正は以下のいずれかで行う（Production restoreを第一選択にしない）:

1. 既存のAdmin編集フロー（Batch 1〜7で確立済み、`docs/audit/
   shrine-knowledge-rollout-batch-1.md`の「Admin/Evidence Gate/Detail
   API/Recommendation selector QA」工程）で該当行を直接修正する
2. 誤って作成された行自体を削除し（Django ORM/Admin経由、対象行の
   PKのみを指定——他行への影響はCASCADE経由のM2M relationのみ）、
   seed側の内容を修正した上で再import（natural keyが変われば
   `CREATE`として新規作成される）

いずれもFact単位の局所的な操作であり、Production全体のrestoreは不要。

---

## 13. Limitations（既知の残存事項）

1. **既存Fact更新（`--allow-update`）は未実装**: 現状は新規作成のみ。
   既存Factの内容修正はSection 12の手動フロー（Admin編集）に依存する。
   将来のPRで、明示的なdiff表示を伴う更新modeを追加検討できる
2. **Source semantic identityはURL依存**: 専用field追加はschema変更を
   伴うため未実装。URL-backed Sourceは`source_type + normalized URL`で
   再利用するが、URL自体の恒久的変更・redirect先同一性は自動判定しない。
   重要metadata差または同一identity複数行はsilent reuseせず停止する
3. **address一致は完全一致**: 表記ゆれ（全角/半角等）が将来生じた場合、
   `resolve_shrine`は`name_jp`のみでの絞り込みへfallbackし、複数一致
   時は`place_ref_id IS NULL`優先ロジックへ進む。今回の41神社では
   問題は発生しなかったが、将来の神社追加時は要注意
4. **認証済みRuntime QA（Batch 1〜7で毎回実施していたAdmin一覧・
   Evidence Gate・Detail API・Recommendation selectorでの1社ごとの
   目視確認）は本Foundationのscopeに含まれない**。本Foundationが
   保証するのはDBレベルの正しさ（schema・identity・idempotency・
   aggregate不変）のみ。Production実施前に、Batch 1〜7と同水準の
   per-shrine QAを別途実施するかはMother Ship判断
5. **大量データ化時のbatching**は設計していない（現状59/103/85件
   規模を前提。将来的により大規模になった場合は別途検討）

---

## 14. Classification（Phase 15）

**`KNOWLEDGE_IMPORT_READY_WITH_LIMITATIONS`**

### READYと判断する根拠

- reproducibility gapを解消（export commandで再現可能なseedを生成、
  リポジトリへcommit）
- shrine identity戦略が実データ・production-equivalent復元DBの両方で
  41/41神社を安全に解決（`AMBIGUOUS`/`NOT_FOUND`0件）
- Production-equivalent test中に発見された0091と同クラスのschema
  drift bugを修正し、regression testで固定化した
- 全Acceptance Criteria（Section 11）が実測PASS
- Production dry-runがexpected countと完全一致、write 0件を確認

### `WITH_LIMITATIONS`とする理由

Section 13の5項目、特に既存Fact更新の未実装と、認証済みRuntime QAが
本Foundationのscope外であること。技術的な投入基盤としては閉じているが、
Batch 1〜7で実践していた「1社投入直後にQAし、問題があれば次社へ進まない」
という運用プロセスとの整合をMother Shipが判断する必要がある。

**Production Knowledge Data writeはMother Ship判断待ち。** 本セッションでは
実行していない（write 0件）。

---

## 15. Mandatory STOP

本Foundationの作成・検証をもって以下は一切開始していない:

- Production Knowledge Data write
- Batch 8
- Score/Ranking変更
- Source UI
- PER_FACT_RENDERING
