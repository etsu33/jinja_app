// apps/web/src/features/concierge/types/chatRequest.ts
//
// Level tagging below follows docs/product/concierge-input-architecture.md
// (Architecture Decision) and docs/audit/concierge-input-level-signal-inventory.md
// (PR #2397 audit). This is documentation only -- no field has been added,
// removed, renamed, or had its optionality changed as part of this
// annotation pass (Concierge Input Contract Foundation, see
// backend/temples/services/concierge_input_contract.py for the backend
// side of this same boundary).
export type ConciergeChatFilters = {
  // ===== Compatibility（top-level と重複送信される既存backend互換field） =====
  birthdate?: string; // "YYYY-MM-DD" -- Level 3-A Personal Profile
  goriyaku_tag_ids?: number[]; // [1,2,3] -- Level 3-B Explicit Constraint (NOT Profile data)
  extra_condition?: string; // "駅近 ひとり" -- Level 2 Visit Preference (Legacy/Transitional)

  // ===== Legacy Candidate（型としては存在するが、現行backendは未消費。
  //       docs/audit/concierge-input-level-signal-inventory.md Gap E参照） =====
  area_pref?: string[]; // ["東京都"]
  goriyaku?: string[]; // ["縁結び","厄除け"]

  // ===== Compatibility（backendには送らず、hooks.ts側でextra_conditionへ
  //       畳み込まれる。単独ではbackend契約に存在しない） =====
  crowd?: ("quiet" | "normal" | "crowded")[];
  duration_max_min?: number;
  free_text?: string; // extra_condition を最終的にここに寄せる
};

export type ConciergeMode = "need" | "compat";

export type ConciergeChatRequestV1 = {
  version: 1;
  query: string; // Level 1 Consultation（raw input; message は互換で query に統合される）
  mode?: ConciergeMode;
  thread_id?: string;
  filters?: ConciergeChatFilters; // Compatibility（下記top-level fieldと重複送信、Gap C）
  birthdate?: string; // Level 3-A Personal Profile（Compatibility copy）
  goriyaku_tag_ids?: number[]; // Level 3-B Explicit Constraint（Compatibility copy）
  extra_condition?: string; // Level 2 Visit Preference（Compatibility copy）
  visit_date?: string; // Level 3-C Context
  location?: { lat: number; lng: number }; // Level 3-C Context
  profile_context?: {
    user_profile: Record<string, unknown>; // Level 3-A Personal Profile
    derived_profile: Record<string, unknown>; // Level 3-A Personal Profile（Derived）
    direction_profile?: never; // backendが必ず上書きするため、clientからは送らない
  };
};
