import * as React from "react";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import * as candidateAdapter from "../../../../../../packages/shared/conciergeCandidates";
import { buildRecommendationReasonDisplay } from "../../../../../../packages/shared/recommendationReasonDisplay";
/** Audit characterization only. No native UI, analytics, or network is executed. */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import ts from "typescript";
import { act, fireEvent, render, renderHook, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { buildConciergeRequestPayload } from "../buildConciergeRequestPayload";
import { buildPayloadFromUnified } from "../buildPayloadFromUnified";
import ConciergeSectionsRenderer from "../components/ConciergeSectionsRenderer";
import { normalizeRecommendations as normalizeWeb } from "@/lib/api/concierge/normalize";
import * as provenance from "../../../../../../packages/shared/recommendationAnalyticsProvenance";
import * as direction from "../../../../../../packages/shared/directionReference";
import * as monthDirection from "../../../../../../packages/shared/monthDirection";
import { toOriginPayload, type UserOrigin } from "../../../../../../packages/shared/userOrigin";
import * as facts from "../../../../../mobile/lib/recommendationReasonFacts";
import * as reasonV4 from "../../../../../mobile/lib/recommendationReasonV4";
import {
  buildConditionFilters,
  buildConditionProfileContext,
  type ConditionState,
} from "../../../../../mobile/lib/conditionPayload";

// Native build flag, needed only to type-check the imported Mobile helper.
declare global {
  const __DEV__: boolean;
}

const mocks = vi.hoisted(() => ({ post: vi.fn() }));
vi.mock("@/lib/api/concierge", () => ({ postConciergeChat: mocks.post }));
vi.mock("@/lib/analytics/searchEvents", () => ({ trackRecommendationQuality: vi.fn(), trackSearchEvent: vi.fn() }));
vi.mock("@/lib/analytics/cardEvents", () => ({ trackCardEvent: vi.fn() }));
vi.mock("@/lib/auth/AuthProvider", () => ({ useAuth: () => ({ isLoggedIn: false, loading: false }) }));
vi.mock("../../../../../mobile/lib/http", () => ({ get: vi.fn() }));
import { useConciergeChat } from "../hooks";

const root = resolve(process.cwd(), "../..");
const fixture = JSON.parse(readFileSync(resolve(root, "docs/audit/fixtures/concierge-web-mobile-parity.json"), "utf8"));

// Mobile's request/card functions are private inside the screen. Compile the actual
// AST declarations, rather than copy their implementation or refactor production.
// UI/imports are excluded; every non-UI dependency below is a real pure module.
const source = readFileSync(resolve(root, "apps/mobile/app/(tabs)/concierge/index.tsx"), "utf8");
const ast = ts.createSourceFile("concierge.tsx", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const declarations = ast.statements
  .filter(
    (node) =>
      (ts.isFunctionDeclaration(node) && node.name && node.name.text !== "ConciergeScreen") ||
      (ts.isVariableStatement(node) &&
        node.declarationList.declarations.some(
          (d) => ts.isIdentifier(d.name) && d.name.text.startsWith("ACTION_SUGGESTION_V4_"),
        )),
  )
  .map((node) => node.getText(ast))
  .join("\n");
const code = ts.transpileModule(declarations, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None, jsx: ts.JsxEmit.React },
}).outputText;
function mobileFunctions(post: (...args: any[]) => any) {
  const NativeView = ({ children, accessibilityLabel }: any) =>
    React.createElement("div", { "aria-label": accessibilityLabel }, children);
  const NativeText = ({ children }: any) => React.createElement("span", null, children);
  const NativeButton = ({ title, onPress }: any) => React.createElement("button", { onClick: onPress }, title);
  const deps = {
    ...provenance,
    ...direction,
    ...monthDirection,
    MonthDirectionSummary: () => null,
    MonthDirectionMark: () => null,
    ...facts,
    ...reasonV4,
    ...candidateAdapter,
    post,
    // Mobile は lib/conciergeChatRequest.ts の postConciergeChat で送る（ログイン中は postAuth）。
    // ここではログインしていない経路（post）として扱う。
    postConciergeChat: (body: unknown) => post("/concierge/chat/", body),
    React,
    View: NativeView,
    Text: NativeText,
    Pressable: NativeView,
    Button: NativeButton,
    styles: {},
    buildRecommendationReasonDisplay,
    trackMobileDirection: vi.fn(),
  };
  return new Function(
    ...Object.keys(deps),
    `${code}\nreturn { fetchConciergeRecommendations, normalizeRecommendations, ConciergeResults };`,
  )(...Object.values(deps)) as {
    fetchConciergeRecommendations: (input: any) => Promise<{ cards: any[]; monthDirection: unknown }>;
    normalizeRecommendations: (input: any[]) => any[];
    ConciergeResults: React.ComponentType<any>;
  };
}
const wire = (value: unknown) => JSON.parse(JSON.stringify(value));
function webItems(recs: any[]) {
  const payload = buildPayloadFromUnified(
    { ok: true, data: { recommendations: normalizeWeb(recs) } } as any,
    {} as any,
  );
  return (payload?.sections.find((s) => s.type === "recommendations") as any)?.items ?? [];
}
const metrics = (a: string[], b: string[]) => ({
  idSet: new Set(a.filter((id) => b.includes(id))).size / new Set([...a, ...b]).size,
  rank: a.filter((id, i) => b[i] === id).length / Math.max(a.length, b.length),
});

describe("Web/Mobile parity audit: actual request and display functions", () => {
  it.each(
    fixture.scenarios as Array<{
      name: string;
      state: any;
      web: any;
      mobile: any;
      expected_responses: Record<string, string>;
    }>,
  )("$name: emitted JSON matches the shared backend fixture", async (scenario: any) => {
    const state = scenario.state;
    const baseFilters = {
      goriyaku_tag_ids: state.goriyakuTagIds?.length ? state.goriyakuTagIds : undefined,
      extra_condition: state.webExtra,
      free_text: state.webExtra,
    };
    const webRecs = fixture.responses[scenario.expected_responses.web];
    const mobileRecs = fixture.responses[scenario.expected_responses.mobile];
    mocks.post.mockResolvedValue({ ok: true, data: { recommendations: webRecs } });
    const { result, unmount } = renderHook(() => useConciergeChat(null, { filters: baseFilters }));
    await act(async () => {
      await result.current.send(
        buildConciergeRequestPayload({
          needText: fixture.query,
          baseFilters,
          visitPreferences: state.webVisitPreferences ?? [],
          plannedVisitDate: state.plannedVisitDate ?? "",
          userOrigin: state.origin ?? null,
        }),
      );
    });
    expect(wire(mocks.post.mock.lastCall?.[0])).toEqual(scenario.web);
    unmount();
    const condition: ConditionState = state;
    const post = vi.fn().mockResolvedValue({ data: { recommendations: mobileRecs } });
    const { cards } = await mobileFunctions(post).fetchConciergeRecommendations({
      consultation: fixture.query,
      conditionFilters: buildConditionFilters(condition),
      profileContext: buildConditionProfileContext({ condition }),
      plannedVisitDate: state.plannedVisitDate?.trim() || undefined,
      location: toOriginPayload((state.origin ?? null) as UserOrigin | null),
    });
    expect(post.mock.lastCall?.[0]).toBe("/concierge/chat/");
    expect(wire(post.mock.lastCall?.[1])).toEqual(scenario.mobile);
    const web = webItems(webRecs);
    const expectedIds = webRecs.map((r: any) => String(r.shrine_id));
    expect(web.map((r: any) => String(r.shrineId))).toEqual(expectedIds);
    expect(cards.map((r) => r.shrineId)).toEqual(expectedIds);
    expect(
      metrics(
        web.map((r: any) => String(r.shrineId)),
        cards.map((r) => r.shrineId),
      ),
    ).toEqual({ idSet: 1, rank: 1 });
    expect(web.map((r: any) => r.reasonFacts)).toEqual(cards.map((r) => r.reasonFacts));
    expect(web.map((r: any) => r.recommendationReasonV4)).toEqual(cards.map((r) => r.recommendationReasonV4));
  });

  it("renders the backend order after expanding Web secondary results", () => {
    const recs = fixture.responses["response-1"];
    const payload = buildPayloadFromUnified(
      { ok: true, data: { recommendations: normalizeWeb(recs) } } as any,
      { isOpen: false, goriyakuTags: [], selectedTagIds: [], suggestedTags: [] } as any,
    );
    const { container, unmount } = render(<ConciergeSectionsRenderer payload={payload!} isPremiumActive={true} />);
    // The initial Web surface deliberately exposes only its registered hero.
    expect(screen.queryByText(recs[1].name)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "迷った時だけ、ほかの神社を見る" }));
    const ids = Array.from(container.querySelectorAll<HTMLAnchorElement>("a[href]"))
      .map((link) => link.getAttribute("href")?.match(/^\/shrines\/(\d+)(?:[?#]|$)/)?.[1])
      .filter(Boolean)
      .map(Number);
    expect([...new Set(ids)]).toEqual(recs.map((r: any) => r.shrine_id));
    const names = recs.map((r: any) => screen.getByText(r.name));
    expect(names[0].compareDocumentPosition(names[1]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(names[1].compareDocumentPosition(names[2]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    unmount();
  });

  it.each(
    fixture.presentation_cases as Array<{
      name: string;
      records: any[];
      registered: number[];
      references: string[];
      ranks: number[];
    }>,
  )("$name: Web/Mobile presentation parity", (scenario) => {
    const web = webItems(scenario.records);
    const mobile = mobileFunctions(vi.fn()).normalizeRecommendations(scenario.records);
    expect(web.filter((c: any) => c.kind === "registered").map((c: any) => c.shrineId)).toEqual(scenario.registered);
    expect(mobile.filter((c) => c.kind === "registered").map((c) => Number(c.shrineId))).toEqual(scenario.registered);
    expect(web.filter((c: any) => c.kind === "place").map((c: any) => c.placeId)).toEqual(scenario.references);
    expect(mobile.filter((c) => c.kind === "place").map((c) => c.placeId)).toEqual(scenario.references);
    expect(mobile.filter((c) => c.kind === "registered").map((c) => c.recommendationRank)).toEqual(scenario.ranks);
    expect(
      mobile.filter((c) => c.kind === "place").every((c) => c.shrineId === undefined && c.recommendationRank === null),
    ).toBe(true);
    if (scenario.name === "mixed-and-nonadjacent-duplicates") {
      expect(web.find((c: any) => c.kind === "registered")).toMatchObject({
        description: "first-31",
        recommendationInstanceId: "instance-first",
      });
      expect(mobile.find((c) => c.kind === "registered")).toMatchObject({
        reason: "first-31",
        recommendationInstanceId: "instance-first",
      });
    }
  });

  it.each(["mixed-and-nonadjacent-duplicates", "external-only", "registered-only", "empty"])(
    "%s: Mobile renders separate references and registered-only actions",
    (name) => {
      const scenario = fixture.presentation_cases.find((c: any) => c.name === name);
      const { normalizeRecommendations, ConciergeResults } = mobileFunctions(vi.fn());
      const onDetail = vi.fn(),
        onActionEvent = vi.fn();
      const { container, unmount } = render(
        <ConciergeResults
          results={normalizeRecommendations(scenario.records)}
          onDetail={onDetail}
          onActionEvent={onActionEvent}
        />,
      );
      expect(screen.queryAllByRole("button", { name: "この神社を詳しく見る" })).toHaveLength(
        scenario.registered.length,
      );
      expect(screen.queryByText("参考候補") !== null).toBe(scenario.references.length > 0);
      for (const rank of scenario.ranks) expect(screen.getByText(`ご縁${rank}`)).toBeInTheDocument();
      if (scenario.registered.length) {
        fireEvent.click(screen.getAllByRole("button", { name: "この神社を詳しく見る" })[0]);
        expect(onDetail).toHaveBeenCalledWith(
          expect.objectContaining({ shrineId: String(scenario.registered[0]), kind: "registered" }),
          1,
        );
      } else {
        expect(onDetail).not.toHaveBeenCalled();
        expect(onActionEvent).not.toHaveBeenCalled();
        expect(container.querySelector("a")).toBeNull();
      }
      unmount();
    },
  );

  it.each(["mixed-and-nonadjacent-duplicates", "external-only", "registered-only", "empty"])(
    "%s: Web hero, references, routes and registered impression dedup",
    (name) => {
      vi.mocked(trackSearchEvent).mockClear();
      const scenario = fixture.presentation_cases.find((c: any) => c.name === name);
      const payload = buildPayloadFromUnified(
        { data: { recommendations: normalizeWeb(scenario.records) } } as any,
        { isOpen: false, goriyakuTags: [], selectedTagIds: [], suggestedTags: [] } as any,
      );
      if (!payload) throw new Error("An explicit response, including empty results, needs a safe presentation");
      const { container, rerender, unmount } = render(
        <ConciergeSectionsRenderer payload={payload} isPremiumActive={true} />,
      );
      expect(screen.queryByRole("region", { name: "参考候補" }) !== null).toBe(scenario.references.length > 0);
      if (scenario.registered.length) {
        expect(container.querySelector(`a[href^="/shrines/${scenario.registered[0]}"]`)).not.toBeNull();
      } else expect(container.querySelector('a[href^="/shrines/31"]')).toBeNull();
      if (scenario.references.length) {
        const ref = screen.getByRole("region", { name: "参考候補" });
        expect(ref.querySelector('a[href^="/shrines/resolve?"]')).not.toBeNull();
        expect(ref.querySelector('a[href^="/shrines/31"]')).toBeNull();
      }
      rerender(<ConciergeSectionsRenderer payload={payload} isPremiumActive={true} />);
      const events = vi
        .mocked(trackSearchEvent)
        .mock.calls.filter(([event]) => event === "concierge_result_impression");
      expect(events.map(([, p]) => [p?.shrineId, p?.recommendationRank, p?.recommendationInstanceId])).toEqual(
        scenario.registered.map((id: number, i: number) => [id, i + 1, "instance-first"]),
      );
      unmount();
    },
  );

  it("characterizes legacy explanation fallback differences", () => {
    const rec = { id: 31, shrine_id: 31, name: "fixture", explanation: { summary: "legacy summary" } };
    expect(normalizeWeb([rec])[0].reason).toBe("legacy summary");
    expect(mobileFunctions(vi.fn()).normalizeRecommendations([rec])[0].reason).toBe(
      "相談内容と神社情報をもとに選ばれた神社です。",
    );
  });

  it("preserves shared location omission and intentionally discards accuracy/source metadata", () => {
    for (const origin of [
      null,
      { latitude: NaN, longitude: 139, source: "device", accuracy: "precise" } as UserOrigin,
    ]) {
      expect(toOriginPayload(origin)).toBeUndefined();
    }
    expect(toOriginPayload({ latitude: 35, longitude: 139, source: "prefecture", accuracy: "approximate" })).toEqual({
      lat: 35,
      lng: 139,
    });
  });
});
