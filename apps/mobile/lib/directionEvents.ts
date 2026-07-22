import { track } from "./analytics";
import { directionEvent, type DirectionEventName, type DirectionEventPayload } from "../../../packages/shared/directionAnalytics";
export function trackMobileDirection(name: DirectionEventName, payload: Omit<DirectionEventPayload, "platform"> = {}) {
  try {
    const event = directionEvent(name, { platform: "mobile", ...payload });
    track(event.name, event.payload);
  } catch {
    if (typeof __DEV__ !== "undefined" && __DEV__) console.warn("direction_analytics_delivery_failed");
  }
}
