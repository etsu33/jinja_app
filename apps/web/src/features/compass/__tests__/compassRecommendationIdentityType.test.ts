/**
 * R-5: CompassRecommendation["shrine_id"] の型契約を固定する。
 *
 * docs/audit/compass-shrine-id-presence-audit.md §13
 *
 *   FRONTEND_TYPE_REQUIRES_SHRINE_ID    = YES
 *   FRONTEND_TYPE_ALLOWS_NULL_SHRINE_ID = NO
 *
 * この file の主目的は `pnpm -C apps/web typecheck` による型検査であり、
 * `@ts-expect-error` が実際に project の TypeScript compiler で評価されることに
 * 依存している。もし将来 shrine_id が再び optional / nullable へ戻ると、
 * `@ts-expect-error` が「未使用のdirective」となって typecheck が失敗する。
 *
 * Vitest 実行時は値の存在を確認するだけで、副作用は持たない。
 * tsd 等の型テスト専用frameworkは導入していない。
 */

import { describe, expect, it } from "vitest";

import type { CompassRecommendation } from "../types";

// --- A: number は受理される -------------------------------------------------
const numericShrineId = { shrine_id: 1 } satisfies CompassRecommendation;

// --- B: string も受理される（表現の絞り込みは R-5 のスコープ外）--------------
const stringShrineId = { shrine_id: "1" } satisfies CompassRecommendation;

// --- E: `id` は COMPATIBILITY_FIELD として optional のまま -------------------
// shrine_id だけで成立し、`id` を伴っても成立する。
const withoutCompatibilityId = { shrine_id: 7 } satisfies CompassRecommendation;
const withCompatibilityId = { shrine_id: 7, id: 7 } satisfies CompassRecommendation;
// `id` は null も許容する（従来どおり）。
const withNullCompatibilityId = { shrine_id: 7, id: null } satisfies CompassRecommendation;

// --- C: shrine_id 欠落は拒否される ------------------------------------------
// @ts-expect-error shrine_id is required after R-5
const missingShrineId: CompassRecommendation = { name: "shrine_idの無い候補" };

// --- D: shrine_id: null は拒否される ----------------------------------------
// @ts-expect-error shrine_id is non-null after R-5
const nullShrineId: CompassRecommendation = { shrine_id: null, name: "nullの候補" };

// --- D-b: undefined も拒否される --------------------------------------------
// @ts-expect-error shrine_id is non-null after R-5
const undefinedShrineId: CompassRecommendation = { shrine_id: undefined, name: "undefinedの候補" };

describe("CompassRecommendation identity type contract (R-5)", () => {
  it("number / string の shrine_id を受理する", () => {
    expect(numericShrineId.shrine_id).toBe(1);
    expect(stringShrineId.shrine_id).toBe("1");
  });

  it("`id` は optional な互換fieldのまま", () => {
    expect(withoutCompatibilityId.shrine_id).toBe(7);
    expect("id" in withoutCompatibilityId).toBe(false);
    expect(withCompatibilityId.id).toBe(7);
    expect(withNullCompatibilityId.id).toBeNull();
  });

  it("型として不正なitemは値としては生成できてしまうため、契約はtypecheckが守る", () => {
    // 実行時にはただのobject。契約違反を捕捉するのは上の @ts-expect-error であり、
    // このassertionはそれらの値がVitest上で無害であることだけを示す。
    expect(missingShrineId).toBeTruthy();
    expect(nullShrineId.shrine_id).toBeNull();
    expect(undefinedShrineId.shrine_id).toBeUndefined();
  });
});
