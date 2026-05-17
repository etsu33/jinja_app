/**
 * Shrine Meaning Layer
 *
 * This schema describes a shrine as a meaningful place, not only as a spot
 * with address, benefits, and access information.
 *
 * The goal is to connect:
 * user state -> narrative -> place meaning -> real-world visit action.
 */

export type ToneLevel = "low" | "mid" | "high";

export type EmotionalTone = {
  /** 静けさ・落ち着きの強さ */
  silence: ToneLevel;
  /** 背筋が伸びる、緊張感がある、圧を感じる度合い */
  intensity: ToneLevel;
  /** 視界や気持ちが開ける感覚 */
  openness: ToneLevel;
  /** 包まれる、守られる、安心しやすい感覚 */
  grounding: ToneLevel;
};

export type ActionMeaning =
  | "rest"
  | "reflect"
  | "reset"
  | "decide"
  | "begin"
  | "continue"
  | "release"
  | "connect";

export type HistoricalContext =
  | "reconstruction"
  | "protection"
  | "boundary"
  | "commerce"
  | "journey"
  | "water"
  | "mountain_worship"
  | "imperial"
  | "local_guardian"
  | "victory"
  | "learning";

export type SpatialFeeling =
  | "quiet_forest"
  | "open_sky"
  | "water_presence"
  | "deep_approach"
  | "urban_oasis"
  | "wide_path"
  | "steep_path"
  | "enclosed_space"
  | "bright_space"
  | "solemn_space";

export type StateFit = {
  continuation: ToneLevel;
  progression: ToneLevel;
  recovery: ToneLevel;
  regression: ToneLevel;
  transition: ToneLevel;
};

export type ShrineMeaningSchema = {
  shrineId: number;
  /** 神社の意味を短く表す内部キー。例: quiet-recovery, boundary-transition */
  meaningKey: string;
  /** UIやnarrativeで使える短い意味タイトル */
  title: string;
  /** 神社固有の意味を説明する短文 */
  summary: string;
  /** 歴史・土地・空間を踏まえた中心テーマ */
  coreMeanings: string[];
  emotionalTone: EmotionalTone;
  actionMeanings: ActionMeaning[];
  historicalContexts: HistoricalContext[];
  spatialFeelings: SpatialFeeling[];
  stateFit: StateFit;
  /** 参拝時の推奨スタイル。断定ではなく提案として扱う。 */
  visitStyle?: {
    alone?: boolean;
    morning?: boolean;
    evening?: boolean;
    shortStay?: boolean;
    slowWalk?: boolean;
    writeAfterVisit?: boolean;
  };
  /** AI narrative に渡す補足。事実ではなく編集済み意味として扱う。 */
  narrativeHints?: string[];
  /** 情報源や編集メモ。UIには原則出さない。 */
  sourceNotes?: string[];
};
