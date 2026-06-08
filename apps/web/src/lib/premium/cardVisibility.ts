import type { AccessLevel } from "./accessLevel";

export type CardVisibilityState = "visible" | "teaser" | "partial" | "hidden";

export type CardId =
  | "consultation_summary"
  | "shrine_hero"
  | "shrine_meaning"
  | "action_meaning"
  | "previous_comparison"
  | "history_shift"
  | "other_shrines"
  | "shrine_compact"
  | "save_prompt"
  | "premium_preview"
  | "login_prompt"
  | "state_teaser"
  | "filter_panel"
  | "comparison_hint"
  | "deep_reflection"
  | "shrine_public_info"
  | "shrine_access"
  | "shrine_goriyaku"
  | "shrine_goshuin_preview"
  | "context_reason"
  | "personal_meaning"
  | "saved_record"
  | "recommendation_meta";

export type CardVisibilityPolicy = {
  cardId: CardId;
  anonymous: CardVisibilityState;
  free: CardVisibilityState;
  premium: CardVisibilityState;
};

export function getCardVisibility(policy: CardVisibilityPolicy, accessLevel: AccessLevel): CardVisibilityState {
  return policy[accessLevel];
}

export const CARD_VISIBILITY_POLICIES: CardVisibilityPolicy[] = [
  {
    cardId: "shrine_hero",
    anonymous: "visible",
    free: "visible",
    premium: "visible",
  },
  {
    cardId: "shrine_compact",
    anonymous: "visible",
    free: "visible",
    premium: "visible",
  },
  {
    cardId: "other_shrines",
    anonymous: "visible",
    free: "visible",
    premium: "visible",
  },
  {
    cardId: "save_prompt",
    anonymous: "teaser",
    free: "visible",
    premium: "visible",
  },
  {
    cardId: "login_prompt",
    anonymous: "visible",
    free: "hidden",
    premium: "hidden",
  },
  {
    cardId: "premium_preview",
    anonymous: "visible",
    free: "visible",
    premium: "hidden",
  },
  {
    cardId: "consultation_summary",
    anonymous: "hidden",
    free: "partial",
    premium: "visible",
  },
  {
    cardId: "state_teaser",
    anonymous: "hidden",
    free: "visible",
    premium: "hidden",
  },
  {
    cardId: "filter_panel",
    anonymous: "visible",
    free: "visible",
    premium: "visible",
  },
  {
    cardId: "shrine_meaning",
    anonymous: "hidden",
    free: "partial",
    premium: "visible",
  },
  {
    cardId: "action_meaning",
    anonymous: "hidden",
    free: "teaser",
    premium: "visible",
  },
  {
    cardId: "comparison_hint",
    anonymous: "hidden",
    free: "partial",
    premium: "hidden",
  },
  {
    cardId: "previous_comparison",
    anonymous: "hidden",
    free: "hidden",
    premium: "visible",
  },
  {
    cardId: "history_shift",
    anonymous: "hidden",
    free: "hidden",
    premium: "visible",
  },
  {
    cardId: "deep_reflection",
    anonymous: "hidden",
    free: "hidden",
    premium: "visible",
  },
  {
    cardId: "shrine_public_info",
    anonymous: "visible",
    free: "visible",
    premium: "visible",
  },
  {
    cardId: "shrine_access",
    anonymous: "visible",
    free: "visible",
    premium: "visible",
  },
  {
    cardId: "shrine_goriyaku",
    anonymous: "visible",
    free: "visible",
    premium: "visible",
  },
  {
    cardId: "shrine_goshuin_preview",
    anonymous: "visible",
    free: "visible",
    premium: "visible",
  },
  {
    cardId: "context_reason",
    anonymous: "hidden",
    free: "partial",
    premium: "visible",
  },
  {
    cardId: "personal_meaning",
    anonymous: "hidden",
    free: "teaser",
    premium: "visible",
  },
  {
    cardId: "saved_record",
    anonymous: "hidden",
    free: "visible",
    premium: "visible",
  },
  {
    cardId: "recommendation_meta",
    anonymous: "hidden",
    free: "visible",
    premium: "visible",
  },
];

export function getVisibilityForCard(cardId: CardId, accessLevel: AccessLevel): CardVisibilityState {
  const policy = CARD_VISIBILITY_POLICIES.find((item) => item.cardId === cardId);
  return policy ? getCardVisibility(policy, accessLevel) : "hidden";
}
