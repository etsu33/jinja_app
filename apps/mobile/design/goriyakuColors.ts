// ご利益の色。
//
// 検索一覧と推薦結果では、複数の神社を見比べる。札がすべて同じ灰色だと、
// どの神社が何を持っているかを文字で読むしかない。色が付いていれば形で拾える。
// 色が情報を運ぶので、これは装飾ではない。
//
// 使うのは「探す・見比べる」画面だけ。神社詳細では使わない(1社・札2〜3枚で、
// 探す行為が無いため、色は意味を持たず飾りになる)。
// 相談フローでも使わない(暗地のため。選択中は朝焼けの曙色で示す)。
//
// 色は和の伝統色から採った。文字色は、札の面と画面の地の両方に対して
// WCAG AA (4.5) を満たす値へ調整してある。検証は
// lib/__tests__/goriyakuColors.test.ts。
//
// 一覧に無いご利益(Backend が返す任意のタグ)は既定の見た目へ落とす。
// 色を増やすより、知らないものを静かに出すほうが安全。
import { kamimusubiLight as theme } from "./theme";

export type GoriyakuColor = {
  /** 和の色名。コードを読むときの手がかりとして持つ。 */
  wa: string;
  /** 札の文字色。 */
  text: string;
  /** 札の面。 */
  surface: string;
};

export const GORIYAKU_COLORS: Record<string, GoriyakuColor> = {
  縁結び: { wa: "紅梅", text: "#A83A5B", surface: "#F7E8EC" },
  金運: { wa: "黄土", text: "#7E5E0C", surface: "#F7F0DC" },
  仕事運: { wa: "藍", text: "#2E4056", surface: "#E6EAF1" },
  厄除け: { wa: "鉄紺", text: "#3A3A5C", surface: "#E9E9F0" },
  学業成就: { wa: "若竹", text: "#3F6B4A", surface: "#E6EDE4" },
  健康: { wa: "鶯", text: "#5A6B2E", surface: "#EEF0E2" },
  商売繁盛: { wa: "丹", text: "#9C4A21", surface: "#F8EBE2" },
  開運: { wa: "紫紺", text: "#5A3A75", surface: "#EFE8F4" },
};

/** 一覧に無いご利益の見た目。色を割り当てない。 */
export const GORIYAKU_FALLBACK: GoriyakuColor = {
  wa: "—",
  text: theme.mutedSoft,
  surface: theme.surfaceSoft,
};

export function goriyakuColor(label: string): GoriyakuColor {
  return GORIYAKU_COLORS[label] ?? GORIYAKU_FALLBACK;
}
