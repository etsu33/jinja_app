import { describe, expect, it } from "vitest";

import type { ConciergeReasonFact } from "@/lib/api/concierge";
import { adaptReasonFactsForViewModel } from "../adaptReasonFactsForViewModel";
import { buildRecommendationReasonViewModel } from "../buildRecommendationReasonViewModel";

function fact(type: string, label: string, overrides: Partial<ConciergeReasonFact> = {}): ConciergeReasonFact {
  return { type, label, evidence: [`${type}:${label}`], score: 1, is_primary: true, ...overrides };
}

describe("adaptReasonFactsForViewModel", () => {
  it.each([
    ["element", "火", { primary_axis: "element", matched_element: "火" }],
    ["need_tag", "仕事", { primary_axis: "need", matched_need_tags: ["仕事"] }],
    ["user_selected_tag", "厄除け", { primary_axis: "need", matched_need_tags: ["厄除け"] }],
    ["goriyaku_tag", "勝運", { primary_axis: "benefit", shrine_benefit: "勝運" }],
    ["history_theme", "再出発", { primary_axis: "feature", shrine_feature: "再出発" }],
    ["text_hint", "静かな境内", { primary_axis: "feature", shrine_feature: "静かな境内" }],
    ["visit_style", "自然", { primary_axis: "feature", visit_fit: "自然" }],
    ["fallback", "近隣候補から選定", { primary_axis: "fallback", fallback_reason: "近隣候補から選定" }],
  ])("%s Primaryを既存表示slotへ写像する", (type, label, expected) => {
    expect(adaptReasonFactsForViewModel([fact(type, label)])).toEqual(expect.objectContaining(expected));
  });

  it("unknown typeをfallbackへ変換せず無視する", () => {
    expect(adaptReasonFactsForViewModel([fact("unknown", "未知")])).toBeNull();
  });

  it("is_primaryが無ければscoreや配列順からPrimaryを作らない", () => {
    expect(adaptReasonFactsForViewModel([
      fact("element", "火", { is_primary: undefined, score: 999 }),
      fact("need_tag", "仕事", { is_primary: undefined, score: 1 }),
    ])).toBeNull();
  });

  it("複数Primaryでもscoreで再ランキングせず、最初の明示Primaryを採用する", () => {
    const adapted = adaptReasonFactsForViewModel([
      fact("need_tag", "仕事", { score: 1 }),
      fact("element", "火", { score: 999 }),
    ]);
    expect(adapted).toEqual(expect.objectContaining({ primary_fact_type: "need_tag", primary_fact_label: "仕事" }));
  });
});

describe("buildRecommendationReasonViewModel Backend fact consumption", () => {
  const build = (type: string, label: string) => buildRecommendationReasonViewModel({
    rec: { id: 999, name: "契約神社" },
    reasonFacts: [fact(type, label)],
    index: 0,
    mode: "need",
    needTags: [],
  });

  it.each([
    ["need_tag", "仕事"],
    ["history_theme", "再出発"],
  ])("%s Primaryのlabelがvisible text用ViewModelへ届く", (type, label) => {
    const vm = build(type, label);
    expect([vm.list.primaryPhrase, vm.hero.catchCopy, vm.detail.shrineMeaning].join(" ")).toContain(label);
  });

  const buildWith = (
    reasonFact: ConciergeReasonFact,
    rec: Record<string, unknown> = {},
    extra: { birthdate?: string | null; mode?: string } = {},
  ) => buildRecommendationReasonViewModel({
    rec: { id: 999, name: "契約神社", ...rec },
    reasonFacts: [reasonFact],
    index: 0,
    mode: extra.mode ?? "need",
    birthdate: extra.birthdate ?? null,
    needTags: [],
  });
  // 画面に出る文だけを見る(debug の reasonKeys などは除く)。
  const visibleOf = (vm: ReturnType<typeof buildWith>) => JSON.stringify({ hero: vm.hero, list: vm.list, detail: vm.detail, rank: vm.rank });
  const ELEMENT = fact("element", "element", { label_ja: "生年月日との相性" });
  const VISIT_STYLE = fact("visit_style", "visit_style", { label_ja: "参拝スタイル" });
  const DISTANCE_PRIMARY = "今回はまず動きやすさを優先して、この神社が候補に入っています。";
  const DISTANCE_CATCH = "まず行きやすさを優先したい時の神社";

  it("element: 神社に登録された五行があれば、その名前で相性の文にする", () => {
    const vm = buildWith(ELEMENT, { astro_elements: ["火"] }, { birthdate: "1990-01-01" });
    expect(vm.list.primaryPhrase).toBe("生年月日から見た「火」の要素との相性が強く重なるため、この神社が候補に入っています。");
    expect(visibleOf(vm)).not.toContain("element");
    expect(visibleOf(vm)).not.toContain("「生年月日との相性」");
  });

  it("element: 五行が無ければ既定の文「生年月日との相性を軸に選びやすい候補です」にする", () => {
    const vm = buildWith(ELEMENT, {}, { birthdate: "1990-01-01" });
    expect(vm.list.primaryPhrase).toBe("生年月日との相性を軸に選びやすい候補です");
    expect(visibleOf(vm)).not.toContain("element");
  });

  it("element: 神社の五行が英字だけ(fire)のときは名前を入れず、element の既定の文にする", () => {
    const vm = buildWith(ELEMENT, { astro_elements: ["fire"] }, { birthdate: "1990-01-01" });
    expect(vm.list.primaryPhrase).toBe("生年月日との相性を軸に選びやすい候補です");
    expect(visibleOf(vm)).not.toContain("fire");
  });

  it("element(生年月日なし): 行きやすさ優先の文にならず、element の既定の文になる", () => {
    const vm = buildWith(ELEMENT);
    expect(vm.list.primaryPhrase).toBe("生年月日との相性を軸に選びやすい候補です");
    expect(vm.list.primaryPhrase).not.toBe(DISTANCE_PRIMARY);
    expect(vm.hero.catchCopy).toBe("相性から無理なく選びたい時の神社");
    expect(vm.hero.catchCopy).not.toBe(DISTANCE_CATCH);
  });

  it("visit_style: 選んだ参拝スタイルの日本語の文を使う", () => {
    const vm = buildWith(VISIT_STYLE, { breakdown_detail: { features: { visit_style: { matched_tags: ["quiet"] } } } });
    expect(vm.list.primaryPhrase).toBe("選んだ参拝スタイルの「静かに落ち着いて過ごしたい気持ち」にも合うため、この神社が候補に入っています。");
    expect(vm.hero.catchCopy).toBe("静かに落ち着いて過ごしたい時の神社");
    expect(visibleOf(vm)).not.toContain("参拝スタイル」");
    expect(visibleOf(vm)).not.toContain("visit_style");
  });

  it("visit_style: データが無ければ「選んだ参拝の好みに合うため…」にし、行きやすさ優先の文にしない", () => {
    const vm = buildWith(VISIT_STYLE);
    expect(vm.list.primaryPhrase).toBe("選んだ参拝の好みに合うため、この神社が候補に入っています。");
    expect(vm.hero.catchCopy).not.toBe(DISTANCE_CATCH);
    expect(visibleOf(vm)).not.toContain("参拝スタイル");
  });

  it.each([
    ["need_tag", "相談内容と一致するため、この神社が候補に入っています。"],
    ["user_selected_tag", "選んだ条件と一致するため、この神社が候補に入っています。"],
    ["goriyaku_tag", "ご利益が相談に重なるため、この神社が候補に入っています。"],
    ["history_theme", "意味・特徴が相談に重なるため、この神社が候補に入っています。"],
    ["text_hint", "意味・特徴が相談に重なるため、この神社が候補に入っています。"],
  ])("%s の名前が英字だけ(quiet)のときは、名前だけを外した同じ種類の文にし、行きやすさ優先の文にしない", (type, expected) => {
    const vm = buildWith(fact(type, "quiet", { label_ja: "quiet" }));
    expect(vm.list.primaryPhrase).toBe(expected);
    expect(vm.list.primaryPhrase).not.toBe(DISTANCE_PRIMARY);
    expect(vm.hero.catchCopy).not.toBe(DISTANCE_CATCH);
    expect(visibleOf(vm)).not.toContain("quiet");
  });

  it("user_selected_tag: 名前入りの文は「選んだ「X」と一致するため…」にする", () => {
    const vm = buildWith(fact("user_selected_tag", "仕事運・出世", { label_ja: "仕事運・出世" }));
    expect(vm.list.primaryPhrase).toBe("選んだ「仕事運・出世」と一致するため、この神社が候補に入っています。");
  });

  it("fallback: 本当に fallback のときは、近さで選んだ候補の文になる", () => {
    const vm = buildWith(fact("fallback", "fallback", { label_ja: "近い候補" }));
    expect(vm.list.primaryPhrase).toBe(DISTANCE_PRIMARY);
    expect(vm.hero.catchCopy).toBe(DISTANCE_CATCH);
    expect(visibleOf(vm)).not.toContain("「近い候補」");
  });

  it("history_theme Primaryを詳細meaning文言へ反映する", () => {
    const vm = build("history_theme", "再出発");
    expect(vm.detail.shrineMeaning).toContain("再出発");
  });

  it("is_primaryなしではfact labelをvisible textへ採用しない", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: { id: 999, name: "契約神社" },
      reasonFacts: [fact("element", "Frontendで推測禁止", { is_primary: undefined, score: 999 })],
      index: 0,
      mode: "need",
      needTags: [],
    });
    expect(JSON.stringify(vm)).not.toContain("Frontendで推測禁止");
  });
});

describe("表示用の名前(label_ja)", () => {
  const build = (reasonFacts: ConciergeReasonFact[], needTags: string[] = []) => buildRecommendationReasonViewModel({
    rec: { id: 999, name: "契約神社" },
    reasonFacts,
    index: 0,
    mode: "need",
    needTags,
  });
  const visibleText = (vm: ReturnType<typeof build>) => JSON.stringify({ hero: vm.hero, list: vm.list, detail: vm.detail, rank: vm.rank });

  it("label_ja を表示用に渡し、判定用の shrine_benefit は label のまま残す", () => {
    expect(adaptReasonFactsForViewModel([fact("goriyaku_tag", "rest", { label_ja: "休息" })])).toEqual(expect.objectContaining({
      primary_axis: "benefit",
      shrine_benefit: "rest",
      shrine_benefit_display_label: "休息",
      primary_fact_label: "rest",
      primary_fact_display_label: "休息",
    }));
  });

  it("label_ja が無いときは label を表示用に使う", () => {
    expect(adaptReasonFactsForViewModel([fact("goriyaku_tag", "勝運")])).toEqual(expect.objectContaining({
      shrine_benefit_display_label: "勝運",
      primary_fact_display_label: "勝運",
    }));
  });

  it.each(["quiet", "goriyaku_tag:501", "need-tag_2"])("英字・数字・記号だけの名前(%s)は表示用の名前を持たない", (label) => {
    expect(adaptReasonFactsForViewModel([fact("goriyaku_tag", label, { label_ja: label })])).toEqual(expect.objectContaining({
      shrine_benefit: label,
      shrine_benefit_display_label: null,
      primary_fact_display_label: null,
    }));
  });

  it("日本語を含む名前(IT守護)はそのまま表示用に使う", () => {
    expect(adaptReasonFactsForViewModel([fact("goriyaku_tag", "it_guard", { label_ja: "IT守護" })])).toEqual(
      expect.objectContaining({ shrine_benefit_display_label: "IT守護" }),
    );
  });

  it("label: rest / label_ja: 休息 のとき、画面の文に「rest」が出ず「休息」が出る", () => {
    const vm = build([fact("goriyaku_tag", "rest", { label_ja: "休息" })], ["rest"]);
    expect(vm.list.primaryPhrase).toContain("休息");
    expect(visibleText(vm)).not.toContain("rest");
  });

  it.each([
    ["visit_style", "quiet"],
    ["text_hint", "quiet"],
    ["history_theme", "mental"],
    ["need_tag", "goriyaku_tag:501"],
  ])("%s の label_ja が英字だけ(%s)のとき、英語を出さず名前を入れない文になる", (type, label) => {
    const vm = build([fact(type, label, { label_ja: label })]);
    expect(vm.list.primaryPhrase).toBeTruthy();
    expect(visibleText(vm)).not.toContain(label);
    expect(visibleText(vm)).not.toContain("「」");
  });

  it("history_theme / text_hint の日本語名は詳細の意味文(detail.shrineMeaning)に入る", () => {
    const vm = build([fact("text_hint", "mental", { label_ja: "不安・心" })], ["mental"]);
    expect(vm.detail.shrineMeaning).toContain("「不安・心」という意味・特徴を持つ場所で");
    expect(visibleText(vm)).not.toContain("mental");
  });

  it("visit_style は分類名「参拝スタイル」を詳細の意味文にも入れない", () => {
    const vm = build([fact("visit_style", "visit_style", { label_ja: "参拝スタイル" })]);
    expect(visibleText(vm)).not.toContain("参拝スタイル");
    expect(visibleText(vm)).not.toContain("visit_style");
  });

  it("判定用の shrine_feature があっても表示名が無いときは、詳細の意味文に内部名を使わない", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: { id: 999, name: "契約神社", reason_facts: { primary_axis: "need", shrine_feature: "quiet" } },
      index: 0,
      mode: "need",
      needTags: ["career"],
    });
    expect(visibleText(vm)).not.toContain("quiet");
  });

  it("element / fallback の日本語名は主な理由の文に入れない", () => {
    const element = build([fact("element", "element", { label_ja: "生年月日との相性" })]);
    expect(element.list.primaryPhrase).not.toContain("「生年月日との相性」");
    const fallback = build([fact("fallback", "fallback", { label_ja: "近い候補" })]);
    expect(fallback.list.primaryPhrase).not.toBe("近い候補");
    expect(visibleText(fallback)).not.toContain("fallback");
  });

  it("buildBenefitMeaningLabel に日本語名が渡ると、用意された言い回しが選ばれる", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: {
        id: 999,
        name: "契約神社",
        reason_facts: { primary_axis: "need", shrine_benefit: "career", shrine_benefit_display_label: "転機・仕事" },
      },
      index: 0,
      mode: "need",
      needTags: ["career"],
    });
    expect(visibleText(vm)).toContain("仕事の流れを立て直す");
    expect(visibleText(vm)).not.toContain("career");
  });

  it("判定用の shrine_benefit があっても表示名が無いときは、内部名を言い回しに使わない", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: { id: 999, name: "契約神社", reason_facts: { primary_axis: "need", shrine_benefit: "career" } },
      index: 0,
      mode: "need",
      needTags: ["career"],
    });
    expect(visibleText(vm)).not.toContain("career");
    expect(vm.list.primaryPhrase).toContain("仕事や転機を見直したい");
  });
});
