> **Status: Active（PR-F1 Shared Contracts + PR-F2 HistoryThemeAssignment）**
>
> 本書は、Evidence Foundation の Shared Evidence Foundation Contract（PR-F1）と、その最初の具体的assignmentモデルであるHistoryThemeAssignment（PR-F2）の責務を記録する。
>
> Evidence Foundationは現時点でRecommendation / Ranking / Concierge / Premium / Readiness判定のいずれにも接続されていない。既存の`Shrine.history_theme` / `Shrine.goriyaku_tags` / `GoriyakuTag.id`は本書の対象外であり、変更されていない。

# Evidence Foundation Shared Contract

## 目的

Evidence Qualification・Source Evidence・Meaning接続の基礎となる、Evidence Foundationの共有契約層（Qualification Contract / Taxonomy Contract / Provenance Contract）と、その上に構築される最初のdomain assignmentモデル（HistoryThemeAssignment）を定義する。

本書が扱うのはPR-F1（Shared Contracts）とPR-F2（HistoryThemeAssignment）で実装した範囲のみ。ShrineGoriyakuAssignment・Source Evidence Link・normalized_evidence transportは、いずれも将来PR（F3〜F5）で追加される別責務であり、本書では扱わない。

---

## 実装

`backend/temples/domain/evidence_qualification.py`（PR-F1）
`backend/temples/domain/evidence_taxonomy.py`（PR-F1）
`backend/temples/domain/evidence_provenance.py`（PR-F1）
`backend/temples/domain/history_theme_taxonomy_v1.py`（PR-F2）
`backend/temples/models.py`（`HistoryThemeAssignment`、PR-F2）
`backend/temples/admin.py`（`HistoryThemeAssignmentAdmin` / `HistoryThemeAssignmentInline`、PR-F2）

PR-F1の3ファイルはpure Pythonの契約・判定ロジックであり、DB modelを持たない（PR-F1ではmigrationを発生させていない）。PR-F2は`HistoryThemeAssignment`という最初の具体的Django modelを追加し、1件のadditiveなmigrationを伴う（下記参照）。

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

- 実際に有効なcanonical key一覧（例: `history_theme:再出発`に対応する実際のkey文字列）は、本PRでは一切定義していない。既存canonical値（`docs/product/history-theme-taxonomy.md`の7カテゴリ、GoriyakuTagの39〜46件の名称）をcanonical keyへどう対応させるかはMother Ship未確定のHOLD事項であり、F2/F3で扱う。
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

## 責務境界

- 本書はEvidence Foundationの共有契約層（Qualification / Taxonomy / Provenance）と、HistoryThemeAssignment（PR-F2）の責務を管理する。
- `ShrineGoriyakuAssignment`のモデル設計、Source Evidence Linkの実装、normalized transportのAPI契約は、将来PR（F3〜F5）ごとに別途文書化する。
- 既存の`docs/knowledge/shrine-knowledge-contract.md`（`ShrineKnowledgeSource` / `ShrineDeity` / `ShrineHistory`のSource契約）はEvidence Foundationとは独立した既存正本であり、本書はその内容を変更しない。
