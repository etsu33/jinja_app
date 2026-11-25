import type { ShrineHighlight } from "@/lib/api/types";
import type {
  DetailFactSection,
  DetailHighlightItem,
  DetailHighlightLink,
  DetailHighlightSection,
} from "@/components/shrine/detail/types";

// 見どころのカテゴリーの表示名。Backend の ShrineHighlight.Category（固定6種）に対応する。
// 未知の値はカテゴリー名を出さない（内部の英語キーを画面に出さないため）。
export const SHRINE_HIGHLIGHT_CATEGORY_LABELS: Readonly<Record<string, string>> = {
  architecture: "建築",
  cultural_heritage: "文化財",
  nature: "自然",
  ritual_festival: "祭り・神事",
  historical_site: "史跡",
  experience: "体験",
};

export const SHRINE_HIGHLIGHT_SECTION_HEADING = "ここで見られるもの";

// 画面内リンクの id。由緒・歴史と見どころを行き来する。
export function shrineHighlightAnchorId(id: number): string {
  return `shrine-highlight-${id}`;
}

export function shrineHistoryAnchorId(id: number): string {
  return `shrine-history-${id}`;
}

function trimmed(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

// "2026-11-21" → "2026年11月21日"。形が違えば null（日付として扱わない）。
export function formatObservedOn(value: string | null | undefined): string | null {
  const match = typeof value === "string" ? /^(\d{4})-(\d{2})-(\d{2})$/.exec(value) : null;
  if (!match) return null;
  return `${Number(match[1])}年${Number(match[2])}月${Number(match[3])}日`;
}

/**
 * Shrine Detail API の highlights を「ここで見られるもの」へ変換する。
 * 見どころが無ければ null を返し、呼び出し側は節を出さない。
 * 由緒・歴史へのリンクは、Fact Section に実際に出ている由緒・歴史だけにする（リンク切れを作らない）。
 */
export function buildShrineHighlightSection(
  shrine: { highlights?: ShrineHighlight[] },
  factSection: DetailFactSection | null,
): DetailHighlightSection | null {
  const highlights = Array.isArray(shrine.highlights) ? shrine.highlights : [];
  const historyTitles = new Map<number, string>();
  for (const history of factSection?.histories ?? []) {
    if (history.id != null) historyTitles.set(history.id, history.title);
  }

  const items: DetailHighlightItem[] = [...highlights]
    .filter((highlight) => trimmed(highlight.name) && trimmed(highlight.description))
    .sort((a, b) => a.sort_order - b.sort_order || a.id - b.id)
    .map((highlight) => ({
      id: highlight.id,
      categoryLabel: SHRINE_HIGHLIGHT_CATEGORY_LABELS[highlight.category] ?? "",
      name: trimmed(highlight.name),
      description: trimmed(highlight.description),
      historicalConnection: trimmed(highlight.historical_connection),
      locationHint: trimmed(highlight.location_hint),
      linkedHistories: (Array.isArray(highlight.linked_history_ids) ? highlight.linked_history_ids : [])
        .filter((id) => historyTitles.has(id))
        .map((id) => ({ id, title: historyTitles.get(id) ?? "" })),
      sources: Array.isArray(highlight.sources) ? highlight.sources : [],
      observedOnLabel: formatObservedOn(highlight.observed_on),
    }));

  if (items.length === 0) return null;

  return {
    kind: "highlight",
    heading: SHRINE_HIGHLIGHT_SECTION_HEADING,
    items,
  };
}

/**
 * Fact Section の各由緒・歴史に、それを境内で確かめられる見どころへのリンクを足す。
 * 元の Fact Section は書き換えず、新しいオブジェクトを返す。
 */
export function attachHighlightLinksToFactSection(
  factSection: DetailFactSection | null,
  highlightSection: DetailHighlightSection | null,
): DetailFactSection | null {
  if (!factSection || !highlightSection) return factSection;

  const linksByHistoryId = new Map<number, DetailHighlightLink[]>();
  for (const item of highlightSection.items) {
    for (const history of item.linkedHistories) {
      const links = linksByHistoryId.get(history.id) ?? [];
      links.push({ id: item.id, name: item.name });
      linksByHistoryId.set(history.id, links);
    }
  }
  if (linksByHistoryId.size === 0) return factSection;

  return {
    ...factSection,
    histories: factSection.histories.map((history) => {
      const links = history.id != null ? linksByHistoryId.get(history.id) : undefined;
      return links ? { ...history, highlightLinks: links } : history;
    }),
  };
}
