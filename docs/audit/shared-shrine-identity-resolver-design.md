# Shared Frontend Shrine Identity Resolver — Design Record (F-3)

## Status

```text
F3_STATUS      = DESIGNED
RUNTIME_CHANGE = NONE
```

- Recorded at: `2026-09-23`
- Type: **design / contract only.** The resolver is **not implemented** and no
  consumer is migrated.
- Follow-up: `F-3` from `docs/audit/shrine-identity-compass-concierge-contract.md` §8
- Verified against `develop` @ `21554d9` (after `R-5` #2955 / `F-1` #2956)
- Implementation + migration ownership: `F-4`

本書は実装しない。`F-4` が実装と移行を行う。

## 1. Why a shared resolver

```text
SHRINE_IDENTITY_AUTHORITY = Shrine.id
PUBLIC_IDENTITY_KEY       = shrine_id
```

Compass Monthly の identity chain は `R-3` / `R-4` / `R-5` / `F-1` で完結した。
一方、frontend 全体の identity 解決は依然として分散しており、同じ問いに対して
最低5通りの異なる優先順位が存在する（§7）。

`pickShrineId`（`detailHref.ts`）のように generic `id` を意図的に除外している
実装もあれば、`shrine_id ?? id` のように identity authority へ昇格させている
実装もある。1箇所に集約しないかぎり、この不一致は再発し続ける。

```text
SHARED_FRONTEND_SHRINE_IDENTITY_RESOLVER
= ONE IMPLEMENTATION
= EXPLICIT POLICY
= FAIL_CLOSED_ON_CONFLICT
```

### 1.1 Why the policy argument is mandatory

共有化の最大のリスクは、**Compass Monthly が `shrine_id only` から
compatibility-fallback 契約へ引き戻されること**である。

policy を省略可能にすると、Compass が暗黙に compat 側へ落ちる余地が生まれる。
そのため policy は **必須引数** とし、既定値を持たせない。`R-5` の
`require_shrine_id` が keyword-only かつ既定値なしである理由と同じ設計判断。

## 2. Resolver contract

```text
resolveShrineId(
  input: unknown,
  policy: "public_strict" | "registered_compat"
): number | null
```

```text
input   : unknown（呼び出し側の型に依存しない。非objectは null）
policy  : 必須。既定値なし。
return  : 正の整数、または null
throw   : しない（fail-closed は null で表現する）
```

`null` は「このinputからは Shrine identity を確定できない」を意味する。
呼び出し側は従来どおり `== null` guard で分岐する。

## 3. Two policies

### 3.1 `public_strict`

```text
PUBLIC_STRICT_ALLOWED_FIELDS = shrine_id
```

alias fallback は**一切ない**。

```text
intended consumers:
  Compass Monthly、および shrine_id を保証する public contract 全般
```

`R-3`（Public Projection の fail-closed）・`R-4`（OpenAPI required/non-null）・
`R-5`（frontend 型 non-optional）が揃っている面は、compat alias を必要としない。

### 3.2 `registered_compat`

```text
REGISTERED_COMPAT_ALLOWED_FIELDS = shrine_id, shrineId, shrine.id
```

互換順序:

```text
1. shrine_id
2. shrineId
3. shrine.id
```

```text
intended consumers:
  public contract が未だ tighten されていない legacy / 互換 Concierge frontend 経路
```

この3つは `detailHref.ts` の `pickShrineId` が既に採用している集合と同一であり、
新しい互換性を導入するものではない。既存の最も厳格な互換実装を正本化する。

## 4. Prohibited identity sources (both policies)

```text
GENERIC_ID_ALLOWED  = NO
PLACE_ID_ALLOWED    = NO
NAME_ALLOWED        = NO
COORDINATE_ALLOWED  = NO
ANCHOR_ALLOWED      = NO
```

```text
禁止:
  id            generic recommendation id
  place_id / placeId / place.id
  name
  address
  coordinates（latitude / longitude）
  Canonical Anchor
  Navigation Anchor
```

generic `id` を Shrine identity authority にしてはならない。これは `R-2`（#2952）
の決定であり、`F-1`（#2956）が Compass で実行した内容でもある。

`place_id` は **F-3 のスコープ外**。shadow identity の問題は `F-6` が扱う
（`docs/audit/shrine-identity-compass-concierge-contract.md` §5 / §8 F-6）。
本resolverが place_id を受理しない、という点のみをここで確定する。

Anchor 類が禁止なのは Gate C の分離規則による——identity は「どの神社か」、
Anchor は「どこか」であり、Anchor の変更が identity を変えてはならない
（`docs/audit/canonical-shrine-anchor-gate-c-decision-record.md` §4）。

## 5. Normalization contract

```text
A valid Shrine id is a POSITIVE INTEGER.
```

```text
ACCEPT
  42        -> 42
  "42"      -> 42

REJECT (-> null)
  0
  negative numbers            (-1)
  floats                      (1.5, "1.5")
  blank / whitespace strings  ("", "   ")
  non-numeric strings         ("abc", "42abc")
  NaN / Infinity / -Infinity
  null / undefined
  boolean                     (true は数値化すると 1 になるため明示的に拒否)
```

`boolean` の明示的拒否は追加の慎重策である。JS では `Number(true) === 1` となり、
`true` が Shrine id 1 に化けうる。既存の backend 側 `_candidate_shrine_id`
（`concierge_chat_candidates.py`）も同じ理由で `isinstance(value, bool)` を
先に弾いている。frontend 側でも同じ穴を開けない。

## 6. Conflict contract

```text
CONFLICT_BEHAVIOR      = FAIL_CLOSED
INVALID_VALUE_BEHAVIOR = NULL
```

許可された alias が複数存在し、**正規化後の値が食い違う**場合、resolver は
fail closed する。

```text
shrine_id=42, shrineId=42        -> 42
shrine_id=42, shrineId="42"      -> 42      （正規化後は一致）
shrine_id=42, shrineId=99        -> null    （FAIL CLOSED）
shrine_id=42, shrine.id=99       -> null    （FAIL CLOSED）
shrine_id=42, id=999             -> 42      （`id` は許可aliasではないので比較対象外）
```

競合時に先頭の値を黙って採用してはならない。

### 6.1 Why fail-closed rather than precedence

優先順位で解決すると、食い違い自体が**観測されないまま**通過する。
`F-1` の乖離値regression（`shrine_id: 42` / `id: 999`）が示したとおり、
2つのidentity fieldが同時に存在する状態では「どちらが勝つか」を暗黙にすると
退行が検出できない。fail-closed は、データ不整合を沈黙ではなく `null` として
表面化させる。

`public_strict` では alias が1つしかないため、この規則は実質 `registered_compat`
専用である。

## 7. Current fragmentation (evidence)

`develop` @ `21554d9` 実測。

| Consumer | 現在の解決順序 | generic `id` を使うか |
| --- | --- | --- |
| `features/compass/components/CompassRecommendationsSection.tsx` L38 / L62 | `shrine_id` | NO（`F-1` で除去済み） |
| `features/concierge/detailHref.ts` L26-29 `pickShrineId` | `shrine_id → shrineId → shrine.id` | NO（明示的に除外） |
| `features/concierge/hooks.ts` L145 / L154 | `shrine_id ?? id` | **YES** |
| `lib/concierge/mapConciergeResponseToPremiumMeaningContext.ts` L54-60 | `[shrine_id, id]` を順に走査 | **YES** |
| `components/views/ConsultationHistoryDetailView.tsx` L41 | `shrine_id ?? id` | **YES** |
| `lib/concierge/buildPreviousConsultationSummary.ts` L16 | `Number(shrine_id ?? id)` | **YES** |
| `lib/concierge/pickReasonFromThread.ts` L20 | `shrine.id → shrine_id → shrineId → id` | **YES** |
| `app/shrines/[id]/page.tsx` L370 | `Number(shrine_id ?? id)` | **YES** |
| `apps/mobile/lib/consultationHistoryUi.ts` L94-99 | `shrine_id ?? id` | **YES** |

```text
DISTINCT_PRECEDENCE_ORDERS_OBSERVED = 5
CONSUMERS_USING_GENERIC_ID          = 6 / 9
```

### 7.1 Naming collision to resolve in F-4

`lib/concierge/mapConciergeResponseToPremiumMeaningContext.ts` L54 には既に
**`resolveShrineId` という名前のローカル関数**が存在する。`F-4` はこれを
共有実装へ置き換える際、名前衝突を明示的に解消する必要がある（単純な import
追加では shadowing になる）。

## 8. Proposed implementation location

```text
apps/web/src/lib/identity/resolveShrineId.ts
```

現在 `apps/web/src/lib/identity/` は**存在しない**。`F-4` が新規作成する。

### 8.1 Why here

```text
- Shrine identity は Concierge 固有ではない
- navigation 固有ではない（buildShrineHref は identity の消費者であって定義者ではない）
- Compass 固有ではない
- recommendation ロジックの一部ではない
- backend は別の実装境界（F-5 が扱う）
```

`apps/web/src/lib/` には既に `analytics/` `api/` `geo/` `concierge/` 等の
ドメイン別ディレクトリがあり、`identity/` はその並びとして自然である。

### 8.2 Explicitly rejected locations

```text
features/concierge/     -> Concierge 固有ではない
features/compass/       -> Compass 固有ではない
lib/nav/buildShrineHref.ts -> navigation は消費者
recommendation code     -> ranking と identity は別責務
backend                 -> 別boundary。F-5。
```

### 8.3 `packages/shared` is NOT chosen — evidence

タスクの条件は「Web と Mobile が**まったく同じ** runtime / type 契約を採用できる
と、最新のリポジトリ証拠が示す場合に限り `packages/shared` へ置く」。
実測した証拠は**その逆**を示す。

```text
E-1  apps/mobile/types/shrine.ts L3
       export type ShrineId = string;
     -> Mobile の Shrine identity 表現は string。本resolverの返り値 number と異なる。

E-2  apps/mobile/lib/consultationHistoryUi.ts L94-99
       extractRecommendationShrineId(...): string | null
     -> 返り値の型が `number | null` ではない。

E-3  apps/mobile/package.json
     -> packages/shared への workspace 依存が存在しない。

E-4  packages/shared/
     -> package.json を持たない素の .ts 群。Web 側は相対パス
        （`../../../../../packages/shared/...`）で参照しており、
        パッケージ境界として確立していない。
```

```text
PACKAGES_SHARED_PLACEMENT = REJECTED_FOR_F3
REASON = Mobile contract differs at the return type (string vs number)
```

Mobile を移行対象に含めるかどうかは、この型差をどう扱うか（Mobile を number へ
寄せるのか、resolver に表現層を追加するのか）の決定を要する。`F-3` では決めない。

## 9. Consumer classification

| # | Consumer | Classification | Rationale |
| ---: | --- | --- | --- |
| 1 | `features/compass/components/CompassRecommendationsSection.tsx` | `PUBLIC_STRICT` | `R-3`/`R-4`/`R-5` により shrine_id が保証済み。`F-1` で既に `shrine_id` のみ。移行は「同じ挙動を共有実装経由にする」だけ |
| 2 | `features/concierge/detailHref.ts` `pickShrineId` | `REGISTERED_COMPAT` | 許可集合が `registered_compat` と完全一致。generic `id` を既に除外しており、挙動は不変 |
| 3 | `features/concierge/hooks.ts`（analytics） | `REGISTERED_COMPAT` | 現在 generic `id` を使用。移行で `id` fallback が外れる = **挙動が変わる**。analytics の shrineId が null になりうる点を `F-4` が評価すること |
| 4 | `components/views/ConsultationHistoryDetailView.tsx` | `REGISTERED_COMPAT` | 同上。履歴レコードは古い payload を含みうるため compat 側 |
| 5 | `lib/concierge/mapConciergeResponseToPremiumMeaningContext.ts` | `REGISTERED_COMPAT` | 同上。§7.1 の名前衝突を併せて解消すること |
| 6 | `lib/concierge/buildPreviousConsultationSummary.ts` | `REGISTERED_COMPAT` | 同上 |
| 7 | `lib/concierge/pickReasonFromThread.ts` | `NEEDS_SEPARATE_DECISION` | 唯一 `shrine.id` を**先頭**に置く順序。`registered_compat` は `shrine_id` 優先なので、移行は**優先順位の変更**になる。`shrine.id` と `shrine_id` が食い違う thread が存在しうるかの確認が先 |
| 8 | `app/shrines/[id]/page.tsx` L370 | `NEEDS_SEPARATE_DECISION` | Concierge snapshot recommendation との突合。保存済み過去 thread が対象で、当時の payload に `shrine_id` が無い可能性がある。`id` fallback を外すと過去履歴の突合が壊れうる |
| 9 | `apps/mobile/lib/consultationHistoryUi.ts` | `OUT_OF_F4_SCOPE` | §8.3 の通り Mobile の契約は返り値型が異なる（`string` vs `number`）。`F-4` は Web のみ |

```text
PUBLIC_STRICT            = 1
REGISTERED_COMPAT        = 5
NEEDS_SEPARATE_DECISION  = 2
OUT_OF_F4_SCOPE          = 1
TOTAL                    = 8 web + 1 mobile = 9
```

### 9.1 Behavior-change warning for F-4

分類は「どの policy を使うか」であって「挙動が変わらない」ことの保証ではない。

```text
挙動不変   : #1（既に shrine_id のみ）, #2（既に同一集合）
挙動が変わる : #3 #4 #5 #6 — generic `id` fallback が外れる
判断が要る : #7（優先順位変更）, #8（過去履歴の突合）
```

`F-4` は #3〜#6 について、`id` fallback 除去で identity が `null` に落ちる
payload が実在するかを確認したうえで移行すること。Compass では `R-5` の型が
その不在を保証していたが、Concierge 側には同等の保証がまだない。

## 10. Migration ownership

```text
F-3 (this record)
  - resolver contract / policies / prohibited fields / normalization / conflict
  - implementation location
  - consumer classification
  - NO implementation, NO migration

F-4
  - implement apps/web/src/lib/identity/resolveShrineId.ts
  - migrate selected Web frontend identity consumers (§9)
  - standardize precedence / policy use
  - add conflict regression
  - add generic-id negative regression
  - resolve the §7.1 naming collision
  - evaluate the §9.1 behavior changes before migrating #3–#6

F-5
  - backend fallback consolidation
    (16 `shrine_id or id` sites / 8 files — identity contract doc §4.1)

F-6
  - place_id shadow identity hardening
    (get_or_create_shrine_by_place_id dedupe — identity contract doc §5)
```

```text
MOBILE_MIGRATION = NOT_DECIDED
  requires a decision on the string/number return-type difference (§8.3)
```

## 11. Required statements

```text
1.  The resolver was NOT implemented.
2.  No consumer was migrated.
3.  No runtime code was modified.
4.  No type was modified.
5.  No fallback was removed.
6.  Compass was NOT modified.
7.  Concierge was NOT modified.
8.  Mobile was NOT modified.
9.  Backend was NOT modified.
10. OpenAPI was NOT modified.
11. Recommendation / Ranking were NOT changed.
12. No DB / schema / migration change.
13. place_id handling was NOT changed.
14. F-4 / F-5 / F-6 were NOT started.
```

## 12. STOP

```text
F3_STATUS      = DESIGNED
RUNTIME_CHANGE = NONE
NEXT           = F-4 (implement + migrate Web consumers)
```

Next action requires a Mother Ship instruction naming `F-4`.
