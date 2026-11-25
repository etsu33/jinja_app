// apps/web/src/lib/shrine/__tests__/buildShrineDetailMetadata.test.ts
import { describe, expect, it } from "vitest";

import type { ShrineHistory } from "@/lib/api/types";

import {
  SHRINE_DETAIL_GENERIC_METADATA,
  buildShrineDetailMetadata,
} from "../buildShrineDetailMetadata";

function makeHistory(overrides: Partial<ShrineHistory> = {}): ShrineHistory {
  return {
    id: 1,
    history_type: "official_origin",
    title: "由緒",
    content: "内容",
    period_text: "",
    event_date: null,
    sort_order: 0,
    verification_status: "source_confirmed",
    confidence: "high",
    sources: [],
    ...overrides,
  };
}

describe("buildShrineDetailMetadata", () => {
  describe("title", () => {
    it("Shrine取得成功時のtitleは {name_jp} | KAMI MUSUBI になる", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区愛宕1-5-3",
        histories: [],
      });

      expect(metadata.title).toBe("愛宕神社 | KAMI MUSUBI");
    });

    it("titleにaddress・goriyaku等の付加情報を含めない", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区愛宕1-5-3",
        histories: [makeHistory({ content: "出世の石段で知られる。" })],
      });

      expect(metadata.title).toBe("愛宕神社 | KAMI MUSUBI");
      expect(metadata.title).not.toContain("東京都");
    });
  });

  describe("History Fact selection", () => {
    it("official_origin のfull Factをdescriptionへ採用する", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区",
        histories: [
          makeHistory({ id: 1, history_type: "founding", content: "創始の内容", sort_order: 0 }),
          makeHistory({ id: 2, history_type: "official_origin", content: "由緒の内容", sort_order: 1 }),
        ],
      });

      expect(metadata.description).toBe("由緒の内容");
    });

    it("official_originが無くfoundingがあればfoundingを採用する", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区",
        histories: [
          makeHistory({ id: 1, history_type: "editorial_summary", content: "要約の内容", sort_order: 0 }),
          makeHistory({ id: 2, history_type: "founding", content: "創始の内容", sort_order: 1 }),
        ],
      });

      expect(metadata.description).toBe("創始の内容");
    });

    it("official_origin/foundingが無ければeditorial_summaryを採用する", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区",
        histories: [
          makeHistory({ id: 1, history_type: "historical_event", content: "歴史の内容", sort_order: 0 }),
          makeHistory({ id: 2, history_type: "editorial_summary", content: "要約の内容", sort_order: 1 }),
        ],
      });

      expect(metadata.description).toBe("要約の内容");
    });

    it("上位3typeが無ければhistorical_eventを採用する", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区",
        histories: [makeHistory({ id: 1, history_type: "historical_event", content: "歴史の内容" })],
      });

      expect(metadata.description).toBe("歴史の内容");
    });

    it("改行・連続空白は正規化するが本文の意味は変更しない", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区",
        histories: [makeHistory({ content: "  由緒の内容\n\n  続きの内容  " })],
      });

      expect(metadata.description).toBe("由緒の内容 続きの内容");
    });

    it("trim後に空になるcontentは候補から除外する", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区",
        histories: [
          makeHistory({ id: 1, history_type: "official_origin", content: "   \n  ", sort_order: 0 }),
          makeHistory({ id: 2, history_type: "founding", content: "創始の内容", sort_order: 1 }),
        ],
      });

      expect(metadata.description).toBe("創始の内容");
    });
  });

  describe("Evidence contract", () => {
    it("disputedなHistoryはdescriptionに使用しない", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区愛宕1-5-3",
        histories: [
          makeHistory({
            id: 1,
            history_type: "official_origin",
            content: "諸説ある由緒",
            verification_status: "disputed",
          }),
        ],
      });

      expect(metadata.description).toBe(
        "愛宕神社は東京都港区愛宕1-5-3にある神社です。KAMI MUSUBIで神社の基本情報を確認できます。",
      );
    });

    it("traditionはmetadata v1で使用しない", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区愛宕1-5-3",
        histories: [makeHistory({ id: 1, history_type: "tradition", content: "伝承の内容" })],
      });

      expect(metadata.description).not.toContain("伝承の内容");
      expect(metadata.description).toBe(
        "愛宕神社は東京都港区愛宕1-5-3にある神社です。KAMI MUSUBIで神社の基本情報を確認できます。",
      );
    });

    it("regional_contextはmetadata v1で使用しない", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区愛宕1-5-3",
        histories: [makeHistory({ id: 1, history_type: "regional_context", content: "地域史の内容" })],
      });

      expect(metadata.description).not.toContain("地域史の内容");
      expect(metadata.description).toBe(
        "愛宕神社は東京都港区愛宕1-5-3にある神社です。KAMI MUSUBIで神社の基本情報を確認できます。",
      );
    });

    it("同一history_typeが複数ある場合は既存のsort_order順で先頭を使う", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区",
        histories: [
          makeHistory({ id: 1, history_type: "official_origin", content: "後の由緒", sort_order: 2 }),
          makeHistory({ id: 2, history_type: "official_origin", content: "先の由緒", sort_order: 1 }),
        ],
      });

      expect(metadata.description).toBe("先の由緒");
    });

    it("disputedが先頭でも後続のfull Factを使う", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区",
        histories: [
          makeHistory({
            id: 1,
            history_type: "official_origin",
            content: "諸説ある由緒",
            sort_order: 1,
            verification_status: "disputed",
          }),
          makeHistory({ id: 2, history_type: "official_origin", content: "確定した由緒", sort_order: 2 }),
        ],
      });

      expect(metadata.description).toBe("確定した由緒");
    });
  });

  describe("generic fallback", () => {
    it("usable Historyなし + addressありでaddress入りのgeneric descriptionを返す", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区愛宕1-5-3",
        histories: [],
      });

      expect(metadata).toEqual({
        title: "愛宕神社 | KAMI MUSUBI",
        description:
          "愛宕神社は東京都港区愛宕1-5-3にある神社です。KAMI MUSUBIで神社の基本情報を確認できます。",
      });
    });

    it("usable Historyなし + address空でaddressなしのgeneric descriptionを返す", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "   ",
        histories: [],
      });

      expect(metadata).toEqual({
        title: "愛宕神社 | KAMI MUSUBI",
        description: "愛宕神社の神社情報です。KAMI MUSUBIで神社の基本情報を確認できます。",
      });
    });

    it("Legacy field（description / sajin）やgoriyakuへfallbackしない", () => {
      const metadata = buildShrineDetailMetadata({
        name_jp: "愛宕神社",
        address: "東京都港区愛宕1-5-3",
        histories: [],
        // Legacy/Recommendation系fieldはmetadataのFact sourceにしない
        ...({ description: "レガシー説明", sajin: "レガシー祭神", goriyaku: "商売繁盛" } as Record<string, unknown>),
      });

      expect(metadata.description).not.toContain("レガシー説明");
      expect(metadata.description).not.toContain("レガシー祭神");
      expect(metadata.description).not.toContain("商売繁盛");
    });

    it("name_jpが空の場合はfail-safeなgeneric metadataを返す", () => {
      expect(buildShrineDetailMetadata({ name_jp: "  ", address: "東京都港区" })).toEqual(
        SHRINE_DETAIL_GENERIC_METADATA,
      );
    });
  });
});
