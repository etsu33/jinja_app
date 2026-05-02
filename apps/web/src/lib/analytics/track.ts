type TrackPayload = Record<string, unknown>;

type TrackEventDetail = {
  eventName: string;
  payload: TrackPayload;
  timestamp: string;
};

const DEV_ANALYTICS_STORAGE_KEY = "app:track:dev-events";
const ANALYTICS_SESSION_ID_STORAGE_KEY = "app:track:session-id";
const MAX_DEV_ANALYTICS_EVENTS = 100;

function generateSessionId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  // fallback（古い環境）
  const array = new Uint8Array(16);
  if (typeof crypto !== "undefined" && crypto.getRandomValues) {
    crypto.getRandomValues(array);
    return Array.from(array)
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }

  // 最終fallback（ほぼ来ないが念のため）
  return `session-${Date.now()}`;
}

function getAnalyticsSessionId(): string | null {
  try {
    const current = window.localStorage.getItem(ANALYTICS_SESSION_ID_STORAGE_KEY);
    if (current) return current;

    const next = generateSessionId();
    window.localStorage.setItem(ANALYTICS_SESSION_ID_STORAGE_KEY, next);
    return next;
  } catch {
    return null;
  }
}

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

  const sessionId = getAnalyticsSessionId();
  const payloadWithSession = sessionId ? { ...payload, sessionId } : payload;

  const detail: TrackEventDetail = {
    eventName,
    payload: payloadWithSession,
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
