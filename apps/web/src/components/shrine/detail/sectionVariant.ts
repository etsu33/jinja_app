// apps/web/src/components/shrine/detail/sectionVariant.ts
//
// PR-G3 (docs/design/premium-meaning-ui-direction.md §6, Direction C): the
// Shrine Detail Meaning sections (reason / proposal / meaning / action /
// supplement) can render either as a bordered card ("card", the default and
// unchanged behaviour) or as a borderless editorial section ("plain") so the
// interpretation layer reads as one continuous narrative rather than a stack of
// repeated cards. Shrine facts (ShrineFactSection) intentionally stay carded so
// the fact / interpretation boundary stays visible.
//
// Additive only -- no content, analytics, or Premium behaviour changes.

export type ShrineDetailSectionVariant = "card" | "plain";

export const SHRINE_DETAIL_SECTION_CARD_CLASS =
  "rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4";
