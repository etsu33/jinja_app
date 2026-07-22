import { track } from "./track";
import { directionEvent, type DirectionEventName, type DirectionEventPayload } from "../../../../../packages/shared/directionAnalytics";
export function trackWebDirection(name: DirectionEventName, payload: Omit<DirectionEventPayload, "platform"> = {}) { const event = directionEvent(name, { platform: "web", ...payload }); track(event.name, event.payload); }
