import * as React from "react";
import { type ColorValue } from "react-native";
import { Tabs } from "expo-router";
import Ionicons from "@expo/vector-icons/Ionicons";
import { appColors as theme } from "../../design/platformTheme";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";

// タブバーの寸法。height は指定しない。
// 指定すると react-navigation がホームインジケータ分の safe area inset を
// 上書きしてしまい、iPhone でラベルがインジケータ帯に重なるため
// (旧実装は height: 64 固定でこの状態だった)。
const bottomNavigationSizes = {
  labelFontSize: 11,
} as const;

// タブの色(ColorValue)はアイコンの color が受け付けない null / number も型上は含むため、
// アイコンに渡せる値だけに絞る(実際の色は theme の文字列で、見た目は変わらない)。
function toIconColor(color: ColorValue): string | Exclude<ColorValue, string | number | null> | undefined {
  if (color === null || typeof color === "number") return undefined;
  return color;
}

// アイコンは Ionicons に統一する。
// 旧実装は MaterialIcons で、iOSにAndroidのイディオムが出ていた。
// SF Symbols (expo-symbols) はApple純正だが iOS 専用で、Android用に別の
// アイコン定義を持ち続けることになる。タブ4つのためにその二重管理は負わない。
// 差し替えるならこのファイルだけで済む。
//
// 非選択は線画(outline)、選択は塗り。iOSのタブバーの標準的な区別。
const TAB_ICONS = {
  home: "home",
  concierge: "sparkles",
  records: "book",
  mypage: "person",
} as const;

type TabIconKey = keyof typeof TAB_ICONS;

function tabIcon(key: TabIconKey) {
  return function TabBarIcon({
    color,
    size,
    focused,
  }: {
    color: ColorValue;
    size: number;
    focused: boolean;
  }) {
    const name = focused ? TAB_ICONS[key] : (`${TAB_ICONS[key]}-outline` as const);
    return <Ionicons name={name} size={size} color={toIconColor(color)} />;
  };
}

// 下層画面は root の Stack (app/_layout.tsx) が持つ。
// このレイアウトには実際にタブバーへ出す4画面だけを置く
// (旧実装の hiddenTabOptions による「隠しタブ」は廃止した)。
export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        // iOSは全タブを深藍・淡金へ統一。Web/Androidの値はadapterで維持する。
        tabBarActiveTintColor: theme.accent,
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
      <Tabs.Screen name="index" options={{ title: "ホーム", tabBarIcon: tabIcon("home") }} />
      {/* 旧実装では中央だけ 54pt の円形ボタン(他アイコンの2.25倍)を marginTop: -18 で
          浮かせていた。Material の FAB パターンで iOS のタブバーには無い形であり、
          はみ出した上側はタブボタンの当たり判定の外で押せなかった。4つを同じ寸法に揃える。
          「相談」への強調は、ホームの主要CTA「この相談からご縁を見る」が引き受ける。 */}
      <Tabs.Screen name="concierge/index" options={{ title: "相談", tabBarIcon: tabIcon("concierge") }} />
      <Tabs.Screen name="records/index" options={{ title: "記録", tabBarIcon: tabIcon("records") }} />
      <Tabs.Screen name="mypage/index" options={{ title: "マイページ", tabBarIcon: tabIcon("mypage") }} />
    </Tabs>
  );
}
