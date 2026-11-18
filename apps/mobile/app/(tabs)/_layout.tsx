import * as React from "react";
import { View, type ColorValue } from "react-native";
import { Tabs } from "expo-router";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { kamimusubiDark as theme } from "../../design/theme";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";

// タブバーの寸法。height は指定しない。
// 指定すると react-navigation がホームインジケータ分の safe area inset を
// 上書きしてしまい、iPhone でラベルがインジケータ帯に重なるため
// (旧実装は height: 64 固定でこの状態だった)。
const bottomNavigationSizes = {
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

// 下層画面は root の Stack (app/_layout.tsx) が持つ。
// このレイアウトには実際にタブバーへ出す4画面だけを置く
// (旧実装の hiddenTabOptions による「隠しタブ」は廃止した)。
export default function TabsLayout() {
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
    </Tabs>
  );
}
