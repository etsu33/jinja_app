// 利用規約・プライバシーポリシーの配信元と、アプリ内からの開き方。
//
// App Store Review Guideline 3.1.2 は、自動更新サブスクリプションを持つアプリに対し、
// 利用規約(EULA)とプライバシーポリシーへの「機能する」リンクをバイナリ内に置くことを
// 求める。本アプリは Premium 画面で自動更新サブスクリプションを販売するため、
// マイページと Premium 画面の両方から到達できるようにする。
//
// URLは Web版(apps/web/src/app/terms, apps/web/src/app/privacy)の配信先。
// 配信ドメインを変える場合はここだけを直す。

const WEB_ORIGIN = "https://jinja-app-web.vercel.app";

export const LEGAL_URLS = {
  terms: `${WEB_ORIGIN}/terms`,
  privacy: `${WEB_ORIGIN}/privacy`,
} as const;

export type LegalDocument = keyof typeof LEGAL_URLS;

export const LEGAL_LABELS: Record<LegalDocument, string> = {
  terms: "利用規約",
  privacy: "プライバシーポリシー",
};

export type OpenUrl = (url: string) => Promise<unknown>;

/**
 * 規約類を外部ブラウザで開く。
 *
 * ブラウザを開けない端末では openURL が reject するため、未処理のまま残さない
 * (app/(tabs)/mypage/index.tsx の openContactMail、app/shrines/[id].tsx と同じ扱い)。
 */
export function openLegalDocument(document: LegalDocument, openUrl: OpenUrl): void {
  void openUrl(LEGAL_URLS[document]).catch(() => {});
}
