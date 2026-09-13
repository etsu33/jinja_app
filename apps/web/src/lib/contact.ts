// apps/web/src/lib/contact.ts
//
// 問い合わせ先の単一の正本。
// Home の連絡導線と Legal Footer の両方がここを参照する。
// アドレスや件名をページ側へ重複ハードコードしないこと。

/** Mother Ship承認済みの問い合わせ先。 */
export const CONTACT_EMAIL = "j33db05@gmail.com";

/** 件名のデコード後の値。 */
export const CONTACT_SUBJECT = "KAMI MUSUBI お問い合わせ";

/**
 * 問い合わせ用の mailto href。
 *
 * クエリ値は UTF-8 の完全な percent-encode とする。日本語を生のまま
 * 置くと、URLの解釈がクライアント任せになり件名が化ける環境が出るため、
 * 手書きせず encodeURIComponent で構築して取りこぼしを防ぐ。
 *
 * 実際に生成される文字列（契約値。テストで固定している）:
 *   mailto:j33db05@gmail.com?subject=KAMI%20MUSUBI%20%E3%81%8A%E5%95%8F%E3%81%84%E5%90%88%E3%82%8F%E3%81%9B
 */
export const CONTACT_MAILTO_HREF = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(
  CONTACT_SUBJECT,
)}`;
