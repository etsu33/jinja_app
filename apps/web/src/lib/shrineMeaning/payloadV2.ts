

// apps/web/src/lib/shrineMeaning/payloadV2.ts

/**
 * ShrineMeaningPayloadV2
 *
 * 神社詳細 Meaning Layer v2 の frontend 契約型。
 * backend meaning composer が生成した payload を frontend が表示するための型として扱う。
 *
 * 方針:
 * - frontend は generated fields を再生成しない
 * - source fields は実データ・生成根拠として保持する
 * - display fields は UI 表示用の安定した見出し・本文として扱う
 * - 欠損時のみ fallback 表示を許可する
 */

export type ShrineMeaningAccessLevel = "anonymous" | "free" | "premium";

export type ShrineMeaningSourceFieldsV2 = {
  shrineId: number;
  nameJp: string;
  address?: string | null;
  latitude?: number | null;
  longitude?: number | null;

  /** ご利益。実データ表示にも意味生成素材にも使う。 */
  goriyaku?: string | null;

  /** ご利益タグ名。表示・意味生成補助の両方に使う。 */
  goriyakuTags?: string[];

  /** 祭神。由緒としては扱わない。 */
  sajin?: string | null;

  /** 神社説明。Meaning本文へそのまま出さず、生成素材として扱う。 */
  description?: string | null;

  /** 歴史本文ではなく、歴史文脈タグとして扱う。 */
  historyTheme?: string | null;

  /** 五行・雰囲気補助。固定属性として断定しない。 */
  element?: string | null;

  /** 土地性・場所性の補助タグ。 */
  placeTags?: string[];

  directionBonus?: number | null;
  directionReason?: string | null;
};

export type ShrineMeaningGeneratedFieldsV2 = {
  /** ヒーロー部分の短い意味コピー。 */
  heroMeaningCopy: string;

  /** ユーザー相談内容との接続。 */
  consultationSummary: string;

  /** この神社をすすめる意味。 */
  shrineMeaning: string;

  /** 参拝・保存・詳細閲覧などの行動意味。 */
  actionMeaning: string;

  /** historyTheme 由来の文脈接続。歴史本文ではない。 */
  historyContext?: string | null;

  /** sajin 由来の象徴接続。由緒説明ではない。 */
  deitySymbolContext?: string | null;

  /** goriyaku 由来の行動接続。願望成就の断定ではない。 */
  benefitActionContext?: string | null;

  directionSupportCopy?: string | null;
};

export type ShrineMeaningDisplayBlockV2 = {
  id:
    | "hero"
    | "consultation_summary"
    | "shrine_meaning"
    | "action_meaning"
    | "history_context"
    | "deity_symbol"
    | "benefit_action"
    | "public_info";
  title: string;
  body: string;
  access: ShrineMeaningAccessLevel;
};

export type ShrineMeaningDisplayFieldsV2 = {
  blocks: ShrineMeaningDisplayBlockV2[];
  fallbackMessage?: string | null;
};

export type ShrineMeaningPayloadV2 = {
  version: "v2";
  source: ShrineMeaningSourceFieldsV2;
  generated: ShrineMeaningGeneratedFieldsV2;
  display: ShrineMeaningDisplayFieldsV2;
};
