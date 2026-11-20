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
      (ts.isFunctionDeclaration(node) && node.name && !["ResultCard", "ConciergeScreen"].includes(node.name.text)) ||
      (ts.isVariableStatement(node) &&
        node.declarationList.declarations.some(
          (d) => ts.isIdentifier(d.name) && d.name.text.startsWith("ACTION_SUGGESTION_V4_"),
        )),
  )
  .map((node) => node.getText(ast))
  .join("\n");
const code = ts.transpileModule(declarations, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None },
}).outputText;
function mobileFunctions(post: (...args: any[]) => any) {
  const deps = { ...provenance, ...direction, ...facts, ...reasonV4, post };
  return new Function(
    ...Object.keys(deps),
    `${code}\nreturn { fetchConciergeRecommendations, normalizeRecommendations };`,
  )(...Object.values(deps)) as {
    fetchConciergeRecommendations: (input: any) => Promise<any[]>;
    normalizeRecommendations: (input: any[]) => any[];
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
const registered = [31, 12, 24].map((id) => ({
  id,
  shrine_id: id,
  name: `audit-${id}`,
  reason: "fixture reason",
  recommendation_reason_v4: "fixture v4",
  reason_facts: [{ type: "need_tag", label: "career", evidence: ["fixture"], score: 1 }],
}));
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
    const cards = await mobileFunctions(post).fetchConciergeRecommendations({
      consultation: fixture.query,
      conditionFilters: buildConditionFilters(condition),
      profileContext: buildConditionProfileContext({ condition, globalUserProfile: state.globalUserProfile ?? {} }),
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

  it("characterizes mixed place/registered ordering and duplicate removal (unresolved product contract)", () => {
    const recs = [
      { place_id: "audit-place", name: "place", reason: "fixture" },
      registered[0],
      registered[1],
      registered[0],
    ];
    const web = webItems(recs).map((r: any) => String(r.shrineId ?? r.placeId));
    const mobile = mobileFunctions(vi.fn())
      .normalizeRecommendations(recs)
      .map((r) => r.shrineId);
    expect(web).toEqual(["31", "12", "audit-place"]);
    expect(mobile).toEqual(["audit-place", "31", "12", "31"]);
    expect(metrics(web, mobile)).toEqual({ idSet: 1, rank: 0 });
  });

  it("characterizes generic id-only response identity divergence", () => {
    const recs = [{ id: 88, name: "legacy", reason: "fixture" }];
    expect(webItems(recs)).toEqual([]);
    expect(mobileFunctions(vi.fn()).normalizeRecommendations(recs)[0].shrineId).toBe("88");
  });

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
