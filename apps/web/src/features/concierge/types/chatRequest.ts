// apps/web/src/features/concierge/types/chatRequest.ts
//
// Level tagging below follows docs/product/concierge-input-architecture.md
// (Architecture Decision + Addendum: Level 3 Profile / Explicit Constraint /
// Recommendation Context Contract) and
// docs/audit/concierge-input-level-signal-inventory.md (PR #2397 audit).
// This is documentation only -- no field has been added, removed, renamed,
// or had its optionality changed as part of any annotation pass (Concierge
// Input Contract Foundation / Level 3 Contract, see
// backend/temples/services/concierge_input_contract.py for the backend
// side of this same boundary). Screen layout is unaffected by this
// annotation -- these are type-level/comment boundaries only.
//
// Level 3 splits into three distinct responsibilities (do not conflate
// them even though they may share UI screen space):
//   3-A Personal Profile      -- user-identity data (birthdate)
//   3-B Explicit Constraint   -- this-request hard constraints (goriyaku_tag_ids)
//   3-C Recommendation Context -- ambient situational data, not user
//                                 identity (location/visit_date)
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
  extra_condition?: string; // Level 2 Visit Preference（Legacy/Transitional, free-text）
  visit_preferences?: string[]; // Level 2 Visit Preference（Structured, canonical tags
  // -- see docs/product/concierge-input-architecture.md Addendum: Level 2 Visit
  // Preference Signal Redesign. Canonical vocabulary: quiet/nature/reset/
  // less_crowded/nearby/classic. No top-level/filters duplication (new field,
  // does not inherit Gap C).

  // ===== Level 3-C Recommendation Context（ユーザー属性ではなく「今回の推薦を
  //       計算する状況」。Personal ProfileでもExplicit Constraintでもない） =====
  visit_date?: string; // Canonical alias -- backend側は visit_date || planned_visit_date
  // で解決する（visit_dateが優先）。API field自体はCompatibility目的で維持、
  // planned_visit_date という別名フィールドは本typeには存在しない（frontendは
  // 送信しない、backend側のみが受理するlegacy alias）。
  location?: { lat: number; lng: number }; // radius/radius_mは現状frontendから送信しない
  // （backend既定値のみ、Concierge Chatパイプライン内ではCandidate hard filterには
  // ならない -- soft bias/観測用のみ。/nearest endpointとは責務が異なる）。

  profile_context?: {
    // Level 3-A Personal Profile。ただし注意: user_profile.birthdate/birthday は
    // 上記 `birthdate`（Canonical scoring birthdate）とは独立した別の優先順位
    // chainで、direction計算（planned_visit_lucky_directions等）のみに使われる
    // -- backend/temples/services/concierge_input_contract.py の
    // resolve_profile_context_birthdate() docstring参照。
    user_profile: Record<string, unknown>; // Level 3-A Personal Profile
    derived_profile: Record<string, unknown>; // Level 3-A Personal Profile（Derived）
    direction_profile?: never; // backendが必ず上書きするため、clientからは送らない
    // 注意: この direction_profile（kyusei方位計算結果）と、
    // consultation_interpreter.build_direction_profile()（相談状態のnarrative、
    // 別概念）は同名だが無関係 -- 既知のnaming collision、本typeの対象外
    // （backend専用の内部衝突、frontendはどちらも直接参照しない）。
  };
};
