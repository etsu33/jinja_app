import { describe, expect, it } from "vitest";

import { normalizeAccessLevel, normalizeConciergeResponse } from "@/features/concierge/hooks";

describe("normalizeAccessLevel", () => {
  it.each(["anonymous", "free", "premium"] as const)("%sをそのまま返す", (value) => {
    expect(normalizeAccessLevel(value)).toBe(value);
  });

  it.each([undefined, null, "invalid", 1, {}])("不正な値(%s)はnullへ正規化する", (value) => {
    expect(normalizeAccessLevel(value)).toBeNull();
  });
});

describe("normalizeConciergeResponse", () => {
  it("最小限のrawからdefault値を補完したUnifiedConciergeResponseを構築する", () => {
    const result = normalizeConciergeResponse({}, []);

    expect(result).toMatchObject({
      ok: true,
      stop_reason: null,
      reply: null,
      plan: null,
      remaining: null,
      limit: null,
      limitReached: false,
      thread: null,
    });
    expect(result.data).toMatchObject({ recommendations: [] });
  });

  it("limitReached=trueかつstop_reason未指定の場合はpaywallになる", () => {
    const result = normalizeConciergeResponse({ limitReached: true }, []);
    expect(result.stop_reason).toBe("paywall");
    expect(result.limitReached).toBe(true);
  });

  it("stop_reason='design'を優先してそのまま採用する", () => {
    const result = normalizeConciergeResponse({ stop_reason: "design", limitReached: true }, []);
    expect(result.stop_reason).toBe("design");
  });

  it("data.replyまたはdata.rawからreply文字列を拾う", () => {
    expect(normalizeConciergeResponse({ reply: "hello" }, []).reply).toBe("hello");
    expect(normalizeConciergeResponse({ data: { reply: "from data" } }, []).reply).toBe(
      "from data",
    );
    expect(normalizeConciergeResponse({ data: { raw: "from raw" } }, []).reply).toBe("from raw");
    expect(normalizeConciergeResponse({ reply: 123 }, []).reply).toBeNull();
  });

  it("ok===falseのときのみfalseになる", () => {
    expect(normalizeConciergeResponse({ ok: false }, []).ok).toBe(false);
    expect(normalizeConciergeResponse({}, []).ok).toBe(true);
  });

  it("有効なplan文字列のみ採用し、不正な値はnullにする", () => {
    expect(normalizeConciergeResponse({ plan: "premium" }, []).plan).toBe("premium");
    expect(normalizeConciergeResponse({ plan: "invalid" }, []).plan).toBeNull();
  });

  it("remaining/limitは数値のみ採用する", () => {
    const result = normalizeConciergeResponse({ remaining: 3, limit: "10" }, []);
    expect(result.remaining).toBe(3);
    expect(result.limit).toBeNull();
  });

  it("thread.idを数値化できる場合のみthreadを構築する", () => {
    const result = normalizeConciergeResponse({ thread: { id: "42", title: "t" } }, []);
    expect(result.thread).toMatchObject({ id: 42, title: "t" });
  });

  it("thread.idが数値化できない場合はthreadをnullにする", () => {
    const result = normalizeConciergeResponse({ thread: { id: "abc" } }, []);
    expect(result.thread).toBeNull();
  });

  it("dataが配列またはobject以外の場合は空objectとして扱う", () => {
    const result = normalizeConciergeResponse({ data: [1, 2, 3] }, []);
    expect(result.data).toMatchObject({ recommendations: [] });
  });

  it("recommendationsをdata.recommendationsへ差し込む", () => {
    const recs = [{ name: "神社A" }] as any;
    const result = normalizeConciergeResponse({}, recs);
    expect(result.data?.recommendations).toEqual(recs);
  });
});
