export const NEED_TAG_LABEL_MAP: Record<string, string> = {
  money: "金運や巡りを整えたい",
  courage: "前に進むきっかけがほしい",
  career: "仕事や転機を見直したい",
  mental: "気持ちを整理したい",
  rest: "静かに休みたい",
  love: "良縁や関係性を整えたい",
  study: "学びや集中を整えたい",

  relationship: "人間関係を整えたい",
  work: "仕事や役割を見直したい",
  restart: "流れを切り替えたい",
  healing: "静かに回復したい",
  decision: "次の選択を整理したい",
  challenge: "前向きに進みたい",
  gratitude: "感謝を言葉にしたい",
  protection: "安心できる感覚を持ちたい",
  learning: "学びや成長を深めたい",
};

export function toNeedTagLabel(tag: string): string {
  return NEED_TAG_LABEL_MAP[tag] ?? tag;
}

export function toNeedTagLabels(tags: string[]): string[] {
  return tags.map(toNeedTagLabel);
}
