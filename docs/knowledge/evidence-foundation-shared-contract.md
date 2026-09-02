> **Status: Active（PR-F1、Shared Contracts のみ）**
>
> 本書は、Evidence Foundation の Shared Evidence Foundation Contract（PR-F1で追加した共有契約層）の責務のみを記録する。
>
> Evidence Foundationは現時点でRecommendation / Ranking / Concierge / Premium / Readiness判定のいずれにも接続されていない。既存の`Shrine.history_theme` / `Shrine.goriyaku_tags` / `GoriyakuTag.id`は本書の対象外であり、変更されていない。

# Evidence Foundation Shared Contract

## 目的

Evidence Qualification・Source Evidence・Meaning接続の基礎となる、Evidence Foundationの共有契約層（Qualification Contract / Taxonomy Contract / Provenance Contract）を定義する。

本書が扱うのはPR-F1（Shared Contracts）で実装した範囲のみ。HistoryThemeAssignment・ShrineGoriyakuAssignment・Source Evidence Link・normalized_evidence transportは、いずれも将来PR（F2〜F5）で追加される別責務であり、本書では扱わない。

---

## 実装

`backend/temples/domain/evidence_qualification.py`
`backend/temples/domain/evidence_taxonomy.py`
`backend/temples/domain/evidence_provenance.py`

いずれもpure Pythonの契約・判定ロジックであり、DB modelを持たない。PR-F1ではmigrationを発生させていない。

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
- namespaceごとのtaxonomy versionは、両方ともbaseline値`1`から開始する（既存taxonomy内容の再設計ではなく、versioning infrastructureの初期値）。

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

## 責務境界

- 本書はEvidence Foundationの共有契約層（Qualification / Taxonomy / Provenance）のみを管理する。
- `HistoryThemeAssignment` / `ShrineGoriyakuAssignment`のモデル設計、Source Evidence Linkの実装、normalized transportのAPI契約は、将来PR（F2〜F5）ごとに別途文書化する。
- 既存の`docs/knowledge/shrine-knowledge-contract.md`（`ShrineKnowledgeSource` / `ShrineDeity` / `ShrineHistory`のSource契約）はEvidence Foundationとは独立した既存正本であり、本書はその内容を変更しない。
