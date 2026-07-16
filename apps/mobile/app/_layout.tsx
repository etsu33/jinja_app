import * as React from "react";
import { View } from "react-native";
import { Tabs } from "expo-router";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { kamimusubiDark as theme } from "./theme";
import { spacing } from "./design/spacing";
import { cardSizes } from "./design/cardSizes";
import { initAnalyticsProvider } from "../lib/posthogAnalyticsProvider";

const bottomNavigationSizes = {
  height: 64,
  labelFontSize: 11,
  featuredIconSize: 28,
  featuredIconContainer: 54,
  featuredIconOffsetTop: -18,
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
          tabBarIcon: ({ color, size }) => <MaterialIcons name="home" size={size} color={color} />,
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
          tabBarIcon: ({ color, size }) => <MaterialIcons name="book" size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="mypage/index"
        options={{
          title: "マイページ",
          tabBarIcon: ({ color, size }) => <MaterialIcons name="person" size={size} color={color} />,
        }}
      />
      <Tabs.Screen name="journey/index" options={{ href: null }} />
      <Tabs.Screen name="premium/index" options={{ href: null }} />
      <Tabs.Screen name="favorites/index" options={{ href: null }} />
      <Tabs.Screen name="goshuin/index" options={{ href: null }} />
      <Tabs.Screen name="goshuin/upload" options={{ href: null }} />
      <Tabs.Screen name="visit-history/index" options={{ href: null }} />
      <Tabs.Screen name="reflection-history/index" options={{ href: null }} />
      <Tabs.Screen name="consultation-history/index" options={{ href: null }} />
      <Tabs.Screen name="recently-viewed/index" options={{ href: null }} />
      <Tabs.Screen name="profile/index" options={{ href: null }} />
      <Tabs.Screen name="birthday/index" options={{ href: null }} />
      <Tabs.Screen name="search/index" options={{ href: null }} />
      <Tabs.Screen name="shrines/[id]" options={{ href: null }} />
      <Tabs.Screen name="ranking/index" options={{ href: null }} />
      <Tabs.Screen name="login" options={{ href: null }} />
      <Tabs.Screen name="theme" options={{ href: null }} />
      <Tabs.Screen name="design/cardSizes" options={{ href: null }} />
      <Tabs.Screen name="design/ctaSizes" options={{ href: null }} />
      <Tabs.Screen name="design/radius" options={{ href: null }} />
      <Tabs.Screen name="design/shadow" options={{ href: null }} />
      <Tabs.Screen name="design/spacing" options={{ href: null }} />
    </Tabs>
  );
}
