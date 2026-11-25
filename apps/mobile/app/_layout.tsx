import * as React from "react";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import * as SplashScreen from "expo-splash-screen";
import { DawnSplash } from "../components/common/DawnSplash";
import { appColors as theme, statusBarStyle } from "../design/platformTheme";
import { typography } from "../design/typography";
import { initAnalyticsProvider } from "../lib/posthogAnalyticsProvider";

// 自前の Splash (DawnSplash) が出るまでネイティブのSplashを維持する。
// 白い瞬きを挟まないため。失敗しても起動を止めないよう握りつぶす。
void SplashScreen.preventAutoHideAsync().catch(() => undefined);

// 深いリンク(/premium など)で直接起動したときも、Stack の下に (tabs) を敷く。
// これが無いと戻る先が無くなり、ネイティブの戻るボタンもスワイプバックも出ない。
export const unstable_settings = {
  anchor: "(tabs)",
};

// 下層画面のネイティブヘッダー。旧実装は各画面が「← 戻る」を手書きしており、
// タップ領域が16〜32pt(HIGの44pt未満)、スワイプバックとpush遷移も無かった。
const SCREEN_TITLES: Record<string, string> = {
  "search/index": "神社を探す",
  "shrines/[id]": "神社の詳細",
  "favorites/index": "お気に入り",
  "ranking/index": "人気神社ランキング",
  "journey/index": "ご縁の歩み",
  "premium/index": "Premium",
  "profile/index": "プロフィール",
  "goshuin/index": "参拝の記録",
  "goshuin/upload": "御朱印を登録",
  "visit-history/index": "参拝履歴",
  "consultation-history/index": "相談履歴",
  "consultation-history/[id]": "相談の詳細",
  "recently-viewed/index": "最近見た神社",
  // ログイン・新規登録は画面内に見出しを持つ(中央寄せカード)。
  // ヘッダーは戻るシェブロンだけにして、同じ語の二重表示を避ける。
  login: "",
  signup: "",
};

export default function Root() {
  const [splashDone, setSplashDone] = React.useState(false);
  const finishSplash = React.useCallback(() => setSplashDone(true), []);

  // Analytics Provider初期化: アプリ起動中に一度だけ行う(initAnalyticsProvider内部で多重呼び出しをガード)
  React.useEffect(() => {
    initAnalyticsProvider();
  }, []);

  return (
    <>
      {/* iOSは深藍に明色文字。Web/Androidは既存の配色を維持する。 */}
      <StatusBar style={statusBarStyle} />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: theme.background },
          headerTintColor: theme.accent,
          // headerTitleStyle は lineHeight / letterSpacing を受け付けないため、
          // Tokenの実値のうちネイティブヘッダーが解釈する2つだけを渡す。
          headerTitleStyle: {
            color: theme.text,
            fontSize: typography.title.fontSize,
            fontWeight: typography.title.fontWeight,
          },
          headerShadowVisible: false,
          // 戻るボタンに前画面名を出さず、シェブロンだけにする。
          headerBackButtonDisplayMode: "minimal",
          contentStyle: { backgroundColor: theme.background },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        {/* 相談入力は Guided Journey (ios-ui-spec-v2.md 41節)。
            22節に従い画面内に小さな戻るを持つため、ネイティブヘッダーは出さない。
            (tabs) の外にあるので、32節のタブバー非表示も自動的に満たす。 */}
        <Stack.Screen name="consultation/index" options={{ headerShown: false }} />
        {Object.entries(SCREEN_TITLES).map(([name, title]) => (
          <Stack.Screen key={name} name={name} options={{ title }} />
        ))}
      </Stack>
      {/* ios-ui-spec-v2.md 10節 / 和の朝焼け。起動のたびに一度だけ出して消える。 */}
      {splashDone ? null : <DawnSplash onDone={finishSplash} />}
    </>
  );
}
