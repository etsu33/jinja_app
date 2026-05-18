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
  | "comparison_hint"
  | "deep_reflection"
  | "shrine_public_info"
  | "shrine_access"
  | "shrine_goriyaku"
  | "shrine_goshuin_preview"
  | "context_reason"
  | "personal_meaning"
  | "saved_record";

export type CardVisibilityPolicy = {
  cardId: CardId;
  anonymous: CardVisibilityState;
  free: CardVisibilityState;
  premium: CardVisibilityState;
};

export function getCardVisibility(policy: CardVisibilityPolicy, accessLevel: AccessLevel): CardVisibilityState {
  return policy[accessLevel];
}
