import { track } from "./track";
import { directionEvent, type DirectionEventName, type DirectionEventPayload } from "../../../../../packages/shared/directionAnalytics";
export function trackWebDirection(name: DirectionEventName, payload: Omit<DirectionEventPayload, "platform"> = {}) {
  try {
    const event = directionEvent(name, { platform: "web", ...payload });
    track(event.name, event.payload);
  } catch {
    // Fixed diagnostic only: never include the payload or user-provided values.
    console.warn("direction_analytics_delivery_failed");
  }
}
