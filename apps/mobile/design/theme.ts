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
  // ---- Foundation: 朝の光を受けた紙 ----
  // 地は鳥の子色。起動時のSplash(design/theme.ts の dawn)の下端と同値にして、
  // 朝焼けが明けきった色からそのまま本編へ繋がるようにしている。
  // 明度は outside < surfaceSoft < background < surface の単調増加。
  // 白と地の比は 1.16 で、線や影に頼らずとも紙の上に紙が乗って見える。
  background: "#F5EEDC",
  surfaceSoft: "#EBE2CC",
  surface: "#FFFFFF",
  surfaceRaised: "#FFFFFF",

  // ---- Border ----
  // 区切りの線は主張させない。borderStrong だけは入力欄など状態を示す
  // 境界に使うため、白に対して 3.69 を確保する (WCAG 1.4.11)。
  borderSoft: "#E2D8C0",
  borderHeader: "#DAD0B6",
  borderMuted: "#D5CAB0",
  border: "#CFC2A4",
  borderStrong: "#8E8472",
  // 金茶。格式の記号として枠にだけ使う。文字には使わない。
  borderAccent: "#B39665",
  borderAccentDark: "#9A7F4E",

  // ---- Accent: 深藍 ----
  // 旧 Dark Forest の gold が担っていた「静かな強調」の位置。見出し・
  // アイコン・選択状態・副次ボタンに広く使う。40箇所以上から参照される。
  // ここを朱にすると画面が赤だらけになり、安売りの広告に見える。
  accent: "#172A40",
  accentSoft: "#2E4056",
  premiumAccent: "#172A40",
  // 選択中の面。深藍をごく薄く敷く (ios-ui-spec-v2.md 15節)。
  // 面を塗りつぶさずに「選ばれている」ことを示すための段階。
  selectedSurface: "#E2E7F0",

  // ---- Vermilion: 朱 ----
  // 鳥居と朱印の朱。1画面に1つだけ、主アクションの塗りにのみ使う。
  // 文字色には使わない (地に対して 4.43 で AA に届かない)。
  vermilion: "#B53A2D",
  vermilionDeep: "#9E3127",

  // ---- Support: 杉緑 ----
  cedar: "#3F6B4A",
  cedarBorder: "#B8CDBB",
  cedarSurface: "#E6EDE4",

  // ---- Text: 墨 ----
  // mutedDark が最も薄い。沈み面の上で 4.75 と余裕が無いため、
  // これより薄い文字色を足さない。
  text: "#242424",
  mutedSoft: "#55514A",
  muted: "#5F5A52",
  mutedDark: "#656057",
  navMuted: "#656057",

  // ---- Status ----
  // 主アクションが朱の塗りなので、error は朱暗の文字 + 淡い面で分ける (案A)。
  warning: "#7E520F",
  error: "#8E2018",
  errorSurface: "#F6E7E4",

  // ---- Outside ----
  // 幅広画面で本文カラム(max-width 430)の外側に出る余白色。
  outside: "#E4D9BE",
} as const;

// 和の朝焼け。夜明け前の濃藍から地平の光へ、上から下へ一方向。
// 使ってよいのは「区切りの画面」だけ (Splash / Brand Intro /
// Immersive Photo Moment の Overlay / Completion Transition)。
// 通常画面の地は単色のまま。ios-ui-spec-v2.md 40節の Gradient 禁止は、
// この4つを除いて有効とする。
//
// 白文字を置けるのは上から 44% まで (50% の薄縹では 4.46 で AA を割る)。
// 焼けの帯 (東雲色・曙色) の上に文字を置くなら墨文字にする。
// 曙色・東雲色は文字色・アイコン色には使わない (地に対して 1.81)。
export const dawn = {
  colors: ["#16213C", "#26354F", "#5A7A9E", "#B9D4DC", "#F8B88B", "#F5EEDC"],
  locations: [0, 0.26, 0.5, 0.68, 0.86, 1],
  // 白文字を置ける下限。これより下へ文字を置かない。
  safeTextLimit: 0.44,
} as const;

export type KamimusubiLightColorKey = keyof typeof kamimusubiLight;

// 画面が参照する実値。配色を切り替えるときはここだけを差し替える。
export const appColors = kamimusubiLight;

// 承認済みホームのIndigo & Gold。iOS全画面パレットもこの色を基準にする。
export const homeIndigo = {
  background: "#08162D",
  backgroundSubtle: "#142D50",
  surface: "#1B304A",
  ornament: "#C9A044",
  action: "#D8C39B",
  actionText: "#08162D",
  text: "#F7F5F0",
  secondaryText: "#BFC9D6",
  border: "#8290A3",
} as const;

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
  "border.focus": kamimusubiLight.vermilion,
  "action.primary": kamimusubiLight.vermilion,
  "action.primaryHover": kamimusubiLight.vermilionDeep,
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

// 2026-11-24: ホーム実画面の承認後、iOS全画面へ展開。
// 旧Light/Darkの値とWebのSemantic契約は変更しない。
export const iosIndigoColors: Record<keyof typeof kamimusubiLight, string> = {
  ...kamimusubiLight,
  background: homeIndigo.background,
  surfaceSoft: "#14263F",
  surface: homeIndigo.surface,
  surfaceRaised: "#243F5D",
  outside: homeIndigo.background,
  borderSoft: "#788AA0",
  borderHeader: "#304862",
  borderMuted: "#788AA0",
  border: homeIndigo.border,
  borderStrong: "#9AAAC0",
  borderAccent: homeIndigo.ornament,
  borderAccentDark: "#B69B64",
  accent: homeIndigo.action,
  accentSoft: "#E4D3B2",
  premiumAccent: "#E4D3B2",
  selectedSurface: "#263F5A",
  // 既存画面の主CTA参照を保つ互換キー。iOSでは朱ではなく淡金を割り当てる。
  vermilion: homeIndigo.action,
  vermilionDeep: "#C9B389",
  cedar: "#B3D2BC",
  cedarBorder: "#7FA88B",
  cedarSurface: "#203F37",
  text: homeIndigo.text,
  mutedSoft: homeIndigo.secondaryText,
  muted: homeIndigo.secondaryText,
  mutedDark: "#A8B8CB",
  navMuted: homeIndigo.secondaryText,
  warning: "#EBC784",
  error: "#F0ADA5",
  errorSurface: "#402A38",
};

export const iosIndigoSemanticTheme: PlatformColorTheme = {
  "background.base": iosIndigoColors.background,
  "background.subtle": iosIndigoColors.surfaceSoft,
  "surface.default": iosIndigoColors.surface,
  "surface.elevated": iosIndigoColors.surfaceRaised,
  "text.primary": iosIndigoColors.text,
  "text.secondary": iosIndigoColors.muted,
  "text.muted": iosIndigoColors.mutedDark,
  "text.inverse": homeIndigo.actionText,
  "border.default": iosIndigoColors.border,
  "border.strong": iosIndigoColors.borderStrong,
  "border.focus": iosIndigoColors.accent,
  "action.primary": homeIndigo.action,
  "action.primaryHover": iosIndigoColors.vermilionDeep,
  "action.primaryText": homeIndigo.actionText,
  "action.disabled": iosIndigoColors.mutedDark,
  "status.success": iosIndigoColors.cedar,
  "status.successText": iosIndigoColors.cedar,
  "status.successSurface": iosIndigoColors.cedarSurface,
  "status.successBorder": iosIndigoColors.cedarBorder,
  "status.warning": iosIndigoColors.warning,
  "status.error": iosIndigoColors.error,
  "status.info": iosIndigoColors.muted,
  "premium.accent": iosIndigoColors.premiumAccent,
  "premium.surface": iosIndigoColors.surfaceRaised,
  "premium.border": iosIndigoColors.borderAccent,
  "overlay.default": "rgba(3, 10, 23, 0.76)",
};

const iosIndigoDawn = {
  ...dawn,
  // Native Splashの先頭色は維持し、既存のフェード時間・順序も変えない。
  colors: [dawn.colors[0], homeIndigo.background, "#102441", homeIndigo.backgroundSubtle, "#102441", homeIndigo.background],
} as const;

// React Nativeに依存しない選択関数。iOS以外の戻り値は既存の実体を保つ。
export function selectAppTheme(platform: string) {
  const isIOS = platform === "ios";
  return {
    colors: isIOS ? iosIndigoColors : appColors,
    semantic: isIOS ? iosIndigoSemanticTheme : appSemanticTheme,
    splash: isIOS ? iosIndigoDawn : dawn,
    statusBarStyle: isIOS ? "light" as const : "dark" as const,
    primaryActionText: isIOS ? homeIndigo.actionText : kamimusubiLight.surfaceRaised,
  };
}
