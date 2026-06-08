export type SearchParamsLike = Pick<URLSearchParams, "get">;

export type MutableSearchParamsLike = Pick<URLSearchParams, "get" | "delete">;

/**
 * 投稿完了後の復帰状態かどうかを判定する。
 *
 * 条件:
 * - submitted=1
 * - status=pending
 */
export function isSubmissionPendingParams(params: SearchParamsLike): boolean {
  return params.get("submitted") === "1" && params.get("status") === "pending";
}

/**
 * 投稿完了後の復帰状態を表す query param を削除する。
 *
 * UI では初回表示後の cleanup 用に使う。
 */
export function clearSubmissionPendingParams(params: MutableSearchParamsLike): void {
  params.delete("submitted");
  params.delete("status");
  params.delete("name");
}
