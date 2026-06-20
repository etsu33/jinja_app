import { Tabs } from "expo-router";

export default function Root() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: "#E0B963",
        tabBarInactiveTintColor: "#8F846E",
        tabBarStyle: {
          backgroundColor: "#07101F",
          borderTopColor: "#1E2A3A",
        },
      }}
    >
      <Tabs.Screen name="index" options={{ title: "ホーム" }} />
      <Tabs.Screen name="concierge/index" options={{ title: "相談" }} />
      <Tabs.Screen name="records/index" options={{ title: "記録" }} />
      <Tabs.Screen name="ranking/index" options={{ title: "ランキング" }} />
      <Tabs.Screen name="mypage/index" options={{ title: "マイページ" }} />
      <Tabs.Screen name="shrines/storage" options={{ href: null }} />
    </Tabs>
  );
}
