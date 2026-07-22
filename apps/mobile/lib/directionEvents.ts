import { track } from "./analytics";
import { directionEvent, type DirectionEventName, type DirectionEventPayload } from "../../../packages/shared/directionAnalytics";
export function trackMobileDirection(name: DirectionEventName, payload: Omit<DirectionEventPayload, "platform"> = {}) { const event = directionEvent(name, { platform: "mobile", ...payload }); track(event.name, event.payload); }
