export type HeroTheme =
  | "quiet"
  | "nature"
  | "reset"
  | "less_crowded"
  | "nearby"
  | "classic"
  | "relationship"
  | "work"
  | "money"
  | "default";

export const HERO_EYEBROW_LABELS = {
  need: "今の相談に近い方向の神社",
  compat: "今の相性に合いそうな神社",
} as const;

export const HERO_COMPAT_SUBTITLE = "生年月日の傾向を補助的に重ねると、比較の軸にしやすい候補です。";

export const HERO_THEME_SUBTITLES: Record<HeroTheme, string> = {
  quiet: "静かに落ち着きたい相談として、騒がしさよりも気持ちを整えやすい候補です。",
  nature: "自然の中で整えたい相談として、緑や空気感を受け取りやすい候補です。",
  reset: "気持ちを切り替えたい相談として、今の流れを変える入口にしやすい候補です。",
  less_crowded: "人混みを避けたい相談として、落ち着いて向き合いやすい候補です。",
  nearby: "無理なく行ける場所を探したい相談として、動き出しやすい候補です。",
  classic: "初めてでも選びやすい相談として、安心して比較しやすい候補です。",
  relationship: "関係性を見直したい相談として、相手との距離感を整えやすい候補です。",
  work: "仕事や次の動きを整理したい相談として、判断軸を立て直しやすい候補です。",
  money: "お金や巡りを整えたい相談として、流れを見直す入口にしやすい候補です。",
  default: "今回の相談内容に近い方向として、まず比較の軸にしやすい候補です。",
};

export function getHeroThemeSubtitle(theme: HeroTheme): string {
  return HERO_THEME_SUBTITLES[theme];
}
