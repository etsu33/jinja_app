import type { UserOrigin } from "./userOrigin";

export type OriginSearchStatus = "idle" | "searching" | "empty" | "error";

export function originSelectionAnnouncement(origin: UserOrigin | null): string {
  if (!origin) return "出発地点は設定されていません。";
  const name = origin.displayName?.trim() || "現在地";
  const accuracy = origin.accuracy === "approximate" ? "おおよその位置" : "確定した位置";
  return `現在の出発地点は${name}、${accuracy}です。`;
}

export function originSearchAnnouncement(status: OriginSearchStatus, count = 0): string {
  if (status === "searching") return "出発地点の候補を検索中です。";
  if (status === "empty") return "候補が見つかりません。相談はそのまま続けられます。";
  if (status === "error") return "候補を検索できませんでした。相談はそのまま続けられます。";
  if (count > 0) return `${count}件の候補が見つかりました。候補を選択してください。`;
  return "";
}
