import { Tabs } from "expo-router";
import { kamimusubiDark as theme } from "./theme";
import { spacing } from "./design/spacing";
import { cardSizes } from "./design/cardSizes";

const bottomNavigationSizes = {
  height: 64,
  labelFontSize: 11,
} as const;

export default function Root() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: theme.gold,
        tabBarInactiveTintColor: theme.muted,
        tabBarLabelStyle: {
          fontSize: bottomNavigationSizes.labelFontSize,
          fontWeight: "600",
        },
        tabBarStyle: {
          backgroundColor: theme.background,
          borderTopColor: theme.borderHeader,
          borderTopWidth: cardSizes.borderWidth,
          height: bottomNavigationSizes.height,
          paddingBottom: spacing.smGap,
          paddingTop: spacing.inlineGap - 1,
        },
      }}
    >
      <Tabs.Screen name="index" options={{ title: "ホーム" }} />
      <Tabs.Screen name="concierge/index" options={{ title: "相談" }} />
      <Tabs.Screen name="records/index" options={{ title: "記録" }} />
      <Tabs.Screen name="ranking/index" options={{ title: "ランキング" }} />
      <Tabs.Screen name="mypage/index" options={{ title: "マイページ" }} />
      <Tabs.Screen name="favorites/index" options={{ href: null }} />
      <Tabs.Screen name="shrines/storage" options={{ href: null }} />
    </Tabs>
  );
}
