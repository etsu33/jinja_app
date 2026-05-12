export type HeroTheme = "quiet" | "reset" | "relationship" | "work" | "money" | "default";

export const HERO_EYEBROW_LABELS = {
  need: "今の相談に近い方向の神社",
  compat: "今の相性に合いそうな神社",
} as const;

export const HERO_COMPAT_SUBTITLE = "生年月日の傾向を補助的に重ねると、比較の軸にしやすい候補です。";

export const HERO_THEME_SUBTITLES: Record<HeroTheme, string> = {
  quiet: "静かに整えたい感覚に近い方向として、今は重ねて見やすい候補です。",
  reset: "気持ちや流れを少し切り替えたい時に、入り口として見やすい候補です。",
  relationship: "相手との距離感や関係の受け取り方を見直したい時に、近い方向として見やすい候補です。",
  work: "働き方や次の動きを整理したい時に、比較しやすい候補です。",
  money: "お金まわりや余裕の感覚を整えたい時に、今は重ねて見やすい候補です。",
  default: "今の相談内容に近い方向として、この候補を軸にすると比較しやすそうです。",
};

export function getHeroThemeSubtitle(theme: HeroTheme): string {
  return HERO_THEME_SUBTITLES[theme];
}
