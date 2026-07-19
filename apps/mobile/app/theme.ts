export const colors = {
  paper: "#F6F3EE",
  primary: "#E24E33",
  accent: "#F2C94C",
  text: "#111",
  muted: "#555",
  border: "#e6e6e6",
  surfaceLight: "#fff",
  surfaceMuted: "#F4F4F5",
  textDark: "#111",
  textGray: "#666",
  textMuted: "#777",
  borderLight: "#eee",
  error: "#b00020",
  errorBackground: "#fff3f3",
  link: "#2f6ee5",
  favorite: "#E24E33",
} as const;

export const kamimusubiDark = {
  background: "#07101F",
  surface: "#101827",
  surfaceSoft: "#0B1424",
  border: "#384154",
  borderGold: "#8A6C32",
  borderGoldDark: "#6B5128",
  borderHeader: "#1E2A3A",
  borderMuted: "#2A3548",
  borderSoft: "#1A2336",
  gold: "#E0B963",
  goldSoft: "#D9C177",
  text: "#F7F0E3",
  muted: "#A99B80",
  mutedDark: "#8F846E",
  mutedSoft: "#C4B89A",
  navMuted: "#5A6478",
  outside: "#F4EFE3",
} as const;

export type AppColorKey = keyof typeof colors;
export type KamimusubiDarkColorKey = keyof typeof kamimusubiDark;

// Design Token v1 定義基盤: Mobile Platform Theme (Semantic Color実値)
// 正本: docs/design/design-token.md
// 既存の colors / kamimusubiDark (上記) は変更せず、kamimusubiDark の値を
// 再利用してSemantic Color Token (semanticColorTokens.ts) の実値を割り当てる。
//
// `satisfies PlatformColorTheme` により、SEMANTIC_COLOR_KEYSの全キーを
// 過不足なく満たすことをtscレベルで強制する
// (キーが1つでも欠けている、または余分なキーがあるとコンパイルエラーになる)。
// apps/mobileにはvitest実行環境が存在しない既存の問題があり、ランタイム
// テストでの契約検証はできないため、この型チェックが唯一の契約保証手段となる。
import type { PlatformColorTheme } from "./design/semanticColorTokens";

export const kamimusubiDarkSemanticTheme = {
  "background.base": kamimusubiDark.background,
  "background.subtle": kamimusubiDark.surfaceSoft,
  "surface.default": kamimusubiDark.surface,
  "surface.elevated": kamimusubiDark.surfaceSoft,
  "text.primary": kamimusubiDark.text,
  "text.secondary": kamimusubiDark.muted,
  "text.muted": kamimusubiDark.mutedSoft,
  "text.inverse": kamimusubiDark.background,
  "border.default": kamimusubiDark.border,
  "border.strong": kamimusubiDark.borderHeader,
  "border.focus": kamimusubiDark.gold,
  "action.primary": kamimusubiDark.gold,
  "action.primaryHover": kamimusubiDark.goldSoft,
  "action.primaryText": kamimusubiDark.background,
  "action.disabled": kamimusubiDark.mutedDark,
  // status.* はPhase 6監査で体系的な既存定義が確認できなかった領域。
  // status.error のみ app/login.tsx:167 の既存直書き値 (#FCA5A5) を再利用し、
  // 孤立していたエラー色をSemantic Tokenへ接続する。他は暫定候補値。
  "status.success": kamimusubiDark.gold,
  "status.warning": kamimusubiDark.goldSoft,
  "status.error": "#FCA5A5",
  "status.info": kamimusubiDark.muted,
  "premium.accent": kamimusubiDark.gold,
  "premium.surface": kamimusubiDark.surface,
  "premium.border": kamimusubiDark.borderGold,
  // overlay.default は reflection-history/index.tsx:431 の既存値を採用
  // (2箇所で不統一だった透過率のうち、より広い透過率のものを採用)
  "overlay.default": "rgba(7, 16, 31, 0.82)",
} satisfies PlatformColorTheme;
