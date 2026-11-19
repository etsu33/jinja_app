// Mobile Color正本 (docs/design/design-token.md Migration方針 5)
// - colors: Light基調の初期パレット。2026-07時点では利用範囲が限定的。
// - kamimusubiDarkSemanticTheme: 共通Buttonを通じて主要画面から参照される。
// - kamimusubiDark: 現行Mobile全画面が実際に参照するDark基調の正本Primitive。
// - kamimusubiDark: 現行Mobile全画面が実際に参照するDark基調の正本Primitive。
//   Color Primitiveの実質的な正本はこちら。
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
  // Visual Direction: Dark Forest (森影) — 近黒緑からモスチャコールへ至る基盤。
  // 旧Navy基調 (#07101F 系) からの改訂。狙いは「静かな鎮守の杜の参道」であり、
  // ホラー/ゴシック、および黒×金のラグジュアリー表現は明確に対象外とする。
  // 奥行きは装飾やエフェクトではなく、背景・面・浮き面の明度差 (大気遠近) で作る。

  // ---- Foundation: near-black green -> deep moss charcoal ----
  // 明度は background < surfaceSoft < surface < surfaceRaised の単調増加。
  // 旧実装では surfaceSoft(#0B1424) が surface(#101827) より暗いまま
  // surface.elevated に割り当てられ、「浮き面ほど明るい」順序が逆転していた
  // (tokens.css の該当コメントが自認)。本改訂で surfaceRaised を追加し、
  // 背景 / カード面 / 浮き面の分離を明度順に回復させる。
  background: "#0A0F0C",
  surfaceSoft: "#0E1410",
  surface: "#131A15",
  surfaceRaised: "#1A231C",

  // ---- Border: muted olive-gray ----
  // 線は主張させない。面の境界は第一に明度差で示し、borderは補助に留める。
  borderSoft: "#1C241E",
  borderHeader: "#222B24",
  borderMuted: "#28322A",
  border: "#333D31",
  // border.strong 用。旧実装は border.strong に borderHeader(#1E2A3A) を
  // 割り当てており、border.default(#384154) より暗く「強い線ほど目立つ」
  // 関係が逆転していた。default より明るい段階をここで用意する。
  borderStrong: "#465043",
  // 金枠は「褪せた鎮守の金具」。彩度を落とし、装飾ではなく格式の記号として扱う。
  borderAccent: "#7A6438",
  borderAccentDark: "#5C4B2A",

  // ---- Accent: restrained shrine-gold ----
  // 旧 gold(#E0B963) は彩度が高くラグジュアリー寄りだったため落ち着かせる。
  // goldは「重要なアクションにのみ差す光」であり、面や装飾には広げない。
  accent: "#C9A96A",
  accentSoft: "#DCC28A",
  // Premium は同じ世界の「より深く、より静かで、わずかに発光する」層。
  // action.primary と同値にせず (旧実装の値衝突を再発させない)、明度のみ上げる。
  premiumAccent: "#E4C88F",

  // ---- Support: soft cedar-green ----
  // 杉と苔の支援色。成功など「静かな肯定」に用い、goldとは責務を分ける。
  cedar: "#8FAE84",
  cedarBorder: "#3E5142",
  cedarSurface: "#222E25",

  // ---- Text: warm mist-ivory -> sage ----
  // 主文字は霧を含んだ暖かい生成り。副次はセージ寄りに寄せ、森の空気に馴染ませる。
  text: "#F3EEE3",
  mutedSoft: "#C6C8B8",
  muted: "#A7AC9B",
  mutedDark: "#7C8375",
  navMuted: "#5F6B5D",

  // ---- Status ----
  // warning は gold と混同されないよう、より橙寄り・高彩度に振る。
  // error は警告色を保ちつつ、森の世界観に合わせ赤土寄りの落ち着いた色味とする。
  warning: "#D99A4E",
  error: "#E0918A",

  // ---- Outside ----
  // 幅広画面で本文カラム(max-width 430)の外側に出る余白色。
  // 旧値は明るいアイボリー(#F4EFE3)で、暗い本文と強く衝突していた。
  // background より一段深くし、本文カラムが木漏れ日で浮かぶ構図にする。
  outside: "#070A08",
} as const;

// ────────────────────────────────────────────────────────────────
// Visual Direction: 和のエディトリアル — 生成りの紙に、深藍の骨格と朱の印。
// 決定記録: docs/design/color-direction-v1.md (2026-11-19)
//
// kamimusubiDark (上) は旧方向の記録として残す。画面が参照するのは
// 下の appColors で、そこを差し替えれば全画面が切り替わる。
//
// 文字色はすべて、最も暗い面 (surfaceSoft #EDE7DA) に対しても
// WCAG AA (4.5) を満たすことを実測で確認している。
// 金茶 (borderAccent) だけは 2.49 で文字に使えないため、線専用とする。
// ────────────────────────────────────────────────────────────────
export const kamimusubiLight = {
  // ---- Foundation: 生成りの紙 ----
  // 明度は outside < surfaceSoft < background < surface < surfaceRaised の単調増加。
  // 暗基調と同じく、奥行きは明度差で作る。明地では影も機能する。
  background: "#F5F1E8",
  surfaceSoft: "#EDE7DA",
  surface: "#FBF8F2",
  surfaceRaised: "#FFFFFF",

  // ---- Border ----
  // 区切りの線は主張させない。borderStrong だけは入力欄など
  // 状態を示す境界に使うため、地に対して 3.27 を確保する (WCAG 1.4.11)。
  borderSoft: "#E4DCCB",
  borderHeader: "#DCD3C0",
  borderMuted: "#D5CBB8",
  border: "#CFC6B5",
  borderStrong: "#8E8472",
  // 金茶。格式の記号として枠にだけ使う。文字には使わない (地に対して 2.49)。
  borderAccent: "#B39665",
  borderAccentDark: "#9A7F4E",

  // ---- Accent: 朱 ----
  // 鳥居と朱印の朱。1画面に1つだけ差す。面には広げない。
  accent: "#B53A2D",
  // 押下は淡くせず濃くする。明地では濃い方が「押された」に見える。
  accentSoft: "#9E3127",
  // Premium は深藍で格を示す。金茶は文字に使えないため採らない。
  premiumAccent: "#172A40",

  // ---- Support: 杉緑 ----
  cedar: "#3F6B4A",
  cedarBorder: "#B8CDBB",
  cedarSurface: "#E8EFE6",

  // ---- Text: 墨 ----
  // mutedDark が最も薄い。沈み面の上で 4.63 と余裕が無いため、
  // これより薄い文字色を足さない。
  text: "#242424",
  mutedSoft: "#5B5750",
  muted: "#635E56",
  mutedDark: "#6B665D",
  navMuted: "#6B665D",

  // ---- Status ----
  // action が朱のため、error は朱暗で受ける (決定: 案A)。
  // 主アクションは「朱の塗り + 白文字」、error は「朱暗の文字 + 淡い面」と
  // 形で分ける。
  warning: "#8A5A12",
  error: "#8E2018",
  errorSurface: "#F7E9E6",

  // ---- Outside ----
  // 幅広画面で本文カラム(max-width 430)の外側に出る余白色。
  // 地より一段沈め、紙のカラムが浮いて見える構図にする。
  outside: "#E6E0D3",
} as const;

export type KamimusubiLightColorKey = keyof typeof kamimusubiLight;

// 画面が参照する実値。配色を切り替えるときはここだけを差し替える。
export const appColors = kamimusubiLight;

export type AppColorKey = keyof typeof colors;
export type KamimusubiDarkColorKey = keyof typeof kamimusubiDark;

// Design Token v1 定義基盤: Mobile Platform Theme (Semantic Color実値)
// 正本: docs/design/design-token.md
// 既存の colors / kamimusubiDark (上記) は変更せず、kamimusubiDark の値を
// 再利用してSemantic Color Token (semanticColorTokens.ts) の実値を割り当てる。
// PlatformColorTheme型により、SEMANTIC_COLOR_KEYSの全キーを満たすことを
// tscレベルで強制する (1つでも欠けるとコンパイルエラーになる)。
import type { PlatformColorTheme } from "./semanticColorTokens";

// Mobile Semantic Color Token契約の正本実値 (キー一覧・型は design/semanticColorTokens.ts)。
// 2026-07時点でこのオブジェクトを参照するのは本ファイル (型契約の充足) のみで、
// 共通Buttonを通じてLogin、Birthday、Premium、AuthPromptなどから消費される。 (design-token.md Migration方針 PR6
// 共通Buttonを通じてLogin、Birthday、Premium、AuthPromptなどから消費される。
export const kamimusubiDarkSemanticTheme: PlatformColorTheme = {
  "background.base": kamimusubiDark.background,
  "background.subtle": kamimusubiDark.surfaceSoft,
  "surface.default": kamimusubiDark.surface,
  // 旧実装は surfaceSoft (surface より暗い) を elevated に割り当てていた。
  // 背景 / カード面 / 浮き面の分離を保つため surfaceRaised を割り当てる。
  "surface.elevated": kamimusubiDark.surfaceRaised,
  "text.primary": kamimusubiDark.text,
  "text.secondary": kamimusubiDark.muted,
  "text.muted": kamimusubiDark.mutedSoft,
  "text.inverse": kamimusubiDark.background,
  "border.default": kamimusubiDark.border,
  // 旧実装の borderHeader は border.default より暗く強弱が逆転していたため、
  // default より明るい borderStrong を割り当てる。
  "border.strong": kamimusubiDark.borderStrong,
  "border.focus": kamimusubiDark.accent,
  // Primary Action は「重要な操作にだけ差す光」としての shrine-gold。
  "action.primary": kamimusubiDark.accent,
  "action.primaryHover": kamimusubiDark.accentSoft,
  "action.primaryText": kamimusubiDark.background,
  "action.disabled": kamimusubiDark.mutedDark,
  // Status: 旧実装は success / warning / premium / action がいずれも gold 系で、
  // 責務が値レベルで衝突していた。本改訂では
  //   action  = gold (shrine-gold)
  //   success = cedar (静かな肯定)
  //   warning = 橙寄りの高彩度 (goldと混同させない)
  //   premium = gold より明度の高い premiumAccent
  // として、色相・明度の双方で分離する。
  "status.success": kamimusubiDark.cedar,
  "status.successText": kamimusubiDark.cedar,
  "status.successSurface": kamimusubiDark.cedarSurface,
  "status.successBorder": kamimusubiDark.cedarBorder,
  "status.warning": kamimusubiDark.warning,
  // 旧実装は login.tsx 由来の直書き値 (#FCA5A5) だった。Primitive へ昇格させる。
  "status.error": kamimusubiDark.error,
  "status.info": kamimusubiDark.muted,
  // Premium は同じ森の「より深く、より静かで、わずかに発光する」層。
  "premium.accent": kamimusubiDark.premiumAccent,
  "premium.surface": kamimusubiDark.surfaceRaised,
  "premium.border": kamimusubiDark.borderAccent,
  // overlay は背景 (#0A0F0C) に合わせた森影。旧値は Navy 由来 (7,16,31)。
  "overlay.default": "rgba(6, 10, 8, 0.82)",
};

// 明基調の Platform Theme。26キーの網羅は PlatformColorTheme 型が tsc で強制する。
// 決定記録: docs/design/color-direction-v1.md
export const kamimusubiLightSemanticTheme: PlatformColorTheme = {
  "background.base": kamimusubiLight.background,
  "background.subtle": kamimusubiLight.surfaceSoft,
  "surface.default": kamimusubiLight.surface,
  "surface.elevated": kamimusubiLight.surfaceRaised,
  "text.primary": kamimusubiLight.text,
  "text.secondary": kamimusubiLight.muted,
  "text.muted": kamimusubiLight.mutedDark,
  "text.inverse": kamimusubiLight.background,
  "border.default": kamimusubiLight.border,
  "border.strong": kamimusubiLight.borderStrong,
  "border.focus": kamimusubiLight.accent,
  "action.primary": kamimusubiLight.accent,
  "action.primaryHover": kamimusubiLight.accentSoft,
  "action.primaryText": kamimusubiLight.background,
  "action.disabled": kamimusubiLight.mutedDark,
  "status.success": kamimusubiLight.cedar,
  "status.successText": kamimusubiLight.cedar,
  "status.successSurface": kamimusubiLight.cedarSurface,
  "status.successBorder": kamimusubiLight.cedarBorder,
  "status.warning": kamimusubiLight.warning,
  "status.error": kamimusubiLight.error,
  "status.info": kamimusubiLight.muted,
  "premium.accent": kamimusubiLight.premiumAccent,
  "premium.surface": kamimusubiLight.surfaceRaised,
  "premium.border": kamimusubiLight.borderAccent,
  "overlay.default": "rgba(36, 36, 36, 0.45)",
};

// UI Component が参照する Semantic Theme。配色の切り替えはここ1行。
export const appSemanticTheme: PlatformColorTheme = kamimusubiLightSemanticTheme;
