// Design Token v1 定義基盤 (Mobile Semantic Color契約)
//
// 正本: docs/design/design-token.md
// 監査根拠: docs/audit/design-token-phase6-audit.md
//
// このファイルはSemantic Color Tokenのキー一覧・型のみを定義する。
// 実値(Platform Theme)は app/theme.ts の kamimusubiDarkSemanticTheme で定義する。
//
// キー名はWeb側 (apps/web/src/styles/tokens.css の --kt-color-* と
// apps/web/src/styles/__tests__/tokens.test.ts) と意味上対応させる。
// dot区切り (例: "background.base") はこのファイルのみの命名形式であり、
// Web側のCSS変数命名 (例: --kt-color-background-base) とは
// 「ハイフンで結合すれば同じ意味になる」という規則で対応させる。

export const SEMANTIC_COLOR_KEYS = [
  "background.base",
  "background.subtle",
  "surface.default",
  "surface.elevated",
  "text.primary",
  "text.secondary",
  "text.muted",
  "text.inverse",
  "border.default",
  "border.strong",
  "border.focus",
  "action.primary",
  "action.primaryHover",
  "action.primaryText",
  "action.disabled",
  "status.success",
  "status.warning",
  "status.error",
  "status.info",
  "premium.accent",
  "premium.surface",
  "premium.border",
  "overlay.default",
] as const;

export type SemanticColorKey = (typeof SEMANTIC_COLOR_KEYS)[number];

// Platformごとの実値割り当て。全SemanticColorKeyを持つことをTypeScriptの
// 型システムで強制する (キーが1つでも欠けるとtscエラーになる)。
export type PlatformColorTheme = Record<SemanticColorKey, string>;
