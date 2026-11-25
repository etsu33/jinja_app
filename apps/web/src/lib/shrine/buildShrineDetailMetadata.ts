import type { ShrineDeity, ShrineHistory } from "@/lib/api/types";

import { buildShrineFactSection } from "./buildShrineFactSection";

const SITE_NAME = "KAMI MUSUBI";

// generic descriptionの共通末尾。Recommendation・Premium・ご利益・相性等の表現は含めない。
const GENERIC_DESCRIPTION_TAIL = `${SITE_NAME}で神社の基本情報を確認できます。`;

/**
 * metadata v1で description の候補にできる history_type と、その優先順位。
 *
 * tradition（伝承としてのhedged wording契約が必要）と regional_context（主語が神社ではなく
 * 地域文脈になり得る）は v1 では使用しない。
 */
const METADATA_HISTORY_TYPE_PRIORITY = [
  "official_origin",
  "founding",
  "editorial_summary",
  "historical_event",
] as const;

export type ShrineDetailMetadataInput = {
  name_jp?: string | null;
  address?: string | null;
  deities?: ShrineDeity[];
  histories?: ShrineHistory[];
};

export type ShrineDetailMetadataResult = {
  title: string;
  description: string;
};

/**
 * invalid ID / Shrine Detail API 取得失敗時の fail-safe metadata。
 * Page本体のerror UI（不正な神社ID / 詳細が見つかりません）は変更しない。
 */
export const SHRINE_DETAIL_GENERIC_METADATA: ShrineDetailMetadataResult = {
  title: `神社詳細 | ${SITE_NAME}`,
  description: GENERIC_DESCRIPTION_TAIL,
};

// metadataとして不要な改行・連続空白のみを畳む。意味の追加・要約・書き換えは行わない。
function normalizeMetadataWhitespace(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

/**
 * Fact Section（buildShrineFactSection）へ変換済みのHistory Factから、metadata description に
 * 使えるFactを1件選ぶ。
 *
 * - Evidence判定はFrontendで再実装せず、buildShrineFactSectionが確定した displayState のみを見る
 *   （displayState === "full" だけを候補とし、disputed は使わない）
 * - 同一 history_type が複数ある場合は buildShrineFactSection が確定した sort_order 順のまま先頭を使う
 * - trim後に空になる content は候補から除外する
 */
export function pickShrineMetadataHistoryContent(shrine: ShrineDetailMetadataInput): string | null {
  const factSection = buildShrineFactSection({
    deities: shrine.deities,
    histories: shrine.histories,
  });

  if (!factSection) {
    return null;
  }

  for (const historyType of METADATA_HISTORY_TYPE_PRIORITY) {
    for (const history of factSection.histories) {
      if (history.displayState !== "full") continue;
      if (history.history_type !== historyType) continue;

      const content = normalizeMetadataWhitespace(history.content ?? "");
      if (!content) continue;

      return content;
    }
  }

  return null;
}

/**
 * Shrine Detail取得成功時の title / description を組み立てる。
 *
 * description の第一候補は Knowledge History Fact。Legacy field（description / sajin）や
 * goriyaku / goriyaku_tags へはfallbackしない。使えるHistory Factが無い場合のみ
 * generic factual fallback を使う。
 *
 * name_jp が空（trim後に空文字）の場合は fallback文の主語が成立しないため、
 * fail-safeとして SHRINE_DETAIL_GENERIC_METADATA を返す。
 */
export function buildShrineDetailMetadata(shrine: ShrineDetailMetadataInput): ShrineDetailMetadataResult {
  const nameJp = (shrine.name_jp ?? "").trim();
  if (!nameJp) {
    return SHRINE_DETAIL_GENERIC_METADATA;
  }

  const title = `${nameJp} | ${SITE_NAME}`;

  const historyContent = pickShrineMetadataHistoryContent(shrine);
  if (historyContent) {
    return { title, description: historyContent };
  }

  const address = (shrine.address ?? "").trim();
  const description = address
    ? `${nameJp}は${address}にある神社です。${GENERIC_DESCRIPTION_TAIL}`
    : `${nameJp}の神社情報です。${GENERIC_DESCRIPTION_TAIL}`;

  return { title, description };
}
