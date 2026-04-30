type TrackPayload = Record<string, unknown>;

export function track(eventName: string, payload: TrackPayload = {}) {
  if (process.env.NODE_ENV === "test") return;

  if (typeof window === "undefined") return;

  window.dispatchEvent(
    new CustomEvent("app:track", {
      detail: {
        eventName,
        payload,
      },
    }),
  );
}
