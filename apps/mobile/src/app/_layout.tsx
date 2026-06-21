

import { View } from "react-native";
import { Tabs } from "expo-router";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";

const ACTIVE_COLOR = "#E0B963";
const INACTIVE_COLOR = "#8F846E";
const BACKGROUND_COLOR = "#07101F";
const BORDER_COLOR = "#1E2A3A";

export default function Root() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: ACTIVE_COLOR,
        tabBarInactiveTintColor: INACTIVE_COLOR,
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: "600",
        },
        tabBarStyle: {
          backgroundColor: BACKGROUND_COLOR,
          borderTopColor: BORDER_COLOR,
          borderTopWidth: 1,
          height: 64,
          paddingBottom: 8,
          paddingTop: 6,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "ホーム",
          tabBarIcon: ({ color, size }) => (
            <MaterialIcons name="home" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="goshuin/index"
        options={{
          title: "記録",
          tabBarIcon: ({ color, size }) => (
            <MaterialIcons name="book" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="concierge/index"
        options={{
          title: "相談",
          tabBarIcon: () => (
            <View
              style={{
                width: 54,
                height: 54,
                borderRadius: 27,
                backgroundColor: ACTIVE_COLOR,
                alignItems: "center",
                justifyContent: "center",
                marginTop: -18,
              }}
            >
              <MaterialIcons name="auto-awesome" size={28} color={BACKGROUND_COLOR} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="search/index"
        options={{
          title: "探す",
          tabBarIcon: ({ color, size }) => (
            <MaterialIcons name="search" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile/index"
        options={{
          title: "マイページ",
          tabBarIcon: ({ color, size }) => (
            <MaterialIcons name="person" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen name="favorites/page" options={{ href: null }} />
      <Tabs.Screen name="goshuin/upload" options={{ href: null }} />
      <Tabs.Screen name="shrines/[id]" options={{ href: null }} />
    </Tabs>
  );
}
