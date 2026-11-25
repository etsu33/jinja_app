import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";

const getRefreshTokenMock = vi.fn();
const postMock = vi.fn();
const postAuthMock = vi.fn();

vi.mock("../authTokens", () => ({
  getRefreshToken: (...args: unknown[]) => getRefreshTokenMock(...args),
}));

vi.mock("../http", async () => {
  const actual = await vi.importActual<typeof import("../http")>("../http");
  return {
    ...actual,
    post: (...args: unknown[]) => postMock(...args),
    postAuth: (...args: unknown[]) => postAuthMock(...args),
  };
});

import { HttpError, UnauthenticatedError } from "../http";
import {
  COMPASS_NOTICES,
  COMPASS_PURPOSES_ORDERED,
  COMPASS_PURPOSE_LABELS_JA,
  buildCompassRouteUrl,
  describeReferenceDirections,
  fetchCompassRecommendations,
  formatBirthdate,
  formatCompassDistance,
  getDirectionNote,
  getDirectionStatusLabel,
  isValidBirthdate,
  parseBirthdate,
  resolveCompassCandidateMeaning,
  resolveCompassCandidateShrineFacts,
  resolveCompassShrineId,
  type CompassRecommendationsResponse,
} from "../compass";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

const deviceOrigin = { latitude: 35.68, longitude: 139.76, source: "device" as const, displayName: "現在地", accuracy: "precise" as const };
const prefectureOrigin = { latitude: 35.69, longitude: 139.69, source: "prefecture" as const, displayName: "東京都", accuracy: "approximate" as const };

const successResponse: CompassRecommendationsResponse = {
  state: "recommendation_success",
  purpose: "career",
  direction_context: {
    targetDate: "2026-11-25",
    targetYear: 2026,
    solarMonthIndex: 10,
    referenceDirections: ["北東"],
    calculationMethod: "annual_monthly_kyusei_v1",
    note: "",
  },
  recommendation_instance_id: "rec-1",
  recommendations: [{ shrine_id: 12, name: "乃木神社", address: "東京都港区赤坂8-11-27" }],
  distance_stage_km: 15,
  direction_candidate_count: 4,
  distance_candidate_count: 2,
};

describe("目的", () => {
  it("need_tag の15分類をすべて、重複なく並べる", () => {
    expect(COMPASS_PURPOSES_ORDERED).toHaveLength(15);
    expect(new Set(COMPASS_PURPOSES_ORDERED).size).toBe(15);
    for (const purpose of COMPASS_PURPOSES_ORDERED) {
      expect(COMPASS_PURPOSE_LABELS_JA[purpose]).toBeTruthy();
    }
  });

  it("Web と同じ表示名を使う", () => {
    const web = readFileSync(resolve(mobileRoot, "../web/src/features/compass/compassPurposes.ts"), "utf8");
    for (const [purpose, label] of Object.entries(COMPASS_PURPOSE_LABELS_JA)) {
      expect(web).toContain(`${purpose}: "${label}"`);
    }
  });
});

describe("生年月日", () => {
  const today = new Date(2026, 10, 25);

  it("YYYY-MM-DD を分けて読み、組み立て直す", () => {
    expect(parseBirthdate("1990-04-05")).toEqual({ year: "1990", month: "04", day: "05" });
    expect(parseBirthdate("不正")).toEqual({ year: "", month: "", day: "" });
    expect(formatBirthdate({ year: "1990", month: "4", day: "5" })).toBe("1990-04-05");
  });

  it("存在しない日付と未来の日付は受け付けない", () => {
    expect(isValidBirthdate({ year: "2000", month: "2", day: "29" }, today)).toBe(true);
    expect(isValidBirthdate({ year: "1900", month: "2", day: "29" }, today)).toBe(false);
    expect(isValidBirthdate({ year: "1990", month: "13", day: "1" }, today)).toBe(false);
    expect(isValidBirthdate({ year: "1990", month: "4", day: "31" }, today)).toBe(false);
    expect(isValidBirthdate({ year: "2027", month: "1", day: "1" }, today)).toBe(false);
    expect(isValidBirthdate({ year: "", month: "", day: "" }, today)).toBe(false);
  });
});

describe("方位の表示", () => {
  it("計算方法ごとに説明を分け、知らない値には見出しを付けない", () => {
    expect(getDirectionNote("annual_monthly_kyusei_v1")).toContain("年盤と月盤の両方で重なる");
    expect(getDirectionNote("monthly_kyusei_v1")).toContain("今月の月盤を参考にした");
    expect(getDirectionStatusLabel("annual_monthly_kyusei_v1")).toBe("年盤・月盤 共通");
    expect(getDirectionStatusLabel("monthly_kyusei_v1")).toBe("今月の月盤を参考");
    expect(getDirectionStatusLabel("daily")).toBeNull();
  });

  it("方位を文でも伝える", () => {
    expect(describeReferenceDirections(["北東", "南"])).toBe("今月意識したい方向: 北東・南");
    expect(describeReferenceDirections([])).toBe("今月意識したい方向は算出されていません");
  });

  it("方位なし・候補なし・通信失敗をそれぞれ別の文言にする", () => {
    const titles = Object.values(COMPASS_NOTICES).map((notice) => notice.title);
    expect(new Set(titles).size).toBe(titles.length);
    expect(COMPASS_NOTICES.no_common_direction.offerConcierge).toBe(true);
    expect(COMPASS_NOTICES.recommendation_eligibility_zero_candidates.offerConcierge).toBe(true);
    expect(COMPASS_NOTICES.backend_error.offerConcierge).toBe(false);
  });
});

describe("候補カード", () => {
  it("is_primary の最初の1件を接点にし、fallback は使わない", () => {
    expect(
      resolveCompassCandidateMeaning({
        shrine_id: 1,
        reason_facts: [
          { type: "fallback", label_ja: "近い候補", is_primary: true },
          { type: "need_tag", label_ja: "仕事の転機", is_primary: false },
          { type: "goriyaku_tag", label_ja: "開運", is_primary: true },
        ],
      }),
    ).toEqual({ text: "開運", isKamiMusubiInterpretation: false });
    expect(resolveCompassCandidateMeaning({ shrine_id: 1, reason_facts: [] })).toBeNull();
  });

  it("history_theme は KAMI MUSUBI の解釈として示す", () => {
    expect(
      resolveCompassCandidateMeaning({
        shrine_id: 1,
        reason_facts: [{ type: "history_theme", label_ja: "武家の信仰", is_primary: true }],
      }),
    ).toEqual({ text: "武家の信仰という文脈", isKamiMusubiInterpretation: true });
  });

  it("祭神・由緒は有るものだけ返し、知らない種類には見出しを付けない", () => {
    expect(
      resolveCompassCandidateShrineFacts({
        shrine_id: 1,
        shrine_facts: { deity: { display_name: "乃木希典" }, history: { history_type: "official_origin", content: "由緒の本文" } },
      }),
    ).toEqual({ deityName: "乃木希典", history: { typeLabel: "由緒", content: "由緒の本文" } });
    expect(
      resolveCompassCandidateShrineFacts({
        shrine_id: 1,
        shrine_facts: { history: { history_type: "unknown_type", content: "本文" } },
      }),
    ).toEqual({ deityName: null, history: { typeLabel: null, content: "本文" } });
    expect(resolveCompassCandidateShrineFacts({ shrine_id: 1, shrine_facts: {} })).toBeNull();
  });

  it("神社の識別子は shrine_id だけを使う", () => {
    expect(resolveCompassShrineId({ shrine_id: 12, id: 99 })).toBe("12");
    expect(resolveCompassShrineId({ shrine_id: "" })).toBeNull();
  });

  it("距離をメートルとキロで出し分ける", () => {
    expect(formatCompassDistance(850)).toBe("約850m");
    expect(formatCompassDistance(12345)).toBe("約12.3km");
    expect(formatCompassDistance(null)).toBeNull();
  });

  it("経路の出発地には正確な位置だけを使う", () => {
    const rec = { shrine_id: 1, name: "乃木神社", address: "東京都港区赤坂8-11-27" };
    expect(buildCompassRouteUrl(rec, deviceOrigin)).toBe(
      `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(rec.address)}&origin=35.68,139.76`,
    );
    expect(buildCompassRouteUrl(rec, prefectureOrigin)).toBe(
      `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(rec.address)}`,
    );
    expect(buildCompassRouteUrl({ shrine_id: 1 }, deviceOrigin)).toBeNull();
  });
});

describe("fetchCompassRecommendations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("ログインしていなければトークンを付けずに、目的・生年月日・出発地点だけを送る", async () => {
    getRefreshTokenMock.mockResolvedValue(null);
    postMock.mockResolvedValue(successResponse);

    const result = await fetchCompassRecommendations({ purpose: "career", birthdate: "1990-04-05", origin: deviceOrigin });

    expect(result).toEqual({ ok: true, response: successResponse });
    expect(postAuthMock).not.toHaveBeenCalled();
    expect(postMock).toHaveBeenCalledWith("/compass/recommendations/", {
      purpose: "career",
      birthdate: "1990-04-05",
      origin: { lat: 35.68, lng: 139.76 },
    });
  });

  it("ログイン中はトークンを付け、使えなければ付けずに送り直す", async () => {
    getRefreshTokenMock.mockResolvedValue("refresh");
    postAuthMock.mockResolvedValue(successResponse);
    await fetchCompassRecommendations({ purpose: "career", birthdate: "1990-04-05", origin: deviceOrigin });
    expect(postAuthMock).toHaveBeenCalledTimes(1);
    expect(postMock).not.toHaveBeenCalled();

    postAuthMock.mockRejectedValue(new UnauthenticatedError());
    postMock.mockResolvedValue(successResponse);
    const result = await fetchCompassRecommendations({ purpose: "career", birthdate: "1990-04-05", origin: deviceOrigin });
    expect(result.ok).toBe(true);
    expect(postMock).toHaveBeenCalledTimes(1);
  });

  it("400 でも本文が結果の形なら結果として扱う", async () => {
    getRefreshTokenMock.mockResolvedValue(null);
    const invalid = { ...successResponse, state: "invalid_purpose", direction_context: null, recommendations: [] };
    postMock.mockRejectedValue(new HttpError(400, "HTTP 400", JSON.stringify(invalid)));

    const result = await fetchCompassRecommendations({ purpose: "career", birthdate: "1990-04-05", origin: deviceOrigin });

    expect(result).toEqual({ ok: true, response: invalid });
  });

  it("通信失敗・500・形の違う応答は失敗にする", async () => {
    getRefreshTokenMock.mockResolvedValue(null);

    postMock.mockRejectedValue(new HttpError(500, "HTTP 500", "{}"));
    expect(await fetchCompassRecommendations({ purpose: "career", birthdate: "1990-04-05", origin: deviceOrigin })).toEqual({ ok: false });

    postMock.mockRejectedValue(new TypeError("Network request failed"));
    expect(await fetchCompassRecommendations({ purpose: "career", birthdate: "1990-04-05", origin: deviceOrigin })).toEqual({ ok: false });

    postMock.mockResolvedValue({ state: "unknown" });
    expect(await fetchCompassRecommendations({ purpose: "career", birthdate: "1990-04-05", origin: deviceOrigin })).toEqual({ ok: false });
  });
});

describe("画面", () => {
  const screen = readFileSync(resolve(mobileRoot, "app/compass/index.tsx"), "utf8");
  const home = readFileSync(resolve(mobileRoot, "app/(tabs)/index.tsx"), "utf8");
  const layout = readFileSync(resolve(mobileRoot, "app/_layout.tsx"), "utf8");

  it("コンパスに相談文の入力を置かない(相談はコンシェルジュの役割)", () => {
    expect(screen).not.toContain("相談内容");
    expect(screen).not.toMatch(/multiline/);
  });

  it("ホームからタブを増やさずに開ける", () => {
    expect(home).toContain('router.push({ pathname: "/compass", params: { ref: "home" } })');
    expect(layout).toContain('"compass/index": "コンパス"');
  });

  it("神社詳細へ shrine_id で進む", () => {
    expect(screen).toContain("router.push(`/shrines/${shrineId}`)");
  });
});
