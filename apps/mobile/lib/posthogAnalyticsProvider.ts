// PostHog Provider実装
// production かつ EXPO_PUBLIC_POSTHOG_KEY 設定時のみ実際にPostHogへイベントを送信する。
// developmentまたはkey未設定時はConsoleAnalyticsProvider(analytics.tsの既定Provider)のまま動作する。
import AsyncStorage from "@react-native-async-storage/async-storage";
import PostHog, { PostHogPersistedProperty } from "posthog-react-native";

import { setAnalyticsProvider, type AnalyticsPayload, type AnalyticsProvider } from "./analytics";

// Web版(apps/web/src/lib/analytics/providers.ts)と同じPostHogホストを既定値にし、
// Web/Mobileのイベントが同一PostHogプロジェクトへ届くようにする。
const DEFAULT_POSTHOG_HOST = "https://app.posthog.com";

export class PostHogAnalyticsProvider implements AnalyticsProvider {
  private readonly client: PostHog;

  constructor(apiKey: string, host: string | undefined) {
    this.client = new PostHog(apiKey, {
      host: host || DEFAULT_POSTHOG_HOST,
      // expo-file-system等を追加せず、既存依存の@react-native-async-storageで永続化する
      customStorage: AsyncStorage,
      enableSessionReplay: false,
    });
  }

  track(eventName: string, payload: AnalyticsPayload): void {
    this.client.capture(eventName, payload);
  }

  // 退会時に呼ぶ。送信待ちのイベントを送り切ってから、匿名ID・端末IDを作り直す。
  // reset() の引数を省略すると端末IDが残るため、残す項目を明示して渡す。
  // アプリのバージョン記録だけは残す。消すと次回起動時に
  // 「Application Installed」が再送され、インストール数が水増しされるため。
  async resetIdentity(): Promise<void> {
    await this.client.flush();
    this.client.reset([
      PostHogPersistedProperty.InstalledAppVersion,
      PostHogPersistedProperty.InstalledAppBuild,
    ]);
  }
}

let initialized = false;

// アプリ起動中に一度だけ呼び出す想定(app/_layout.tsx参照)。
// 2回目以降の呼び出しは何もしない。
export function initAnalyticsProvider(): void {
  if (initialized) return;
  initialized = true;

  if (__DEV__) return;

  const apiKey = process.env.EXPO_PUBLIC_POSTHOG_KEY;
  if (!apiKey) return;

  try {
    const provider = new PostHogAnalyticsProvider(apiKey, process.env.EXPO_PUBLIC_POSTHOG_HOST);
    setAnalyticsProvider(provider);
  } catch (error) {
    if (__DEV__) {
      console.warn("[initAnalyticsProvider] failed", error);
    }
  }
}
