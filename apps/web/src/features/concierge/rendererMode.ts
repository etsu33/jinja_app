// concierge/rendererMode.ts

// プレゼン用の一時対応: Vercel環境変数の反映に依存せず新レンダラーを有効化する。
// デモ完了後、NEXT_PUBLIC_CONCIERGE_RENDERER 制御へ戻す。
export const CONCIERGE_RENDERER = "new";

export const SHOW_NEW_RENDERER = true;
