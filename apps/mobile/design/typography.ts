// Mobile Typography Token の正本 (docs/design/design-token.md「Typography」節)。
//
// 2026-11 決定。それ以前は Color / Spacing / Radius / Shadow / Component の5カテゴリが
// Token 化済みで、Typography だけが各画面の直接指定のまま残っていた。実測では
// fontSize が20種 (10〜48)、fontWeight は246スタイル中190が700以上という分布で、
// 「小さい文字 + 極太」という iOS では読みにくい組み合わせが基準になっていた。
//
// 本 Token は Apple HIG の標準スケール (Body 17 / Headline 17 semibold /
// Subhead 15 / Footnote 13 / Caption 12 / Title2 22) に合わせる。
// 本文は 17pt regular を既定とし、太さは意味の強弱にだけ使う。
//
// 対象外: 絵文字・記号・数値を表示するスタイル (⛩ ♡ ↑ ✓ やカウント値など)。
// これらは文字サイズではなく図形の寸法であり、本スケールに載せない。

export const SEMANTIC_TYPOGRAPHY_KEYS = [
  "display",
  "question",
  "heading",
  "subheading",
  "title",
  "body",
  "bodyStrong",
  "subhead",
  "label",
  "footnote",
  "footnoteStrong",
  "caption",
  "eyebrow",
  "button",
  "buttonCompact",
] as const;

export type SemanticTypographyKey = (typeof SEMANTIC_TYPOGRAPHY_KEYS)[number];

export type TextStyleToken = {
  fontSize: number;
  fontWeight: "400" | "500" | "600" | "700";
  lineHeight?: number;
  letterSpacing?: number;
};

export type PlatformTypographyTheme = Record<SemanticTypographyKey, TextStyleToken>;

export const typography: PlatformTypographyTheme = {
  // 画面最上位の大見出し。1画面に1つまで。
  display: { fontSize: 32, fontWeight: "700", lineHeight: 42, letterSpacing: 0.2 },
  // Guided Journey の質問見出し (ios-ui-spec-v2.md 13節: 24〜30px /
  // Medium〜Semibold / Line Height 1.35〜1.5)。質問文を画面の主役にする。
  question: { fontSize: 26, fontWeight: "600", lineHeight: 38 },
  // セクションの大見出し (HIG Title2)。
  heading: { fontSize: 22, fontWeight: "700", lineHeight: 30 },
  // セクション見出し (HIG Title3)。
  subheading: { fontSize: 20, fontWeight: "600", lineHeight: 28 },
  // カード見出し・リスト項目名 (HIG Headline)。
  title: { fontSize: 17, fontWeight: "600", lineHeight: 24 },
  // 本文 (HIG Body)。読ませる文章はすべてこれ。
  body: { fontSize: 17, fontWeight: "400", lineHeight: 26 },
  // 本文と同じ大きさで強調する場合 (入力文字、主CTAのラベルなど)。
  bodyStrong: { fontSize: 17, fontWeight: "600", lineHeight: 26 },
  // 補助的な説明文 (HIG Subhead)。本文より一段弱い。
  subhead: { fontSize: 15, fontWeight: "400", lineHeight: 23 },
  // フォームラベル・選択肢の文字。
  label: { fontSize: 15, fontWeight: "500", lineHeight: 21 },
  // 注記・日時・住所など (HIG Footnote)。
  footnote: { fontSize: 13, fontWeight: "400", lineHeight: 19 },
  // 同じ大きさで強調する短い語 (タグ、ピル、順位など)。
  footnoteStrong: { fontSize: 13, fontWeight: "600", lineHeight: 19 },
  // 最小の補足 (HIG Caption1)。これより小さい文字は使わない。
  caption: { fontSize: 12, fontWeight: "500", lineHeight: 17 },
  // セクション先頭の小見出しラベル。字間を開けて区切りを示す。
  eyebrow: { fontSize: 12, fontWeight: "600", lineHeight: 16, letterSpacing: 1.2 },
  // ボタン内のテキスト。
  button: { fontSize: 17, fontWeight: "600" },
  buttonCompact: { fontSize: 15, fontWeight: "600" },
};
