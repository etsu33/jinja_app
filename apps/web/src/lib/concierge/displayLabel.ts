/**
 * 画面に出してよい表示名だけを返す。
 *
 * Backend の label_ja は、Backend の対応表に無い内部名だと英語のまま返る
 * (例: "quiet"、"goriyaku_tag:501")。英字・数字・記号(_ : -)だけでできた値は
 * 日本語名が無いものとして扱い、null を返す。呼び出し側は名前を入れない文に切り替える。
 * 「IT守護」のように日本語を含む値はそのまま使う。
 */
const INTERNAL_NAME_PATTERN = /^[A-Za-z0-9_:-]+$/;

export function isInternalName(value: string): boolean {
  return INTERNAL_NAME_PATTERN.test(value);
}

/** 最初に見つかった空でない文字列を表示名として返す。内部名なら null。 */
export function toDisplayLabel(...candidates: unknown[]): string | null {
  for (const candidate of candidates) {
    if (typeof candidate !== "string") continue;
    const trimmed = candidate.trim();
    if (!trimmed) continue;
    return isInternalName(trimmed) ? null : trimmed;
  }
  return null;
}
