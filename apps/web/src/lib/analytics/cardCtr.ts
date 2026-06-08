export type CardCtrVisibility = "visible" | "partial" | "teaser";

export type CardCtrEventInput = {
  event?: string | null;
  source?: string | null;
  cardId?: string | null;
  visibility?: string | null;
  accessLevel?: string | null;
  historyTheme?: string | null;
};

export type CardCtrRow = {
  source: string;
  cardId: string;
  visibility: CardCtrVisibility;
  accessLevel: string;
  historyTheme: string | null;
  cardVisibilityCount: number;
  premiumClickCount: number;
  ctr: number;
};

const CARD_VISIBILITY_EVENTS = new Set(["card_view", "card_partial_view", "card_teaser_view"]);

const PREMIUM_CLICK_EVENTS = new Set([
  "premium_preview_click",
  "concierge_premium_preview_click",
  "shrine_detail_premium_preview_click",
  "save_prompt_click",
]);

function normalizeVisibility(event: CardCtrEventInput): CardCtrVisibility | null {
  if (event.visibility === "visible" || event.visibility === "partial" || event.visibility === "teaser") {
    return event.visibility;
  }

  if (event.event === "card_view") return "visible";
  if (event.event === "card_partial_view") return "partial";
  if (event.event === "card_teaser_view") return "teaser";

  return null;
}

function buildGroupKey(args: {
  source: string;
  cardId: string;
  visibility: CardCtrVisibility;
  accessLevel: string;
  historyTheme: string | null;
}) {
  return [args.source, args.cardId, args.visibility, args.accessLevel, args.historyTheme ?? ""].join("::");
}

function createEmptyRow(args: {
  source: string;
  cardId: string;
  visibility: CardCtrVisibility;
  accessLevel: string;
  historyTheme: string | null;
}): CardCtrRow {
  return {
    source: args.source,
    cardId: args.cardId,
    visibility: args.visibility,
    accessLevel: args.accessLevel,
    historyTheme: args.historyTheme,
    cardVisibilityCount: 0,
    premiumClickCount: 0,
    ctr: 0,
  };
}

function isValidGroupInput(event: CardCtrEventInput): event is CardCtrEventInput & {
  source: string;
  cardId: string;
  accessLevel: string;
} {
  return Boolean(event.source && event.cardId && event.accessLevel);
}

export function aggregateCardCtr(events: CardCtrEventInput[]): CardCtrRow[] {
  const rows = new Map<string, CardCtrRow>();

  for (const event of events) {
    if (!event.event) continue;
    if (!isValidGroupInput(event)) continue;

    const visibility = normalizeVisibility(event);
    if (!visibility) continue;
    const historyTheme = event.historyTheme ?? null;

    const key = buildGroupKey({
      source: event.source,
      cardId: event.cardId,
      visibility,
      accessLevel: event.accessLevel,
      historyTheme,
    });

    const row = rows.get(key) ??
      createEmptyRow({
        source: event.source,
        cardId: event.cardId,
        visibility,
        accessLevel: event.accessLevel,
        historyTheme,
      });

    if (CARD_VISIBILITY_EVENTS.has(event.event)) {
      row.cardVisibilityCount += 1;
    }

    if (PREMIUM_CLICK_EVENTS.has(event.event)) {
      row.premiumClickCount += 1;
    }

    rows.set(key, row);
  }

  return Array.from(rows.values()).map((row) => ({
    ...row,
    ctr: row.cardVisibilityCount > 0 ? row.premiumClickCount / row.cardVisibilityCount : 0,
  }));
}
