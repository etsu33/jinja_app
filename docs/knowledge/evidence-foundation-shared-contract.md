> **Status: Active（PR-F1 Shared Contracts + PR-F2 HistoryThemeAssignment + PR-F3 ShrineGoriyakuAssignment + PR-F3b Goriyaku canonical registry v1）**
>
> 本書は、Evidence Foundation の Shared Evidence Foundation Contract（PR-F1）と、その具体的assignmentモデルである HistoryThemeAssignment（PR-F2）・ShrineGoriyakuAssignment（PR-F3）の責務を記録する。
>
> Evidence Foundationは現時点でRecommendation / Ranking / Concierge / Premium / Readiness判定のいずれにも接続されていない。既存の`Shrine.history_theme` / `Shrine.goriyaku_tags` / `GoriyakuTag.id`は本書の対象外であり、変更されていない。

# Evidence Foundation Shared Contract

## 目的

Evidence Qualification・Source Evidence・Meaning接続の基礎となる、Evidence Foundationの共有契約層（Qualification Contract / Taxonomy Contract / Provenance Contract）と、その上に構築されるdomain assignmentモデル（HistoryThemeAssignment、ShrineGoriyakuAssignment）を定義する。

本書が扱うのはPR-F1（Shared Contracts）・PR-F2（HistoryThemeAssignment）・PR-F3（ShrineGoriyakuAssignment schema foundation）で実装した範囲のみ。Source Evidence Link・normalized_evidence transportは、いずれも将来PR（F4〜F5）で追加される別責務であり、本書では扱わない。

---

## 実装

`backend/temples/domain/evidence_qualification.py`（PR-F1）
`backend/temples/domain/evidence_taxonomy.py`（PR-F1）
`backend/temples/domain/evidence_provenance.py`（PR-F1）
`backend/temples/domain/history_theme_taxonomy_v1.py`（PR-F2）
`backend/temples/domain/goriyaku_taxonomy_v1.py`（PR-F3）
`backend/temples/models.py`（`HistoryThemeAssignment` PR-F2、`ShrineGoriyakuAssignment` PR-F3）
`backend/temples/admin.py`（`HistoryThemeAssignmentAdmin`/`Inline` PR-F2、`ShrineGoriyakuAssignmentAdmin`/`Inline` PR-F3）

PR-F1の3ファイルはpure Pythonの契約・判定ロジックであり、DB modelを持たない（PR-F1ではmigrationを発生させていない）。PR-F2・PR-F3はそれぞれ1つの具体的Django modelを追加し、additiveなmigration（通常lineage・NoGIS lineageの両方）を伴う（下記参照）。

---

## EvidenceQualification Contract

Evidenceが「採用可能か」を、以下5次元すべてを満たす場合のみ`qualified=True`とする。

- identifiable（Assignment Identity）
- taxonomy_stable（Controlled Taxonomy）
- provenance_satisfied（Assignment Provenance）
- semantic_assignment_traceable（Semantic Assignment Rationale）
- transport_traceable（Transport Integrity）

判定は`evaluate_evidence_qualification()`が行う。同じ入力に対して常に同じ結果を返すpure deterministic判定であり、LLM・random・現在時刻・DB状態・外部APIには一切依存しない。

重要（変更不可の前提）:

```text
semantic value exists != Qualified Evidence
Qualified Evidence != Relationship Origin ALLOW
```

`EvidenceQualification`が`true`であることは、その値がRelationship Origin・Recommendationの入力として使ってよいことを意味しない。この判定は、あるEvidenceが「Evidence Foundationの土台として扱える状態にあるか」だけを表す。

---

## Taxonomy Contract

taxonomyはDB正本ではなく、code-level versioned registryとして扱う。

登録済みnamespace（`backend/temples/domain/evidence_taxonomy.py`）:

- `history_theme`
- `goriyaku`

canonical semantic keyの形式は`<namespace>:<key>`（例: `history_theme:<key>`, `goriyaku:<key>`）。`validate_canonical_semantic_key()`がformat（namespace + separator + 非空key）のみを検証する。

**PR-F1時点でのscope境界**:

- 実際に有効なcanonical key一覧（例: `history_theme:再出発`に対応する実際のkey文字列）は、本PR（PR-F1）では一切定義していない。history_theme側はPR-F2で7値を確定済み。goriyaku側は、PR-F3でschema/registryの**構造**（`backend/temples/domain/goriyaku_taxonomy_v1.py`）のみを追加し、既存GoriyakuTag 46件へのcanonical key対応表は意図的に未定義のまま（DATA_REVIEW事項、下記「ShrineGoriyakuAssignment（PR-F3）」節参照）。
- key part（`:`より後ろ）の文字種ルールは、既存taxonomy実態（日本語ラベル、一部「・」区切りの複合語）を踏まえ、ASCII限定regexへ意図的に固定していない。文字種ルールの最終決定もHOLD事項。
- namespaceごとのtaxonomy versionは、両方ともbaseline値`"v1"`から開始する（既存taxonomy内容の再設計ではなく、versioning infrastructureの初期値）。taxonomy versionはMother Ship FINAL contractに従い文字列表現のみを正とし、整数表現は存在しない（PR-F2で修正済み。詳細は「HistoryThemeAssignment（PR-F2）」節のShared Contract Correctionを参照）。

---

## Provenance Contract

`producer`（誰/何が生成したか）と`mechanism`（どの管理された処理によってassignmentが作られたか）を区別する。値はMother Ship FINALをそのまま実装し、既存`ShrineKnowledgeSource.SOURCE_TYPE_CHOICES`等からの再推論・簡略化はしていない（格納表現のみ本repositoryのlowercase snake_case規約に合わせた）。

- producer（Mother Ship FINAL）: `ADMIN` / `CURATOR` / `MIGRATION` / `VERIFIED_IMPORT` / `CONTROLLED_AUTOMATION`（格納値: `admin` / `curator` / `migration` / `verified_import` / `controlled_automation`）
- mechanism（Mother Ship FINAL v1）: `MANUAL_REVIEW` / `SOURCE_BACKED_IMPORT` / `VERIFIED_MIGRATION` / `CONTROLLED_RULE`（格納値: `manual_review` / `source_backed_import` / `verified_migration` / `controlled_rule`）

想定される組み合わせ例（Mother Ship提示、v1では組み合わせの妥当性チェックは行わない）:

```text
MIGRATION + VERIFIED_MIGRATION
VERIFIED_IMPORT + SOURCE_BACKED_IMPORT
CONTROLLED_AUTOMATION + CONTROLLED_RULE
```

重要: これらの組み合わせは、それだけでEvidenceQualificationの`qualified=True`を意味しない。qualificationは引き続き5次元すべてを要求する。producer/mechanismは`provenance_satisfied`という1次元への入力候補になり得るだけで、`evidence_provenance.py`自体はqualification判定に関与しない。

`EvidenceProvenance`（`producer` / `mechanism` / `assigned_at`）はpure Python dataclassであり、Django abstract modelではない。F2/F3の実際のDB model設計時に、このfield構成を再利用することを想定しているが、DB化自体は別PRのscope。

---

## HistoryThemeAssignment（PR-F2）

`HistoryThemeAssignment`は、1神社に対する1つのhistory_theme意味的assignmentを、追跡可能な形で保持する最初のEvidence Foundation domain model。

### 既存Shrine.history_themeとの分離

Mother Ship FINAL:

- `Shrine.history_theme` = 既存compatibility / 現行read path（Recommendation / Rankingが引き続き参照する）
- `HistoryThemeAssignment` = Evidence Foundation qualification path

両者は独立して共存する。`HistoryThemeAssignment`の作成・更新は`Shrine.history_theme`を一切書き換えず、`Shrine.history_theme`の変更も`HistoryThemeAssignment`を自動生成しない。NO BACKFILL・NO AUTO-SYNCが両方向で確定事項。

### Shared Contract Correction（PR-F1 TaxonomyVersion）

PR-F1の`evidence_taxonomy.TaxonomyVersion.version`は、実装時点では整数`1`として実装されていた。しかしMother Ship FINAL Evidence Foundation contractでは`taxonomyVersion`は文字列（例: `"v1"`）であり、将来のnormalized Evidence transport（PR-F5）が定義する`taxonomyVersion: string`とも一致する必要がある。

PR-F2がtaxonomy versionを初めてDBへ永続化するPRであるため、このPRで是正した。是正が可能だった根拠:

- PR-F1の`TaxonomyVersion`はpure Pythonであり、PR-F1自体はDB modelもmigrationも持たなかった
- そのためデータマイグレーションは不要（永続化された行が一件も存在しない）
- `evidence_taxonomy.py`はPR-F1時点で本番のRecommendation / Ranking / Concierge のいずれからもimportされていなかった（PR-F1完了時点で確認済み）ため、ランタイム挙動への影響もない
- PR-F2のmigrationはまだpush/適用されていなかったため、`IntegerField`として一度でも永続化された履歴を残さず、最初から`CharField`として1本のCreateModelにまとめられる

是正内容: `TaxonomyVersion.version`を`int`から`str`へ変更し、`history_theme` / `goriyaku`両namespaceのcurrent versionを`1`から`"v1"`へ変更した。整数⇄文字列の変換ヘルパーは追加していない（Foundation全体で単一の文字列表現のみを正とする）。

### Taxonomy v1（namespace: `history_theme`、version: `"v1"`）

PR-F1のformat validator（`evidence_taxonomy.validate_canonical_semantic_key()`）を再利用し、`backend/temples/domain/history_theme_taxonomy_v1.py`で以下7値のみを登録する（goriyaku taxonomyはPR-F2で一切登録しない）。

| 日本語表示値 | canonical key |
|---|---|
| 再出発 | `history_theme:restart` |
| 静寂 | `history_theme:stillness` |
| 復興 | `history_theme:restoration` |
| 勝負 | `history_theme:challenge` |
| 縁 | `history_theme:connection` |
| 学び | `history_theme:learning` |
| 守り | `history_theme:protection` |

canonical keyが機械識別子。日本語ラベルは表示値に過ぎず、identityとしては使用しない。未知のnamespace・未知のkey・不正なtaxonomy version・空keyは、モデルの`clean()`でfail-safeにrejectされる（fuzzy normalization・自動推定は行わない）。

### Lifecycle

`ACTIVE` / `SUPERSEDED`の2状態のみ（v1）。GoriyakuTagは将来別のlifecycle語彙（`ACTIVE`/`REVOKED`）を持つ予定であり、意図的に共通化していない。

DB制約: `UNIQUE(shrine) WHERE lifecycle = 'ACTIVE'`（PostgreSQL partial unique constraint、`uniq_history_theme_assignment_active_per_shrine`）。1神社につき同時にACTIVEになれるassignmentは最大1件。SUPERSEDEDは同一神社に何件あってもよい。

PR-F2では自動supersede処理を実装しない。lifecycle変更は常に明示的な値指定によって行われる（signal・save()内での暗黙変換なし）。

### Provenance

PR-F1の`evidence_provenance.EVIDENCE_PRODUCERS` / `EVIDENCE_MECHANISMS`をそのまま`choices`として再利用する（第二のenumを作らない）。`producer` / `mechanism` / `assigned_at`はモデルの必須fieldであり、値は呼び出し側が明示的に指定する（admin inlineでの暗黙生成なし）。

`created_at`（DB行の作成時刻）と`assigned_at`（provenance上の意味的assignment時刻）は責務が異なるfieldとして分離している。

### Qualified Evidenceではない

`HistoryThemeAssignment`はPR-F2単体では**Qualified Evidenceにならない**。Source Evidence link・rationaleはPR-F4のscopeであり、PR-F2には存在しない。`producer=MIGRATION`かつ`mechanism=VERIFIED_MIGRATION`のようなprovenanceが揃っていても、それだけでqualification（`evidence_qualification.evaluate_evidence_qualification()`の5次元判定）がTrueになることはない。

### 既存データとの関係

既存105神社の`Shrine.history_theme`データからの自動backfillは行わない。既存の`HISTORY_THEME_SEED`（`seed_history_theme.py`）等の値を、`producer=MIGRATION`のような信頼済みprovenanceへ自動変換することもしない。したがって、このPRの直後は105神社すべてが`HistoryThemeAssignment`を0件持つ状態が正しい。

`ShrineReflection.history_theme` / `ActionEvent.history_theme`（過去のスナップショット）も同様にbackfillしない。

---

## ShrineGoriyakuAssignment（PR-F3）

`ShrineGoriyakuAssignment`は、神社のご利益（goriyaku）semantic assignmentを、Evidence Foundation上で将来Qualified Evidenceとして扱えるようにするための器（schema foundation）。PR-F3ではschemaのみを追加し、実際にAssignment行を作成できる状態にはしない（下記「Fail-Closed」参照）。

### 既存Shrine.goriyaku_tagsとの分離

- `Shrine.goriyaku_tags`（既存M2M） = Recommendation Signal / compatibility layer。`NEED_TO_GORIYAKU_IDS`・`matched_by_gid`/`matched_by_tag`/`matched_by_user_selected_gid`（`concierge_chat_ranking.py`）が引き続き参照する。
- `ShrineGoriyakuAssignment`（新規） = Evidence Foundation / Qualified Evidence preparation layer。

両者は接続しない。`Shrine.goriyaku_tags`をthrough modelへ変更しない。どちらの方向にも自動生成・自動同期を行わない。PR-F3はこの2層の分離を確定させることのみを目的とし、Recommendation / Ranking / Concierge / Compassのコードは一切変更していない。

### Mother Ship Decisions（PR-F3設計ゲートで確定、FINAL）

- **Decision 1（Canonical Key）= Option B**: PR-F3ではAssignment schemaのみ実装し、既存GoriyakuTag 46件への具体的canonical key（`goriyaku:<stable_key>`）対応は後続DATA_REVIEWへ分離する。
- **Decision 2（Duplicate Handling）= Option B**: 既存GoriyakuTagのduplicate / near-duplicateはPR-F3では一切解決しない（normalization・merge・alias作成・synonym inference・rename・delete・ID変更のいずれも禁止）。判断は後続DATA_REVIEWで行う。
- **Decision 3（Legacy Governance）= Option C**: legacy goriyaku taxonomy（`GoriyakuTag`・`GoriyakuTagAdmin`・`backfill_goriyaku_tags.py`・`ShrineAdmin.filter_horizontal`・`NEED_TO_GORIYAKU_IDS`・Recommendation/Ranking挙動）はPR-F3では一切変更しない。将来のGovernance PRとしてHOLD・ロードマップ化し、MVP必須とはしない。

### Taxonomy v1（namespace: `goriyaku`、version: `"v1"`）

`backend/temples/domain/goriyaku_taxonomy_v1.py`が、PR-F1のformat validator（`evidence_taxonomy.validate_canonical_semantic_key()`）を再利用したregistryを提供する（`history_theme_taxonomy_v1.py`と同型）。

**Canonical registry: PR-F3では未投入（空・fail-closed）だったが、PR-F3bでProduction canonical master 39件をMother Ship FINALとして投入済み。** DATA_REVIEWはこの39件の範囲で完了している。

- 母集団はProduction canonical master **39件**。local dev DBにのみ存在するlegacy 7件（`子宝・安産` / `金運・商売繁盛` / `仕事運・出世` / `厄除け・方除け` / `勝運・必勝祈願` / `地域安泰` / `開運招福`）は**registry対象外**。
- **39 concept → 39 canonical identity**を維持する。semantic merge・alias・synonym inferenceは行わない。表記が近い概念（`八方除`=`goriyaku:happo_jo` と `八方除け`=`goriyaku:happo_yoke`、`芸能` と `芸能運`、`健康長寿` と `延命長寿` 等）は別identityとして保持する。
- canonical keyがimmutable identityであり、日本語ラベルはdisplay valueに過ぎない。`GoriyakuTag.id`はbackfill順に依存する不安定な値のため、identityとして使用しない。
- registryの正本はcode-level versioned registry（このモジュール）であり、DBではない。taxonomy用のDB tableは作らない。

### Fail-Closed（重要）

registryは**closed vocabulary**であり、`ShrineGoriyakuAssignment.clean()`は登録済み39件の`goriyaku:<key>`のみを受理する。未登録キーは常にreject（`reason="unknown_goriyaku_key"`）される。「formatが正しければ許可する」は実装していない — formatの正しさはregistry登録の代替にならない。

PR-F3の「registryが空なので何も受理しない」状態から、PR-F3bで「登録済み39件のみ受理する」状態へ移行した。fail-closedの性質自体は変わっていない。

### Lifecycle

`ACTIVE` / `REVOKED`の2状態のみ（v1）。HistoryThemeAssignmentの`SUPERSEDED`語彙はコピーしていない — goriyakuは1神社が複数ご利益を同時に持てる（多対多的な）性質のため、「置き換え」ではなく「取り消し」を表すREVOKEDを採用した。

DB制約: `UNIQUE(shrine, canonical_key, taxonomy_version) WHERE lifecycle = 'ACTIVE'`（PostgreSQL partial unique constraint、`uniq_goriyaku_assignment_active_per_shrine_tag_version`）。同一神社×同一canonical_key×同一taxonomy versionにつき、同時にACTIVEになれるassignmentは最大1件。REVOKED historyは同一神社に何件あってもよい。

PR-F3では自動revoke処理を実装しない。既存ACTIVEのsilent replacementも行わない。lifecycle変更は常に明示的な値指定によって行われる。

### Provenance

PR-F1の`evidence_provenance.EVIDENCE_PRODUCERS` / `EVIDENCE_MECHANISMS`をそのまま`choices`として再利用する（第二のenumを作らない、HistoryThemeAssignmentと同じ構成）。`producer` / `mechanism` / `assigned_at`はモデルの必須fieldであり、値は呼び出し側が明示的に指定する。

### Admin

`ShrineGoriyakuAssignmentAdmin`（標準登録）と`ShrineGoriyakuAssignmentInline`（`ShrineAdmin.inlines`へadditiveに追加）を用意した。既存`ShrineAdmin.filter_horizontal = ("goriyaku_tags",)`には一切触れていない。Admin経由でも同じserver-side validationが働くため、未登録canonical keyはAdminからも保存できない。

### Qualified Evidenceではない

`ShrineGoriyakuAssignment`はPR-F3単体では**Qualified Evidenceにならない**。Source Evidence link・rationaleはPR-F4のscope（HOLD）。normalized_evidence transportはPR-F5のscope（HOLD）。producer/mechanismが揃っていても、それだけでqualification（`evidence_qualification.evaluate_evidence_qualification()`の5次元判定）がTrueになることはない。

### 既存データとの関係

既存GoriyakuTag・`Shrine.goriyaku_tags`データからの自動backfillは行わない。Data migrationも一切実装していない（PR-F3のschema onlyのmigrationのみ。PR-F3bはmigrationを追加していない）。registryへ39件が登録された後も、`ShrineGoriyakuAssignment`行は明示的に作成されない限り0件のままであり、既存M2Mから自動生成されることはない。

### 未解決事項

- canonical key registry population: **PR-F3bで解決済み**（Production 39件）
- duplicate / near-duplicate統合判定: 未実施。39 concept → 39 identityとして分離保持しており、統合するか否かの判断自体が将来課題（統合は現時点で明示的に禁止）
- Legacy taxonomy governance（`GoriyakuTag` / `GoriyakuTagAdmin` / `backfill_goriyaku_tags.py` / `NEED_TO_GORIYAKU_IDS`）: Future Governance PR（HOLD、MVP必須ではない）
- local dev DBのlegacy 7件とProduction 39件の環境差（`DEV_DB_PK_DRIFT`）: registry対象外として据え置き

---

## EvidenceLink（PR-F4）

`EvidenceLink`は、許可されたSemantic Assignmentと、その根拠となるStored Factの
exact edgeをrationale付きで永続化する。F4 v1のallowlistは次の4組だけである。

```text
HistoryThemeAssignment   → ShrineHistory | ShrineDeity
ShrineGoriyakuAssignment → ShrineHistory | ShrineDeity
```

単一の明示的Django modelを使用し、GenericForeignKey / ContentType、pair別model、
Assignment共通基底modelは使用しない。Assignment FKはexactly oneかつCASCADE、Fact FKは
exactly oneかつPROTECTである。`rationale`は必須で、DBは空文字を拒否し、model validationは
strip後の空文字も拒否する。4つのpartial unique constraintにより、rationaleが異なっても
同じAssignment × Fact edgeの重複を許可しない。

Same-Shrineの正式条件は、選択されたAssignmentとStored Factの`shrine_id`一致である。
cross-table CheckConstraintやtriggerは追加せず、`EvidenceLink.clean()`とF4 preparation時の
structural revalidationでfail closedにする。通常の`save()`は必ず`full_clean()`を通り、
bulk write用の迂回経路は提供しない。

Assignmentの`ACTIVE → SUPERSEDED` / `ACTIVE → REVOKED`はhard deleteではないため、Link、
rationale、Fact、Sourceを保持する。旧Linkを新しいACTIVE Assignmentへ自動コピーしない。
Assignment hard deleteはLinkへCASCADEするが、参照中のFact hard deleteはPROTECTする。

### F4 predicatesとpreparation

- structural validity: persisted Link identity、exactly-one selectors、C-1 allowlist、relation解決、
  Same-Shrine、nonblank string rationaleをDB非依存snapshot上で判定する。
- Fact / Source Quality: 既存`KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES`を正本とし、Factがready、
  かつready Sourceが最低1件ある場合だけPASS。複数Factは全件PASS必須。0件は
  `NOT_APPLICABLE`であり、PASSへ読み替えない。confidenceは使わない。
- `semantic_assignment_traceable`: AssignmentにLinkが1件以上あり、全Linkがstable identityを持つ
  exact edgeとしてnonblank rationaleを再取得できる場合だけtrue。0件はfalseだがstructural
  corruptionではない。Same-ShrineやQualityはこのpredicateへ混ぜない。
- F4 preparation: ACTIVE lifecycle、structural、Qualityをprerequisiteとして別々に追跡し、
  `identifiable` / `taxonomy_stable` / `provenance_satisfied` /
  `semantic_assignment_traceable`の4 dimensionを準備する。taxonomyとprovenanceはF1〜F3の
  validator / builderをそのまま再利用する。BUILD BLOCKとdimension falseは別状態で保持する。

F4 production codeはRecommendation / Ranking / Concierge / Compassへ接続しない。また、
`transport_traceable`を仮値でも算出せず、最終`EvidenceQualificationInput`を作らず、
`evaluate_evidence_qualification()`を呼ばない。normalized Evidence transportはPR-F5に残す。

---

## 責務境界

- 本書はEvidence Foundationの共有契約層（Qualification / Taxonomy / Provenance）と、HistoryThemeAssignment（PR-F2）・ShrineGoriyakuAssignment（PR-F3）の責務を管理する。
- Source Evidence LinkはPR-F4の上記契約を正本とする。normalized transportのAPI契約はPR-F5で別途文書化する。
- goriyaku canonical key registryの具体的内容（46件対応表）、duplicate/near-duplicate判定、legacy taxonomy governanceは、いずれも後続のDATA_REVIEW / Governance PRで別途文書化する。本書はPR-F3時点でこれらが「未確定である」という事実のみを記録する。
- 既存の`docs/knowledge/shrine-knowledge-contract.md`（`ShrineKnowledgeSource` / `ShrineDeity` / `ShrineHistory`のSource契約）はEvidence Foundationとは独立した既存正本であり、本書はその内容を変更しない。
