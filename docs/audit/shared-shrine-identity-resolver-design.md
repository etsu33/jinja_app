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

---

# F-3.1 — Design Amendment (resolution status preserved)

> 本節以降は `F-3`（§1–§12）への**追記**である。§1–§12 は `F-3` 時点の記録として
> そのまま保持し、書き換えない。`F-3` の `F3_STATUS = DESIGNED` /
> `RUNTIME_CHANGE = NONE` / §11 Required statements は、いずれも
> **`F-3` 時点の事実**として読むこと。現在の実装状態は §14 を参照。

## 13. F-3.1 amendment

```text
F3_1_STATUS = AMENDED
AMENDED_AT  = 2026-09-24
REASON      = RESOLUTION_STATUS_COLLAPSE_IS_UNSAFE_FOR_PLACE_ID_FALLBACK
```

### 13.1 何が問題だったか

`F-3` §2 の signature は

```ts
resolveShrineId(input: unknown, policy): number | null
```

であり、次の3つを**すべて同じ `null`** に潰していた。

```text
absent    identity が主張されていない
invalid   identity は主張されているが使えない
conflict  許可 alias 同士が食い違っている
```

`features/concierge/detailHref.ts` は identity が無いとき `place_id` へ
fallback する。したがって潰された `null` を受け取ると:

```text
{ shrine_id: 42, shrineId: 99, place_id: "ChIJxxx" }
  -> conflict
  -> null
  -> place_id fallback
  -> /shrines/resolve?place_id=ChIJxxx
```

となる。これは `F-3` §6 の `CONFLICT_BEHAVIOR = FAIL_CLOSED` を破っており、
かつ `F-6` の place_id shadow identity 経路へ入る。**conflict は「identity が
無い」ではなく「identity が壊れている」であり、代替経路へ落としてはならない。**

### 13.2 Authoritative result contract

```ts
type ShrineIdentityResolution =
  | { status: "resolved"; shrineId: number }
  | { status: "absent";   shrineId: null }
  | { status: "invalid";  shrineId: null }
  | { status: "conflict"; shrineId: null };
```

```ts
resolveShrineIdentity(
  input: unknown,
  policy: "public_strict" | "registered_compat"
): ShrineIdentityResolution
```

Optional convenience wrapper:

```ts
resolveShrineId(
  input: unknown,
  policy: "public_strict" | "registered_compat"
): number | null
```

```text
WRAPPER_DELEGATES_TO_AUTHORITATIVE = YES
IDENTITY_RESOLUTION_IMPLEMENTATIONS = 1
```

wrapper の実装は `resolveShrineIdentity(input, policy).shrineId` のみ。
`resolved` なら `shrineId`、それ以外はすべて `null`。分岐も再正規化も持たない。

### 13.3 Status の定義

```text
absent
  policy が許可する identity field が1つも present でない

invalid
  policy が許可する identity field が1つ以上 present だが、
  正の整数へ正規化できない

conflict
  2つ以上の有効な許可 alias が、正規化後に異なる ID になる

resolved
  有効な許可 field が1つ以上あり、present な有効 alias がすべて一致する
```

`generic id` / `place_id` / `placeId` / `place.id` / 名称 / 住所 / 座標は
**禁止 source であるため、これら4つの status のどれにも一切参加しない。**

#### 13.3.1 Presence rule（F-3.1 で明示した判断）

```text
PRESENCE_RULE = KEY_EXISTS_AND_VALUE_IS_NEITHER_UNDEFINED_NOR_NULL
```

すなわち **`shrine_id: null` は `absent` であり、`invalid` ではない。**

根拠（repository evidence、推測ではない）:

```text
backend/temples/services/concierge_candidate_normalize.py
  L20-24  place_id / shrine_id 等の空文字を _none_if_blank() で None に潰す
  L27     if out.get("shrine_id") is None: ... （key は present のまま None）
  L58-59  最後に shrine_id / place_id をもう一度 _none_if_blank()
```

未登録（place_id のみ）の候補は `shrine_id` **key を持ったまま値が `None`** で
frontend に届く。ここを `invalid` と判定すると、未登録候補の
`/shrines/resolve` 導線が全滅する。したがって `null` は `absent`。

#### 13.3.2 Status precedence（F-3.1 で解決した仕様上の曖昧さ）

`F-3.1` の status 定義は、`{ shrine_id: 42, shrineId: "bad" }` に対して
`invalid`（present だが正規化できない alias がある）とも
`resolved`（present な**有効** alias はすべて一致している）とも読める。

```text
PRECEDENCE = absent -> invalid -> conflict -> resolved
DECISION   = INVALID_WINS
```

採用根拠: 壊れた alias が有効な alias と同居している状態は、conflict と同じく
**データ整合性の破綻シグナル**であり、黙って捨てるのは `FAIL_CLOSED` の趣旨に
反する。

```text
{ shrine_id: 42, shrineId: "bad" } -> invalid   （resolved ではない）
```

これは `F-3.1` 指示文が明示していなかった点についての実装判断である。
Mother Ship が `RESOLVED_WINS` を選ぶ場合は上書き可能。

### 13.4 正規化（`F-3` §5 から不変）

```text
ACCEPT  42, "42"
REJECT  0 / 負数 / 浮動小数 / 空白文字列 / 非数値文字列 /
        NaN / Infinity / -Infinity / boolean / null / undefined
NEVER_THROWS = YES
```

`boolean` は `number` 判定より前に明示的に弾く（`Number(true) === 1` で
Shrine 1 に化けるため。backend の `_candidate_shrine_id` も同じ順序）。

### 13.5 Consumer への含意

```text
非identity fallback を持つ consumer     -> resolveShrineIdentity() 必須
非identity fallback を持たない consumer -> resolveShrineId() で十分
```

```text
detailHref.ts   place_id fallback あり -> resolveShrineIdentity()
Compass         fallback なし          -> resolveShrineId()
hooks.ts        fallback なし          -> resolveShrineId()
```

---

# F-4 — Implementation Status

## 14. F-4 implementation status

```text
F4_STATUS = PARTIAL_SAFE_MIGRATION
F4_AT     = 2026-09-24
```

```text
SHARED_RESOLVER_IMPLEMENTED               = YES
PUBLIC_STRICT_CONSUMER_MIGRATED           = YES
LIVE_REGISTERED_COMPAT_CONSUMERS_MIGRATED = YES

HISTORICAL_SNAPSHOT_CONSUMERS_MIGRATED    = NO
MOBILE_MIGRATED                           = NO

GENERIC_ID_ALLOWED_BY_SHARED_RESOLVER     = NO
PLACE_ID_ALLOWED_BY_SHARED_RESOLVER       = NO
CONFLICT_BEHAVIOR                         = FAIL_CLOSED
```

### 14.1 実装場所

```text
apps/web/src/lib/identity/resolveShrineId.ts
```

`F-3` §8.3 の通り `packages/shared` には置かない（Mobile の `ShrineId = string`
との返り値型差が未決のため）。

```text
PUBLIC_STRICT_ALLOWED_FIELDS     = shrine_id
REGISTERED_COMPAT_ALLOWED_FIELDS = shrine_id, shrineId, shrine.id
POLICY_ARGUMENT                  = REQUIRED_NO_DEFAULT
```

### 14.2 移行した consumer

| # | Consumer | Policy | 使った API | 挙動変化 |
| ---: | --- | --- | --- | --- |
| 1 | `features/compass/components/CompassRecommendationsSection.tsx` | `public_strict` | `resolveShrineId` | なし（`F-1` で既に `shrine_id` のみ）＋不正値が fail closed |
| 2 | `features/concierge/detailHref.ts` | `registered_compat` | **`resolveShrineIdentity`** | invalid / conflict が place_id へ落ちなくなった |
| 3 | `features/concierge/hooks.ts`（analytics 2箇所） | `registered_compat` | `resolveShrineId` | generic `id` fallback を除去 |
| 5 | `lib/concierge/mapConciergeResponseToPremiumMeaningContext.ts` | `registered_compat` | `resolveShrineId` | generic `id` fallback を除去（意図的な契約修正、§14.4） |

`F-3` §7.1 の名前衝突は、#5 の local `resolveShrineId()` を**削除**して
共有 resolver を import することで解消した（shadowing を残していない）。

`detailHref.ts` の `pickShrineId()` は export されていたが外部 importer が
1件も存在しなかったため**削除**した（独自正規化実装を残さないため）。
`pickPlaceId()` は未変更。

```text
INDEPENDENT_NORMALIZATION_RETAINED_IN_MIGRATED_CONSUMERS = NONE
```

### 14.3 `detailHref.ts` の status 分岐

```text
status=resolved -> buildShrineHref(shrineId)
status=absent   -> 既存の place_id fallback（/shrines/resolve）を維持
status=invalid  -> null（place_id へ落とさない）
status=conflict -> null（place_id へ落とさない）
```

必須回帰（`apps/web/src/features/concierge/__tests__/detailHref.test.ts`）:

```text
{ shrine_id: 42, shrineId: 99, place_id: "ChIJxxx" } -> null / not /shrines/resolve
{ shrine_id: "bad", place_id: "ChIJxxx" }            -> null / not /shrines/resolve
{ place_id: "ChIJxxx" }                              -> /shrines/resolve?place_id=ChIJxxx&ctx=concierge
{ shrine_id: null, place_id: "ChIJxxx" }             -> /shrines/resolve（§13.3.1）
```

### 14.4 意図的な契約修正（accidental regression ではない）

```text
FILE   apps/web/src/lib/concierge/__tests__/mapConciergeResponseToPremiumMeaningContext.test.ts
BEFORE { id: 1 } -> shrineId = 1
AFTER  { id: 1 } -> null
REASON GENERIC_ID_IS_NOT_SHRINE_IDENTITY_AUTHORITY
CLASS  INTENTIONAL_F4_CONTRACT_CORRECTION
```

当該 module は現時点で production importer を持たないが、その test は契約の
一部として維持する。既存の「shrine_id/id のみでも throw しない」test は
`{ shrine_id: 1 }` を使うよう書き換え、意図（throw しない・field が埋まる）を
保持した。

### 14.5 live producer evidence（#3 の移行根拠）

```text
F-7 が backend で固定:
  candidate["id"] == candidate["shrine_id"] == Shrine.id
  backend/temples/tests/services/test_concierge_build_chat_candidates_contract.py

現在の Concierge live recommendation はその共有 producer
（concierge_chat_candidates.py L284-285）由来。
```

したがって live 経路で generic `id` fallback を外しても identity は失われない。
解決できない場合も `shrine_id` を fabricate せず `null` のままとし、
`serializeSearchAnalyticsPayload()` の既存 null-strip 契約に従う
（イベント自体は従来どおり送信される）。

### 14.6 移行しなかった consumer（DEFERRED）

```text
F4_HISTORICAL_SNAPSHOT_MIGRATION = DEFERRED
REASON = PRE_CUTOVER_ID_ONLY_SNAPSHOT_COMPATIBILITY_NOT_PROVEN
```

| # | Consumer | 状態 |
| ---: | --- | --- |
| 4 | `components/views/ConsultationHistoryDetailView.tsx` L41 | 未変更 |
| 6 | `lib/concierge/buildPreviousConsultationSummary.ts` L16 | 未変更 |
| 7 | `lib/concierge/pickReasonFromThread.ts` L20 | 未変更 |
| 8 | `app/shrines/[id]/page.tsx` L370 | 未変更 |
| 9 | `apps/mobile/lib/consultationHistoryUi.ts` | 未変更（scope 外） |

根拠（repository evidence）:

```text
backend/temples/tests/api/test_journey_timeline_api.py
  recommendations_v2 の item が
    { "id": shrine.id, ... }
  という generic `id` のみの形を含む。
```

保存済み `ConciergeThread` snapshot は JSON であり、repository は
**すべての履歴 snapshot が `shrine_id` を持つことを証明していない。**
これら4 consumer から `id` 互換を外すと既存履歴の突合が壊れうる。

```text
本 PR は「履歴 snapshot に id-only が存在しない」とは推論していない。
証明されていないため保留した、というのが記録である。
```

### 14.7 Web runtime に残る generic-`id` identity fallback

```text
[A] F-4 で除去
  features/compass/components/CompassRecommendationsSection.tsx  （F-1 で既に除去、F-4 で共有化）
  features/concierge/detailHref.ts            pickShrineId 削除
  features/concierge/hooks.ts            L158 / L167
  lib/concierge/mapConciergeResponseToPremiumMeaningContext.ts  local resolveShrineId 削除

[B] 履歴互換のため意図的に保持（§14.6）
  components/views/ConsultationHistoryDetailView.tsx        L41
  lib/concierge/buildPreviousConsultationSummary.ts         L16
  lib/concierge/pickReasonFromThread.ts                     L20
  app/shrines/[id]/page.tsx                                 L370

[C] F-6（place_id shadow identity）経路 — /places/resolve/ レスポンス読み取り
  lib/api/places.ts                                         L47
  components/PlaceCardClientActions.tsx                     L29
  app/shrines/resolve/page.tsx                              L38

[D] F-5（backend）
  16 sites / 8 files — identity contract doc §4.1

[E] 本監査で新たに観測（F-3 §9 の consumer 一覧に無い。F-4 scope 外）
  lib/server/favorites.server.ts  L29
    favorite?.shrine_id ?? favorite?.shrine?.id ?? favorite?.target_id
    generic `id` ではないが、`target_id` は許可 source ではない。
  lib/concierge/pickBreakdownFromThread.ts  L23
  features/concierge/buildPayloadFromUnified.ts  L132
    いずれも generic `id` は読まないが、共有 resolver を使わない
    独自正規化が残っている（DUPLICATE_NORMALIZATION、違反ではない）。
  components/shrine/detail/ShrineDetailArticle.tsx  L368
    Shrine detail payload の `id` は Shrine PK そのもの（identity contract
    doc §4.4 の既存記録どおり）。違反ではない。
```

### 14.8 Validation

```text
pnpm -C apps/web typecheck                     PASS (exit 0)
vitest run src/lib/identity                    22 tests PASS
vitest run src/features/compass                PASS
vitest run src/features/concierge              PASS
vitest run src/lib/concierge                   PASS
vitest run（web 全体）                          214 files / 1774 tests PASS
git diff --check                               PASS
```

観測した環境上の事実（F-4 では修正していない）:

```text
apps/web/src/features/concierge/detailHref.ts の隣にある
detailHref.test.ts は vitest の include glob
  src/**/tests/*.{ts,tsx}
  src/**/__tests__/**/*.{test,spec}.{js,ts,tsx}
に一致しないため **収集されていない**（`No test files found`）。
同名の __tests__/detailHref.test.ts が実際に走っている方である。
F-4 の必須回帰は走る側（__tests__/）へ追加した。
vitest 設定の変更は F-4 のスコープ外のため行っていない。
```

### 14.9 Required statements

```text
1.  共有 resolver を実装した（apps/web/src/lib/identity/resolveShrineId.ts）。
2.  identity 解決の実装は1つだけ（wrapper は委譲のみ）。
3.  移行した Web consumer は #1 #2 #3 #5 の4件。
4.  #4 / #6 / #7 / #8 は未変更（DEFERRED）。
5.  Mobile は未変更。
6.  Backend は未変更。
7.  OpenAPI は未変更。
8.  DB / schema / migration の変更なし。
9.  Recommendation / Ranking は未変更。
10. place_id resolver の挙動は未変更（pickPlaceId 含む）。
11. F-5 の backend fallback は未変更。
12. F-6 の shadow identity logic は未変更。
13. 履歴 id-only snapshot が存在しない、という推論はしていない。
14. F-5 は開始していない。
```

## 15. STOP

```text
F3_1_STATUS = AMENDED
F4_STATUS   = PARTIAL_SAFE_MIGRATION
NEXT        = F-5 (backend fallback consolidation) / F-6 (place_id shadow identity)
              + 履歴 snapshot の id-only 実在確認（#4 #6 #7 #8 の前提）
```

次の行動には `F-5` を名指しする Mother Ship 指示が必要。
