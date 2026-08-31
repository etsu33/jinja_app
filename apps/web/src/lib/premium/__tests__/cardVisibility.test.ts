import { describe, expect, it } from "vitest";

import type { AccessLevel } from "../accessLevel";
import {
  CARD_VISIBILITY_POLICIES,
  getVisibilityForCard,
  type CardId,
  type CardVisibilityState,
} from "../cardVisibility";

/**
 * KAMI MUSUBI Premium / Free boundary -- Guest / Free / Premium visibility matrix.
 *
 * Fixed product rules encoded here (docs: PR-F Premium Boundary / CTA / cardVisibility):
 *  - The recommendation itself is never paywalled.
 *  - Consultation Summary is FREE and shown in full to Guest / Free / Premium.
 *  - Basic Reason + Recommendation Evidence are FREE (never "partial", never gated).
 *  - Deep Recommendation Reason / Personal Meaning / Action Meaning are PREMIUM,
 *    and Guest + Free both get a *teaser* (never "partial", never fully hidden).
 *  - Login only gates persistence / account surfaces (save_prompt, saved_record,
 *    state_teaser, login_prompt).
 */

type Matrix = Record<
  CardId,
  [anonymous: CardVisibilityState, free: CardVisibilityState, premium: CardVisibilityState]
>;

const EXPECTED_MATRIX: Matrix = {
  // anonymous, free, premium
  shrine_hero: ["visible", "visible", "visible"],
  shrine_compact: ["visible", "visible", "visible"],
  other_shrines: ["visible", "visible", "visible"],

  // Recommendation Evidence / rank -- FREE, never paywalled.
  recommendation_meta: ["visible", "visible", "visible"],

  // Consultation Summary -- FREE, full for everyone.
  consultation_summary: ["visible", "visible", "visible"],

  // Basic Reason -- FREE, full for everyone (not a deep section).
  context_reason: ["visible", "visible", "visible"],

  // Deep Recommendation Reason / Personal Meaning / Action Meaning -- PREMIUM.
  // Guest + Free both get a teaser; Premium gets the full content.
  shrine_meaning: ["teaser", "teaser", "visible"],
  personal_meaning: ["teaser", "teaser", "visible"],
  action_meaning: ["teaser", "teaser", "visible"],

  // Cross-session meaning / delta / journey -- PREMIUM only (CTA-B continuity
  // surfaces carry their own teaser copy; they are not surfaced via these cards).
  previous_comparison: ["hidden", "hidden", "visible"],
  history_shift: ["hidden", "hidden", "visible"],
  deep_reflection: ["hidden", "hidden", "visible"],
  comparison_hint: ["hidden", "partial", "hidden"],

  // Premium upsell teaser card -- shown to Guest / Free, hidden once Premium.
  premium_preview: ["visible", "visible", "hidden"],

  // Persistence / account -- login gates these, not the meaning content.
  save_prompt: ["teaser", "visible", "visible"],
  saved_record: ["hidden", "visible", "visible"],
  state_teaser: ["hidden", "visible", "hidden"],
  login_prompt: ["visible", "hidden", "hidden"],

  // Shrine public facts -- FREE for everyone (never Premium-only).
  shrine_public_info: ["visible", "visible", "visible"],
  shrine_access: ["visible", "visible", "visible"],
  shrine_goriyaku: ["visible", "visible", "visible"],
  shrine_goshuin_preview: ["visible", "visible", "visible"],

  filter_panel: ["visible", "visible", "visible"],
};

const LEVELS: AccessLevel[] = ["anonymous", "free", "premium"];

describe("cardVisibility -- Guest / Free / Premium matrix", () => {
  it("every policy in CARD_VISIBILITY_POLICIES has an expected matrix row", () => {
    const policyIds = CARD_VISIBILITY_POLICIES.map((p) => p.cardId).sort();
    const expectedIds = (Object.keys(EXPECTED_MATRIX) as CardId[]).sort();
    expect(policyIds).toEqual(expectedIds);
  });

  it.each(Object.entries(EXPECTED_MATRIX))("%s resolves to the fixed Guest/Free/Premium visibility", (cardId, expected) => {
    LEVELS.forEach((level, index) => {
      expect(getVisibilityForCard(cardId as CardId, level)).toBe(expected[index]);
    });
  });

  it("unknown card ids resolve to hidden", () => {
    expect(getVisibilityForCard("does_not_exist" as CardId, "free")).toBe("hidden");
  });
});

describe("cardVisibility -- fixed KAMI MUSUBI Premium boundary rules", () => {
  it("Consultation Summary is FREE and full for Guest / Free / Premium", () => {
    LEVELS.forEach((level) => {
      expect(getVisibilityForCard("consultation_summary", level)).toBe("visible");
    });
  });

  it("Basic Reason and Recommendation Evidence are FREE (visible, never partial/hidden) at every level", () => {
    (["context_reason", "recommendation_meta"] as const).forEach((cardId) => {
      LEVELS.forEach((level) => {
        expect(getVisibilityForCard(cardId, level)).toBe("visible");
      });
    });
  });

  it("Deep Reason / Personal Meaning / Action Meaning are teased identically for Guest and Free, full for Premium", () => {
    (["shrine_meaning", "personal_meaning", "action_meaning"] as const).forEach((cardId) => {
      const guest = getVisibilityForCard(cardId, "anonymous");
      const free = getVisibilityForCard(cardId, "free");
      expect(guest).toBe("teaser");
      expect(free).toBe("teaser");
      expect(guest).toBe(free);
      expect(getVisibilityForCard(cardId, "premium")).toBe("visible");
    });
  });

  it("no deep meaning section is ever shown as 'partial' to Free (deep sections are teased, not truncated)", () => {
    (["shrine_meaning", "personal_meaning", "action_meaning", "context_reason"] as const).forEach((cardId) => {
      expect(getVisibilityForCard(cardId, "free")).not.toBe("partial");
    });
  });

  it("Shrine public facts are FREE at every level, never Premium-only", () => {
    (["shrine_public_info", "shrine_access", "shrine_goriyaku", "shrine_goshuin_preview"] as const).forEach((cardId) => {
      LEVELS.forEach((level) => {
        expect(getVisibilityForCard(cardId, level)).toBe("visible");
      });
    });
  });

  it("premium upsell teaser is shown to Guest / Free and disappears for Premium", () => {
    expect(getVisibilityForCard("premium_preview", "anonymous")).toBe("visible");
    expect(getVisibilityForCard("premium_preview", "free")).toBe("visible");
    expect(getVisibilityForCard("premium_preview", "premium")).toBe("hidden");
  });
});
