import { describe, expect, it } from "vitest";

import {
  buildEnShrineSections,
  distanceMeters,
  formatDistanceEn,
  pickEnFeatureWords,
  pickEnShrineBasics,
  type EnShrineBasics,
} from "../buildEnShrineDetailModel";

const shrine: EnShrineBasics = {
  id: 60,
  nameJa: "赤坂氷川神社",
  nameRomaji: "Akasaka Hikawa Jinja",
  address: "東京都港区赤坂6-10-12",
  lat: 35.6702,
  lng: 139.7357,
};

const story = { wordId: "T_IMPERIAL", labelEn: "imperial connection", slot: "history_culture" as const, sourceUrl: "https://example.jp/a", checkedOn: "2026-11-01" };
const sight = { wordId: "S_FOREST", labelEn: "sacred forest", slot: "scenery_experience" as const, sourceUrl: "https://example.jp/b", checkedOn: "2026-11-01" };

describe("buildEnShrineSections（英語の神社詳細の枠）", () => {
  it("2 神社名・所在地 → 4 歴史・文化 → 5 景観・季節・体験 → 6 参拝の情報 の順に並ぶ（1・3・7 は出さない）", () => {
    const sections = buildEnShrineSections({ shrine, featureWords: [sight, story], origin: { lat: 35.6812, lng: 139.7671 } });
    expect(sections.map((s) => s.kind)).toEqual(["name_location", "history_culture", "scenery_experience", "visit"]);
    expect(sections.map((s) => s.kind)).not.toContain("photo");
  });

  it("データの無い枠は出さない（歴史・文化が無ければ景観の枠だけ）", () => {
    const sections = buildEnShrineSections({ shrine, featureWords: [sight] });
    expect(sections.map((s) => s.kind)).toEqual(["name_location", "scenery_experience", "visit"]);
  });

  it("4 と 5 が両方とも空なら、その旨を出す枠を置く（推測の文で埋めない）", () => {
    const sections = buildEnShrineSections({ shrine, featureWords: [] });
    expect(sections.map((s) => s.kind)).toEqual(["name_location", "no_feature_words", "visit"]);
  });

  it("参拝の情報: 現在地があれば距離、Google マップのルートには出発地点を入れない", () => {
    const visit = buildEnShrineSections({ shrine, featureWords: [], origin: { lat: 35.6812, lng: 139.7671 } }).find(
      (s) => s.kind === "visit",
    );
    expect(visit).toMatchObject({ kind: "visit" });
    if (visit?.kind !== "visit") throw new Error("visit section missing");
    expect(visit.distanceText).toMatch(/^\d+(\.\d)? (m|km) away$/);
    expect(visit.routeUrl).toContain("https://www.google.com/maps/dir/");
    expect(visit.routeUrl).toContain("destination=35.6702%2C139.7357");
    expect(visit.routeUrl).not.toContain("origin=");
  });

  it("現在地が無ければ距離は出さず、ルートだけ。位置が無い神社は参拝の枠を出さない", () => {
    const noOrigin = buildEnShrineSections({ shrine, featureWords: [] }).find((s) => s.kind === "visit");
    expect(noOrigin).toMatchObject({ distanceText: null });
    const noLocation = buildEnShrineSections({ shrine: { ...shrine, lat: null, lng: null }, featureWords: [] });
    expect(noLocation.map((s) => s.kind)).not.toContain("visit");
  });
});

describe("pickEnShrineBasics / pickEnFeatureWords", () => {
  it("神社データから日本語名・ローマ字名・住所・位置を取り出す", () => {
    expect(
      pickEnShrineBasics({ name_jp: "赤坂氷川神社", name_romaji: "", address: "東京都", latitude: "35.1", longitude: 139.2 }, 60),
    ).toEqual({ id: 60, nameJa: "赤坂氷川神社", nameRomaji: null, address: "東京都", lat: 35.1, lng: 139.2 });
    expect(pickEnShrineBasics({ name_jp: "" }, 1)).toBeNull();
  });

  it("特徴語は枠と出典のあるものだけを取り出し、引用（evidence_quote）は持たない", () => {
    const words = pickEnFeatureWords({
      items: [
        { word_id: "T_IMPERIAL", label_en: "imperial connection", slot: "history_culture", source_url: "https://example.jp/a", checked_on: "2026-11-01", evidence_quote: "引用" },
        { word_id: "X", label_en: "no source", slot: "history_culture", source_url: "" },
        { word_id: "Y", label_en: "bad slot", slot: "other", source_url: "https://example.jp/y" },
        { word_id: "Z", label_en: "bad url", slot: "scenery_experience", source_url: "javascript:alert(1)" },
      ],
    });
    expect(words).toEqual([story]);
    expect(JSON.stringify(words)).not.toContain("引用");
    expect(pickEnFeatureWords(null)).toEqual([]);
  });
});

describe("距離", () => {
  it("東京駅から赤坂氷川神社まで約3km", () => {
    const m = distanceMeters({ lat: 35.6812, lng: 139.7671 }, { lat: 35.6702, lng: 139.7357 });
    expect(m).toBeGreaterThan(2500);
    expect(m).toBeLessThan(3500);
  });

  it("1km 未満は m、以上は km（小数1桁）", () => {
    expect(formatDistanceEn(850.4)).toBe("850 m away");
    expect(formatDistanceEn(3240)).toBe("3.2 km away");
  });
});
