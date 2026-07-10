import { describe, expect, it, vi } from "vitest";

// journey.ts は ./http 経由で getAuth (RN の AsyncStorage に依存) を読み込むため、
// ペアリングロジック単体のテストではネイティブ依存を避けるために ./http をモックする。
vi.mock("../http", () => ({
  getAuth: vi.fn(),
}));

import { buildJourneyTimeline, type JourneyEvent } from "../journey";

function makeEvent(
  overrides: Partial<JourneyEvent> & Pick<JourneyEvent, "id" | "event_type" | "occurred_at">,
): JourneyEvent {
  return {
    title: "",
    description: "",
    thread_id: null,
    shrine_id: null,
    shrine_name: null,
    metadata: {},
    ...overrides,
  };
}

describe("buildJourneyTimeline", () => {
  it("consultation_created / recommendation_shown はそのまま単独イベントとして残す", () => {
    const consultation = makeEvent({
      id: "c1",
      event_type: "consultation_created",
      occurred_at: "2026-01-01T09:00:00Z",
    });
    const recommendation = makeEvent({
      id: "r1",
      event_type: "recommendation_shown",
      occurred_at: "2026-01-01T09:05:00Z",
    });

    const timeline = buildJourneyTimeline([consultation, recommendation]);

    expect(timeline).toEqual([
      { kind: "event", occurredAt: recommendation.occurred_at, event: recommendation },
      { kind: "event", occurredAt: consultation.occurred_at, event: consultation },
    ]);
  });

  it("同一神社・visit以降7日以内のReflectionをVisitに1件だけ結合する", () => {
    const visit = makeEvent({
      id: "visit:1",
      event_type: "visit_completed",
      occurred_at: "2026-01-01T00:00:00Z",
      shrine_id: 10,
      shrine_name: "乃木神社",
      metadata: { note: "静かだった" },
    });
    const reflection = makeEvent({
      id: "reflection:1",
      event_type: "reflection_created",
      occurred_at: "2026-01-03T00:00:00Z",
      shrine_id: 10,
      description: "少し落ち着いた",
      metadata: { history_theme: "再出発", mood_before: "anxious", mood_after: "calm" },
    });

    const timeline = buildJourneyTimeline([visit, reflection]);

    expect(timeline).toEqual([{ kind: "visit_experience", occurredAt: visit.occurred_at, visit, reflection }]);
  });

  it("Reflectionの発生日時がVisitより前の場合は結合せず単独イベントとして残す", () => {
    const visit = makeEvent({
      id: "visit:1",
      event_type: "visit_completed",
      occurred_at: "2026-01-05T00:00:00Z",
      shrine_id: 10,
    });
    const reflection = makeEvent({
      id: "reflection:1",
      event_type: "reflection_created",
      occurred_at: "2026-01-01T00:00:00Z",
      shrine_id: 10,
    });

    const timeline = buildJourneyTimeline([visit, reflection]);

    expect(timeline).toEqual([
      { kind: "visit_experience", occurredAt: visit.occurred_at, visit, reflection: null },
      { kind: "event", occurredAt: reflection.occurred_at, event: reflection },
    ]);
  });

  it("7日を超えるReflectionは結合せず単独イベントとして残す", () => {
    const visit = makeEvent({
      id: "visit:1",
      event_type: "visit_completed",
      occurred_at: "2026-01-01T00:00:00Z",
      shrine_id: 10,
    });
    const reflection = makeEvent({
      id: "reflection:1",
      event_type: "reflection_created",
      occurred_at: "2026-01-09T00:00:01Z",
      shrine_id: 10,
    });

    const timeline = buildJourneyTimeline([visit, reflection]);

    const visitItem = timeline.find((item) => item.kind === "visit_experience");
    const reflectionAsEvent = timeline.find((item) => item.kind === "event" && item.event.id === "reflection:1");

    expect(visitItem).toMatchObject({ reflection: null });
    expect(reflectionAsEvent).toBeDefined();
  });

  it("shrine_idが異なるReflectionは結合しない", () => {
    const visit = makeEvent({
      id: "visit:1",
      event_type: "visit_completed",
      occurred_at: "2026-01-01T00:00:00Z",
      shrine_id: 10,
    });
    const reflection = makeEvent({
      id: "reflection:1",
      event_type: "reflection_created",
      occurred_at: "2026-01-02T00:00:00Z",
      shrine_id: 99,
    });

    const timeline = buildJourneyTimeline([visit, reflection]);

    const visitItem = timeline.find((item) => item.kind === "visit_experience");
    expect(visitItem).toMatchObject({ reflection: null });
  });

  it("1件のReflectionは最も近いVisitにのみ割り当て、他のVisitへ重複割り当てしない", () => {
    const visitOld = makeEvent({
      id: "visit:old",
      event_type: "visit_completed",
      occurred_at: "2026-01-01T00:00:00Z",
      shrine_id: 10,
    });
    const visitNew = makeEvent({
      id: "visit:new",
      event_type: "visit_completed",
      occurred_at: "2026-01-04T00:00:00Z",
      shrine_id: 10,
    });
    const reflection = makeEvent({
      id: "reflection:1",
      event_type: "reflection_created",
      occurred_at: "2026-01-05T00:00:00Z",
      shrine_id: 10,
    });

    const timeline = buildJourneyTimeline([visitOld, visitNew, reflection]);

    const newVisitItem = timeline.find((item) => item.kind === "visit_experience" && item.visit.id === "visit:new");
    const oldVisitItem = timeline.find((item) => item.kind === "visit_experience" && item.visit.id === "visit:old");

    expect(newVisitItem).toMatchObject({ reflection });
    expect(oldVisitItem).toMatchObject({ reflection: null });
    expect(timeline.some((item) => item.kind === "event" && item.event.id === "reflection:1")).toBe(false);
  });

  it("複数Visitに対応するReflectionが1件のみの場合、片方のVisitは単独イベント相当（reflection: null）のまま残る", () => {
    const visitA = makeEvent({
      id: "visit:a",
      event_type: "visit_completed",
      occurred_at: "2026-02-01T00:00:00Z",
      shrine_id: 10,
    });
    const visitB = makeEvent({
      id: "visit:b",
      event_type: "visit_completed",
      occurred_at: "2026-02-10T00:00:00Z",
      shrine_id: 10,
    });
    const reflectionForB = makeEvent({
      id: "reflection:b",
      event_type: "reflection_created",
      occurred_at: "2026-02-11T00:00:00Z",
      shrine_id: 10,
    });

    const timeline = buildJourneyTimeline([visitA, visitB, reflectionForB]);

    const aItem = timeline.find((item) => item.kind === "visit_experience" && item.visit.id === "visit:a");
    const bItem = timeline.find((item) => item.kind === "visit_experience" && item.visit.id === "visit:b");

    expect(aItem).toMatchObject({ reflection: null });
    expect(bItem).toMatchObject({ reflection: reflectionForB });
  });
});
