// Analytics payloadのプリミティブ型
// 送信先(Console/将来の外部プロバイダ)に渡せる値だけを許容する。
export type AnalyticsPayload = Record<string, string | number | boolean>;

// provider interface
// 実際の送信手段(Console/PostHog等)はこのinterfaceの実装差し替えで切り替える。
export interface AnalyticsProvider {
  track(eventName: string, payload: AnalyticsPayload): void;
}

function isPrimitiveValue(value: unknown): value is string | number | boolean {
  if (typeof value === "string" || typeof value === "boolean") return true;
  if (typeof value === "number") return Number.isFinite(value);
  return false;
}

// serializer
// object/array/null/undefined/NaN等の非プリミティブ値は破棄し、
// プリミティブ型のフィールドだけを残す(送信先の型崩れを防ぐため)。
export function serializeAnalyticsPayload(payload: Record<string, unknown> | null | undefined): AnalyticsPayload {
  const source = payload && typeof payload === "object" ? payload : {};
  const result: AnalyticsPayload = {};

  for (const [key, value] of Object.entries(source)) {
    if (key === "session_id" || key === "sessionId") continue;

    if (isPrimitiveValue(value)) {
      result[key] = value;
    }
  }

  return result;
}

// Console provider
// 既定のprovider。開発時のみ出力し、本番ビルドでは何もしない。
export class ConsoleAnalyticsProvider implements AnalyticsProvider {
  track(eventName: string, payload: AnalyticsPayload): void {
    if (__DEV__) {
      console.info("[analytics]", eventName, payload);
    }
  }
}

const defaultAnalyticsProvider = new ConsoleAnalyticsProvider();
let analyticsProvider: AnalyticsProvider = defaultAnalyticsProvider;

// provider差し替え
// null を渡すと既定のConsoleAnalyticsProviderへ戻す。
export function setAnalyticsProvider(provider: AnalyticsProvider | null): void {
  analyticsProvider = provider ?? defaultAnalyticsProvider;
}

export function getAnalyticsProvider(): AnalyticsProvider {
  return analyticsProvider;
}

// 送信本体。送信失敗はアプリ本体の動作を止めないよう握り潰す。
export function track(eventName: string, payload: Record<string, unknown> = {}): void {
  const trimmedName = eventName.trim();
  if (!trimmedName) return;

  try {
    getAnalyticsProvider().track(trimmedName, serializeAnalyticsPayload(payload));
  } catch (error) {
    if (__DEV__) {
      console.warn("[track] failed", error);
    }
  }
}
