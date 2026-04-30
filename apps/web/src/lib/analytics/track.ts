type TrackPayload = Record<string, unknown>;

type TrackEventDetail = {
  eventName: string;
  payload: TrackPayload;
  timestamp: string;
};

const DEV_ANALYTICS_STORAGE_KEY = "app:track:dev-events";
const MAX_DEV_ANALYTICS_EVENTS = 100;

function persistDevTrackEvent(detail: TrackEventDetail) {
  if (process.env.NODE_ENV !== "development") return;

  try {
    const current = window.localStorage.getItem(DEV_ANALYTICS_STORAGE_KEY);
    const parsed = current ? JSON.parse(current) : [];
    const events = Array.isArray(parsed) ? parsed : [];
    const nextEvents = [...events, detail].slice(-MAX_DEV_ANALYTICS_EVENTS);

    window.localStorage.setItem(DEV_ANALYTICS_STORAGE_KEY, JSON.stringify(nextEvents));
  } catch {
    // 開発用ログ保存の失敗でアプリ本体を止めない
  }
}

export function track(eventName: string, payload: TrackPayload = {}) {
  if (process.env.NODE_ENV === "test") return;

  if (typeof window === "undefined") return;

  const detail: TrackEventDetail = {
    eventName,
    payload,
    timestamp: new Date().toISOString(),
  };

  if (process.env.NODE_ENV === "development") {
    console.info("[track]", detail);
    persistDevTrackEvent(detail);
  }

  window.dispatchEvent(
    new CustomEvent("app:track", {
      detail,
    }),
  );
}
