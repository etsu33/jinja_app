// apps/mobile/lib/compass.ts
//
// Mobile「今月の参拝コンパス」の通信・型・表示用の値をまとめる。
// Web の apps/web/src/features/compass（types.ts / compassPurposes.ts /
// resolveCompassCandidatePresentation.ts / CompassClient.tsx）と同じ契約に揃える。
// Web の型は Web だけが使う前提で features/compass に置かれているため、
// Mobile 側に同じ形の写しを持つ（packages/shared への移動はこのPRでは行わない）。
//
// 役割の線引き（ドライブ「KAMI MUSUBI コンシェルジュとコンパスの役割の線引き」2026-11-25）:
// コンパスは「生年月日 × 方位」。相談文は受け取らない（相談はコンシェルジュの役割）。
//
// Backend: POST /api/compass/recommendations/
//   backend/temples/api_views_compass.py::CompassRecommendationsView
//   AllowAny + JWTAuthentication。ログイン中ならトークンを付け、無ければ付けずに送る。
//   結果の state は Backend の値をそのまま使い、Mobile で読み替えない。
import { getRefreshToken } from "./authTokens";
import { isHttpError, isUnauthenticatedError, post, postAuth } from "./http";
import { toOriginPayload, type UserOrigin } from "../../../packages/shared/userOrigin";

// ---------------------------------------------------------------------------
// 目的（既存の need_tag 15分類をそのまま使う。Web の compassPurposes.ts と同じ）
// ---------------------------------------------------------------------------

export type CompassPurpose =
  | "love"
  | "relationship"
  | "marriage"
  | "communication"
  | "career"
  | "money"
  | "study"
  | "health"
  | "mental"
  | "protection"
  | "courage"
  | "focus"
  | "rest"
  | "family"
  | "travel_safe";

export const COMPASS_PURPOSE_LABELS_JA: Record<CompassPurpose, string> = {
  love: "恋愛",
  relationship: "人間関係",
  marriage: "縁結び・結婚",
  communication: "対話・発信",
  career: "転機・仕事",
  money: "金運",
  study: "学業・合格",
  health: "健康",
  mental: "不安・心",
  protection: "厄除け・守り",
  courage: "前進・後押し",
  focus: "集中・継続",
  rest: "休息",
  family: "子宝・家族",
  travel_safe: "移動・安全",
};

// 表示順。Web と同じく backend/temples/domain/need_tags.py の NEED_PRIORITY の順。
export const COMPASS_PURPOSES_ORDERED: readonly CompassPurpose[] = [
  "protection",
  "marriage",
  "love",
  "family",
  "study",
  "career",
  "money",
  "health",
  "mental",
  "relationship",
  "communication",
  "courage",
  "focus",
  "rest",
  "travel_safe",
];

// ---------------------------------------------------------------------------
// Backend の応答（Web の types.ts と同じ形）
// ---------------------------------------------------------------------------

export type CompassCalculationMethod = "annual_monthly_kyusei_v1" | "monthly_kyusei_v1";

export type CompassDirectionRuntime = {
  targetDate: string;
  targetYear: number;
  solarMonthIndex: number;
  referenceDirections: string[];
  calculationMethod: CompassCalculationMethod;
  note: string;
};

export type CompassReasonFact = {
  type?: string | null;
  label?: string | null;
  label_ja?: string | null;
  is_primary?: boolean | null;
};

export type CompassShrineFacts = {
  deity?: { display_name: string };
  history?: { history_type: string; content: string };
};

export type CompassRecommendation = {
  // 神社の識別子は shrine_id だけを使う（id は互換用で識別に使わない）。
  shrine_id: number | string;
  id?: number | string | null;
  name?: string | null;
  address?: string | null;
  distance_m?: number | null;
  reason_facts?: CompassReasonFact[] | null;
  shrine_facts?: CompassShrineFacts | null;
  [key: string]: unknown;
};

export type CompassResultState =
  | "invalid_purpose"
  | "direction_filter_unavailable"
  | "no_common_direction"
  | "recommendation_eligibility_zero_candidates"
  | "direction_zero_candidates"
  | "evidence_zero_candidates"
  | "recommendation_success";

export type CompassRecommendationsResponse = {
  state: CompassResultState;
  purpose: string | null;
  direction_context: CompassDirectionRuntime | null;
  recommendation_instance_id: string;
  recommendations: CompassRecommendation[];
  distance_stage_km: 15 | 30 | 60 | null;
  direction_candidate_count: number | null;
  distance_candidate_count: number | null;
};

const RESULT_STATES: readonly CompassResultState[] = [
  "invalid_purpose",
  "direction_filter_unavailable",
  "no_common_direction",
  "recommendation_eligibility_zero_candidates",
  "direction_zero_candidates",
  "evidence_zero_candidates",
  "recommendation_success",
];

function isCompassResultState(value: unknown): value is CompassResultState {
  return typeof value === "string" && (RESULT_STATES as readonly string[]).includes(value);
}

function isCompassResponse(value: unknown): value is CompassRecommendationsResponse {
  return Boolean(value) && typeof value === "object" && isCompassResultState((value as { state?: unknown }).state);
}

// ---------------------------------------------------------------------------
// 通信
// ---------------------------------------------------------------------------

export type CompassRequest = {
  purpose: CompassPurpose;
  birthdate: string;
  origin: UserOrigin;
};

export type CompassFetchResult =
  | { ok: true; response: CompassRecommendationsResponse }
  | { ok: false };

const COMPASS_PATH = "/compass/recommendations/";

function buildBody(request: CompassRequest) {
  // 相談文・参拝スタイルなどは送らない。Web と同じ3項目だけ。
  return {
    purpose: request.purpose,
    birthdate: request.birthdate,
    origin: toOriginPayload(request.origin),
  };
}

// 400 は Backend が state 付きの結果を返すことがある（invalid_purpose など）。
// Web と同じく、本文が結果の形なら結果として扱う。
function parseErrorBody(error: unknown): CompassRecommendationsResponse | null {
  if (!isHttpError(error) || error.status !== 400 || !error.body) return null;
  try {
    const parsed: unknown = JSON.parse(error.body);
    return isCompassResponse(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

async function postAnonymously(body: ReturnType<typeof buildBody>): Promise<unknown> {
  return post<unknown>(COMPASS_PATH, body);
}

export async function fetchCompassRecommendations(request: CompassRequest): Promise<CompassFetchResult> {
  const body = buildBody(request);

  try {
    // ログイン中はトークンを付ける。期限切れなどで使えなければ、付けずに送り直す。
    const hasSession = Boolean(await getRefreshToken());
    let raw: unknown;
    if (hasSession) {
      try {
        raw = await postAuth<unknown>(COMPASS_PATH, body);
      } catch (error) {
        if (!isUnauthenticatedError(error)) throw error;
        raw = await postAnonymously(body);
      }
    } else {
      raw = await postAnonymously(body);
    }
    return isCompassResponse(raw) ? { ok: true, response: raw } : { ok: false };
  } catch (error) {
    const structured = parseErrorBody(error);
    return structured ? { ok: true, response: structured } : { ok: false };
  }
}

// ---------------------------------------------------------------------------
// 生年月日（Web の CompassClient.tsx と同じ判定）
// ---------------------------------------------------------------------------

export type BirthdateParts = { year: string; month: string; day: string };

export function parseBirthdate(value: string | null | undefined): BirthdateParts {
  const match = value?.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return match ? { year: match[1], month: match[2], day: match[3] } : { year: "", month: "", day: "" };
}

export function isValidBirthdate({ year, month, day }: BirthdateParts, today: Date = new Date()): boolean {
  if (!/^\d{4}$/.test(year) || !/^\d{1,2}$/.test(month) || !/^\d{1,2}$/.test(day)) return false;
  const numericYear = Number(year);
  const numericMonth = Number(month);
  const numericDay = Number(day);
  if (numericMonth < 1 || numericMonth > 12 || numericDay < 1) return false;
  const isLeapYear = numericYear % 4 === 0 && (numericYear % 100 !== 0 || numericYear % 400 === 0);
  const daysInMonth = [31, isLeapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (numericDay > daysInMonth[numericMonth - 1]) return false;
  // 未来の日付は生年月日として受け付けない。
  const birth = new Date(numericYear, numericMonth - 1, numericDay);
  return birth.getTime() <= today.getTime();
}

export function formatBirthdate({ year, month, day }: BirthdateParts): string {
  return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
}

export function formatTargetMonth(date: Date): string {
  return `${date.getFullYear()}年${date.getMonth() + 1}月`;
}

// ---------------------------------------------------------------------------
// 方位の表示（Web の CompassClient.tsx と同じ文言）
// ---------------------------------------------------------------------------

// Backend の note は2つの計算方法で同じ固定文のため、計算方法から文を決める。
export function getDirectionNote(calculationMethod: CompassCalculationMethod): string {
  if (calculationMethod === "monthly_kyusei_v1") {
    return "年盤と月盤で重なる方位がないため、今月の月盤を参考にした方位です。日盤は使用していません。";
  }
  return "年盤と月盤の両方で重なる、今月の参考方位です。日盤は使用していません。";
}

// 知らない値のときは何も出さない（分類を作らない）。
export function getDirectionStatusLabel(calculationMethod: string): string | null {
  if (calculationMethod === "annual_monthly_kyusei_v1") return "年盤・月盤 共通";
  if (calculationMethod === "monthly_kyusei_v1") return "今月の月盤を参考";
  return null;
}

export const DIRECTION_LABELS = ["北", "北東", "東", "南東", "南", "南西", "西", "北西"] as const;

export function describeReferenceDirections(referenceDirections: readonly string[]): string {
  return referenceDirections.length > 0
    ? `今月意識したい方向: ${referenceDirections.join("・")}`
    : "今月意識したい方向は算出されていません";
}

// ---------------------------------------------------------------------------
// 結果がうまく出なかったときの文言（Web の CompassClient.tsx と同じ）
// ---------------------------------------------------------------------------

export type CompassNoticeState = Exclude<CompassResultState, "recommendation_success" | "invalid_purpose"> | "backend_error";

export type CompassNotice = {
  title: string;
  description: string;
  // コンシェルジュへの導線を出すか（結果そのものが正常なのに候補が無いとき）
  offerConcierge: boolean;
};

export const COMPASS_NOTICES: Record<CompassNoticeState, CompassNotice> = {
  direction_filter_unavailable: {
    title: "方向の参考情報を計算できませんでした",
    description: "生年月日または出発地点をご確認のうえ、もう一度お試しください。",
    offerConcierge: false,
  },
  no_common_direction: {
    title: "今月は方位の参考情報がありません",
    description:
      "生年月日・出発地点はどちらも問題ありません。年盤と月盤の共通方位も、今月の月盤単独の参考方位も、今月はいずれもありませんでした。",
    offerConcierge: true,
  },
  recommendation_eligibility_zero_candidates: {
    title: "ご案内できる参拝候補がまだありません",
    description: "現在の条件では、ご案内に必要な情報を確認できる神社が見つかりませんでした。",
    offerConcierge: true,
  },
  direction_zero_candidates: {
    title: "この方向の参拝候補が見つかりませんでした",
    description: "出発地点を変えると、見つかることがあります。",
    offerConcierge: false,
  },
  evidence_zero_candidates: {
    title: "参拝候補の情報を確認できませんでした",
    description: "しばらくしてから、もう一度お試しください。",
    offerConcierge: false,
  },
  backend_error: {
    title: "只今、確認できませんでした",
    description: "時間をおいて、もう一度お試しください。",
    offerConcierge: false,
  },
};

// ---------------------------------------------------------------------------
// 候補カード（Web の resolveCompassCandidatePresentation.ts と同じ判定）
// ---------------------------------------------------------------------------

export type CompassCandidateMeaning = {
  text: string;
  // history_theme は KAMI MUSUBI の解釈で、公式の事実として出さない。
  isKamiMusubiInterpretation: boolean;
};

export type CompassCandidateShrineFacts = {
  deityName: string | null;
  history: { typeLabel: string | null; content: string } | null;
};

function nonEmpty(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

// is_primary の最初の1件だけを「今のあなたとの接点」に使う。fallback は使わない。
export function resolveCompassCandidateMeaning(rec: CompassRecommendation): CompassCandidateMeaning | null {
  const facts = Array.isArray(rec.reason_facts) ? rec.reason_facts : [];
  for (const fact of facts) {
    if (!fact || typeof fact !== "object" || fact.is_primary !== true) continue;
    if (fact.type === "fallback") continue;
    const labelJa = nonEmpty(fact.label_ja);
    if (!labelJa) continue;
    if (fact.type === "history_theme") {
      return { text: `${labelJa}という文脈`, isKamiMusubiInterpretation: true };
    }
    return { text: labelJa, isKamiMusubiInterpretation: false };
  }
  return null;
}

// 神社詳細の「祭神・由緒」と同じ見出し。知らない値は内部の文字列を出さず、見出しなし。
const HISTORY_TYPE_LABELS: Record<string, string> = {
  official_origin: "由緒",
  founding: "創始",
  historical_event: "歴史",
  tradition: "伝承",
  regional_context: "地域史",
  editorial_summary: "要約",
};

export function resolveCompassCandidateShrineFacts(rec: CompassRecommendation): CompassCandidateShrineFacts | null {
  const facts = rec.shrine_facts;
  if (!facts || typeof facts !== "object") return null;
  const deityName = nonEmpty(facts.deity?.display_name);
  const content = nonEmpty(facts.history?.content);
  const historyType = facts.history?.history_type;
  const history = content
    ? { typeLabel: (historyType && HISTORY_TYPE_LABELS[historyType]) || null, content }
    : null;
  if (!deityName && !history) return null;
  return { deityName, history };
}

export function resolveCompassShrineId(rec: CompassRecommendation): string | null {
  const raw = rec.shrine_id;
  if (raw === null || raw === undefined) return null;
  const value = String(raw).trim();
  return value ? value : null;
}

export function formatCompassDistance(distanceM: number | null | undefined): string | null {
  if (typeof distanceM !== "number" || !Number.isFinite(distanceM) || distanceM < 0) return null;
  if (distanceM < 1000) return `約${Math.round(distanceM)}m`;
  return `約${(distanceM / 1000).toFixed(1)}km`;
}

// 経路の出発地には、正確な位置（現在地・駅名・住所）だけを使う。
// 都道府県の代表座標は実際の出発地ではないため、目的地だけの経路にする。
export function buildCompassRouteUrl(rec: CompassRecommendation, origin: UserOrigin | null): string | null {
  const destination = nonEmpty(rec.address) ?? nonEmpty(rec.name);
  if (!destination) return null;
  const params = [`api=1`, `destination=${encodeURIComponent(destination)}`];
  if (origin && origin.accuracy === "precise") {
    const payload = toOriginPayload(origin);
    if (payload) params.push(`origin=${payload.lat},${payload.lng}`);
  }
  return `https://www.google.com/maps/dir/?${params.join("&")}`;
}
