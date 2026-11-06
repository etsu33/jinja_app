import * as React from "react";
import { View, type ColorValue } from "react-native";
import { Tabs } from "expo-router";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { kamimusubiDark as theme } from "../design/theme";
import { spacing } from "../design/spacing";
import { cardSizes } from "../design/cardSizes";
import { initAnalyticsProvider } from "../lib/posthogAnalyticsProvider";

const bottomNavigationSizes = {
  height: 64,
  labelFontSize: 11,
  featuredIconSize: 28,
  featuredIconContainer: 54,
  featuredIconOffsetTop: -18,
} as const;

// タブの色(ColorValue)はアイコンの color が受け付けない null / number も型上は含むため、
// アイコンに渡せる値だけに絞る(実際の色は theme の文字列で、見た目は変わらない)。
function toIconColor(color: ColorValue): string | Exclude<ColorValue, string | number | null> | undefined {
  if (color === null || typeof color === "number") return undefined;
  return color;
}

// タブバーにボタンを出さない画面の options。
// expo-router 58 から `href: null` は `hidden: true` に変換され、その画面を開くと最初のタブ(ホーム)へ
// 移されるようになった。SDK 57 までの `href: null` と同じく「ボタンだけを見えなくする」書き方で、
// 画面そのものは開けるようにする(タブの中にスタックを入れる構成へ移すまでの暫定対応)。
const hiddenTabOptions = {
  tabBarItemStyle: { display: "none" },
  tabBarButton: () => null,
} as const;

export default function Root() {
  // Analytics Provider初期化: アプリ起動中に一度だけ行う(initAnalyticsProvider内部で多重呼び出しをガード)
  React.useEffect(() => {
    initAnalyticsProvider();
  }, []);

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
      <Tabs.Screen
        name="index"
        options={{
          title: "ホーム",
          tabBarIcon: ({ color, size }) => <MaterialIcons name="home" size={size} color={toIconColor(color)} />,
        }}
      />
      <Tabs.Screen
        name="concierge/index"
        options={{
          title: "相談",
          tabBarIcon: () => (
            <View
              style={{
                width: bottomNavigationSizes.featuredIconContainer,
                height: bottomNavigationSizes.featuredIconContainer,
                borderRadius: bottomNavigationSizes.featuredIconContainer / 2,
                backgroundColor: theme.gold,
                alignItems: "center",
                justifyContent: "center",
                marginTop: bottomNavigationSizes.featuredIconOffsetTop,
              }}
            >
              <MaterialIcons
                name="auto-awesome"
                size={bottomNavigationSizes.featuredIconSize}
                color={theme.background}
              />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="records/index"
        options={{
          title: "記録",
          tabBarIcon: ({ color, size }) => <MaterialIcons name="book" size={size} color={toIconColor(color)} />,
        }}
      />
      <Tabs.Screen
        name="mypage/index"
        options={{
          title: "マイページ",
          tabBarIcon: ({ color, size }) => <MaterialIcons name="person" size={size} color={toIconColor(color)} />,
        }}
      />
      <Tabs.Screen name="journey/index" options={hiddenTabOptions} />
      <Tabs.Screen name="premium/index" options={hiddenTabOptions} />
      <Tabs.Screen name="favorites/index" options={hiddenTabOptions} />
      <Tabs.Screen name="goshuin/index" options={hiddenTabOptions} />
      <Tabs.Screen name="goshuin/upload" options={hiddenTabOptions} />
      <Tabs.Screen name="visit-history/index" options={hiddenTabOptions} />
      <Tabs.Screen name="reflection-history/index" options={hiddenTabOptions} />
      <Tabs.Screen name="consultation-history/index" options={hiddenTabOptions} />
      <Tabs.Screen name="consultation-history/[id]" options={hiddenTabOptions} />
      <Tabs.Screen name="recently-viewed/index" options={hiddenTabOptions} />
      <Tabs.Screen name="profile/index" options={hiddenTabOptions} />
      <Tabs.Screen name="search/index" options={hiddenTabOptions} />
      <Tabs.Screen name="shrines/[id]" options={hiddenTabOptions} />
      <Tabs.Screen name="ranking/index" options={hiddenTabOptions} />
      <Tabs.Screen name="login" options={hiddenTabOptions} />
      <Tabs.Screen name="signup" options={hiddenTabOptions} />
    </Tabs>
  );
}
