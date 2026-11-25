# Compass Current Contract Alignment

> Status: Active Audit Record
>
> 本書は、`docs/audit/compass-current-state-audit.md` で確認された現行Compass実装と既存Contractの差分を整理し、
> Current Contract Alignmentフェーズで確定した責務境界・Mother Ship Decision・未解決事項を記録する。
>
> 本書はdocs-onlyの監査記録であり、Runtime / API / Model / Migration / Ranking / Analytics event / Premium gateの挙動を変更しない。

## 1. Purpose

Current-State Audit後に確認された契約ドリフトを、現行実装へ合わせて責務単位で整理する。

本フェーズでは主に以下を扱う。

- Direction Runtime Persistence
- Weekly Presentation Persistence
- Recommendation analytics attribution
- Weekly Presentation Product Contract
- Compass Product Contractとの上下関係
- Free / Premiumの未決定境界
- Meaning Contract開始前に必要なMother Ship Decision

---

## 2. Current Persistence Boundary

現行Compassは「すべてephemeral」ではない。

責務ごとのCurrent Contractは以下である。

```text
Direction Runtime
  → ephemeral / recomputable

Weekly Presentation
  → persistent
  → owner / week / purpose / direction_fingerprint / presentation_version 単位

Recommendation Instance
  → ephemeral analytics attribution context
  → DBへ保存しない
```

Weekly Presentation SnapshotはCalculation Cacheではなく、同一Ownerの同一週におけるPresentation結果を安定して再提示するためのPersistenceである。

Weekly SnapshotはCompass HistoryまたはAnalytics Historyとして扱わない。

---

## 3. Weekly Presentation Contract Alignment

Weekly CompassはMonthly Compassを置き換える別のDirection Modelではない。

```text
Direction Time Model = MONTH
Weekly = Presentation cadence / continuity
```

Weekly専用の方位計算は持たず、既存Compass Runtime AuthorityのDirection Runtimeを再利用する。

Weekly PresentationはCompass全体の第6のtop-level Authorityではない。

`docs/product/compass-product-contract.md`が定義する既存Presentation AuthorityのWeekly specializationとして扱う。

Weekly固有の以下の責務は`docs/product/compass-weekly-presentation-contract.md`を正本とする。

- Weekly Theme
- Featured Shrine
- Owner
- Snapshot
- Reproducibility
- Weekly Fail-safe
- Weekly Persistence / Privacy boundary

---

## 4. Free / Premium Boundary

Current implementationではWeekly CompassにFree / Premium gateは存在しない。

ただし、これは将来のFree / Premium配置を決定するものではない。

```text
Current fact:
  Weekly gateなし

Product decision:
  未決定

Snapshot persistence:
  Premium価値・Entitlementの根拠とはみなさない
```

将来のPaywall / 価格 / Entitlementは別のMother Ship Decisionとする。

---

## 5. Meaning Contract Blocker Classification

Current-State Auditで残ったMother Ship Decisionのうち、Meaning Contract開始前のblockerを再分類した。

| Decision | Classification | Current handling |
|---|---|---|
| M5 `target_date` public API | NON-BLOCKER | API contract issueとして分離 |
| M6 Compass LLM Policy | BLOCKER → RESOLVED | Section 6でMother Ship Decision確定 |
| M8 Monthly recommendations allowlist | NON-BLOCKER | API boundary issueとして分離 |
| M9 Compass OpenAPI inclusion | NON-BLOCKER | API contract issueとして分離 |
| M10 display month timezone | NON-BLOCKER | Runtime / UI整合として分離 |
| M11 no_common_direction時のWeekly表示 | NON-BLOCKER | Presentation trigger decisionとして分離 |
| M12 kyusei boundary approximation | NON-BLOCKER | Calculation precision issueとして分離 |
| M13 element axis | NON-BLOCKER | Meaning Contract v1ではScope Out |

---

## 6. Mother Ship Decision — M6 Compass LLM Policy

> Decision: **NO_LLM**
>
> Status: **RESOLVED**
>
> Decision Owner: Mother Ship

### 6-1. Decision

CompassではLLMを使用しない。

現行Compass Product Contract上、LLMは以下の責務を持たない。

- Direction calculation
- Traditional meaning mapping
- Meaning synthesis
- Recommendation candidate selection
- Recommendation ranking
- Recommendation score
- Recommendation Reason generation
- Shrine Knowledge generation
- Weekly Theme generation
- Compass user-facing expression generation

CompassのCalculation / Mapping / Synthesis / Presentationは、LLMをAuthorityとして前提にしない。

### 6-2. Current Implementation Gap

現行共有Recommendation経路には、Concierge用の`CONCIERGE_USE_LLM`設定が存在する。

現行コードでは、`build_chat_recommendations()`が`CONCIERGE_USE_LLM`を参照し、
`resolve_llm_route()`を通じて`ConciergeOrchestrator().suggest()`へ到達し得る。

Compassはこの共有Recommendation経路を再利用しているため、Concierge側で`CONCIERGE_USE_LLM=1`となった場合、
CompassもLLM経路へ入る可能性が残っている。

これはCompass Product Policyではない。

Classification:

```text
Product Policy:
  NO_LLM

Current implementation:
  latent shared LLM route exists

Status:
  IMPLEMENTATION GAP
```

### 6-3. Authority Boundary

`CONCIERGE_USE_LLM`はCompassのLLM Authorityではない。

Concierge用feature flagの値によって、CompassのMeaning / Recommendation / Presentation挙動が暗黙に変更されてはならない。

Compass用のLLM feature flagを新設して「OFFにする」ことを本Decisionは要求しない。

CompassではLLMを使わないため、後続実装ではCompass経路がLLM routeへ入らない境界を明示的に保証する。

### 6-4. Current Alignment PR Boundary

Current Contract Alignment PRではRuntime codeを変更しない。

したがって本PRでは、

- `CONCIERGE_USE_LLM`を削除しない
- Compass専用feature flagを追加しない
- `resolve_llm_route()`を変更しない
- Recommendation実装を変更しない
- LLM testを追加しない

M6 Decisionと現行Implementation Gapの記録のみを行う。

Runtimeの遮断実装は別PRとする。

### 6-5. Meaning Contract Gate

M6はMeaning Contract開始前の唯一のblocking decisionだった。

`NO_LLM`確定により、Meaning Contractは以下を前提として設計できる。

```text
Calculation
  ↓
Traditional Mapping
  ↓
Synthesis
  ↓
Expression

LLM Authority = NONE
```

同一input + 同一source/rules/versionから、同一Calculationおよび同一Meaning candidate setへ到達できる再現可能な設計を前提とする。

M6 Decision確定により、Meaning Contract開始前のblockerは解消された。

---

## 7. Current PR Scope Classification

Current Contract Alignment PRで扱うもの:

- Direction Runtime Persistence contract alignment
- Weekly Presentation Persistence contract alignment
- Compass Analytics persistence boundary alignment
- Weekly Presentation Product Contract
- Compass Product ContractからWeekly Contractへの責務委譲
- Free / Premium未決定境界の維持
- M6 NO_LLM Mother Ship Decisionの記録

Current PRで扱わないもの:

- M5 `target_date` API変更
- M8 Monthly recommendation field allowlist
- M9 OpenAPI追加
- M10 timezone挙動変更
- M11 Weekly trigger変更
- M12 kyusei計算精緻化
- M13 element axis変更
- Compass LLM routeのRuntime遮断
- 新Analytics event
- E2E / determinism test追加
- Premium gate実装

---

## 8. Follow-up

Current Contract Alignment完了後、Meaning Contractへ進む。

Meaning Contractでは少なくとも以下を分離する。

```text
Calculation
Traditional Mapping
Synthesis
Expression
```

LLMをMeaning Authorityとして使用しない。

element / astro_priorityはM13未決定のため、Meaning Contract v1のMeaning SourceからScope Outする。

---

## 更新ルール

- 本書はCurrent Contract Alignment時点の監査判断とMother Ship Decisionを記録する。
- Product Contract・Runtime Contract・Analytics Contractの正本文言を本書で重複管理しない。
- 実装変更が発生した場合は、該当する正本Contractと実装テストを優先して更新する。
- M6を将来変更する場合は、新しいMother Ship Decisionを明示的に作成し、本書の記録を黙って上書きしない。
