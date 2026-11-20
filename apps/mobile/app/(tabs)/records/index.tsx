import { useEffect, useMemo, useRef, useState } from "react";
import { Animated, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Ionicons from "@expo/vector-icons/Ionicons";
import { useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { WaPattern } from "../../../components/common/WaPattern";
import { dawnNight } from "../../../design/theme";
import { spacing } from "../../../design/spacing";
import { cardSizes } from "../../../design/cardSizes";
import { radius } from "../../../design/radius";
import { typography } from "../../../design/typography";

import { getFavoriteShrines } from "../../../lib/shrineStorage";
import { isLoggedIn } from "../../../lib/authTokens";
import { AuthPrompt } from "../../../components/common/AuthPrompt";

const AUTH_REQUIRED_ROUTES = new Set(["journey"]);

type RecordItemConfig = {
  title: string;
  description: string;
  meta: string;
  // 旧実装は円の中に漢字1文字(歩・朱)と記号(♡)を混ぜていた。タブバーと同じ
  // Ionicons へ揃える。
  icon: React.ComponentProps<typeof Ionicons>["name"];
  routeLabel: string;
};

// カード左のアイコン(48ptの枠の中)と、右端の送り記号。
const CARD_ICON_SIZE = 22;
const CHEVRON_SIZE = 20;

type RecordCardProps = RecordItemConfig & {
  onPress: (routeLabel: string) => void;
};

const recordItems: readonly RecordItemConfig[] = [
  {
    title: "ご縁の歩み",
    description: "相談から提案、参拝、振り返りまでを時系列で見返す",
    meta: "時系列の記録",
    icon: "footsteps",
    routeLabel: "journey",
  },
  {
    title: "保存した神社",
    description: "あとで訪れたい神社を見返す",
    meta: "あとで行きたい場所",
    icon: "heart",
    routeLabel: "favorites",
  },
  {
    title: "御朱印",
    description: "登録した御朱印を確認する",
    meta: "参拝の記録",
    icon: "images",
    routeLabel: "goshuin",
  },
];

const ROUTE_MAP: Record<string, string> = {
  journey: "/journey",
  favorites: "/favorites",
  goshuin: "/goshuin",
};

function RecordCard({ title, description, meta, icon, routeLabel, onPress }: RecordCardProps) {
  const scale = useRef(new Animated.Value(1)).current;

  const animateScale = (toValue: number) => {
    Animated.timing(scale, {
      toValue,
      duration: 80,
      useNativeDriver: true,
    }).start();
  };

  return (
    <Animated.View style={{ transform: [{ scale }] }}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`${title}を開く`}
        onPress={() => onPress(routeLabel)}
        onPressIn={() => animateScale(0.98)}
        onPressOut={() => animateScale(1)}
        style={{
          alignItems: "center",
          backgroundColor: dawnNight.surface,
          borderColor: dawnNight.border,
          borderRadius: radius.md,
          borderWidth: cardSizes.borderWidth,
          flexDirection: "row",
          gap: spacing.xlGap,
          minHeight: 104,
          padding: cardSizes.cardPaddingLg,
        }}
      >
        <View
          style={{
            alignItems: "center",
            borderColor: dawnNight.mark,
            borderRadius: radius.sm,
            borderWidth: cardSizes.borderWidth,
            height: 48,
            justifyContent: "center",
            width: 48,
          }}
        >
          <Ionicons name={icon} size={CARD_ICON_SIZE} color={dawnNight.mark} />
        </View>

        <View style={{ flex: 1 }}>
          <Text style={{ ...typography.subheading, color: dawnNight.text }}>{title}</Text>
          <Text style={{ ...typography.body, color: dawnNight.text, opacity: dawnNight.textBody, marginTop: 5 }}>{description}</Text>
          <Text style={{ ...typography.footnote, color: dawnNight.text, opacity: dawnNight.textMuted, marginTop: 5 }}>{meta}</Text>
        </View>

        <Ionicons
          accessibilityElementsHidden
          name="chevron-forward"
          size={CHEVRON_SIZE}
          color={dawnNight.placeholder}
        />
      </Pressable>
    </Animated.View>
  );
}

export default function RecordsScreen() {
  const router = useRouter();
  // タブ画面はネイティブヘッダーを持たないため、Dynamic Island / ステータスバーの
  // 高さを自分で避ける(下層画面はStackのヘッダーが避けている)。
  const insets = useSafeAreaInsets();
  const { height: screenHeight } = useWindowDimensions();
  const [favCount, setFavCount] = useState<number | null>(null);
  const [authPromptVisible, setAuthPromptVisible] = useState(false);

  const handlePress = async (routeLabel: string) => {
    const route = ROUTE_MAP[routeLabel];
    if (!route) return;

    if (AUTH_REQUIRED_ROUTES.has(routeLabel) && !(await isLoggedIn())) {
      setAuthPromptVisible(true);
      return;
    }

    router.push(route as any);
  };

  useEffect(() => {
    let mounted = true;

    getFavoriteShrines()
      .then((items) => { if (mounted) setFavCount(items.length); })
      .catch(() => { if (mounted) setFavCount(0); });

    return () => { mounted = false; };
  }, []);

  const recordItemsWithMeta = useMemo(
    () =>
      recordItems.map((item) => {
        if (item.routeLabel === "favorites") {
          return {
            ...item,
            meta:
              favCount === null
                ? "確認中"
                : favCount > 0
                  ? `${favCount}件保存済み`
                  : "まだ保存されていません",
          };
        }
        return item;
      }),
    [favCount],
  );

  return (
    <>
    <View style={{ backgroundColor: dawnNight.colors[0], flex: 1 }}>
      {/* 地は相談フロー・ホームと同じ藍。タブ4画面で揃える。 */}
      <LinearGradient
        colors={dawnNight.colors}
        locations={dawnNight.locations}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
        style={StyleSheet.absoluteFill}
      />
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <WaPattern height={screenHeight} />
      </View>
      <View style={{ paddingTop: insets.top }} />
      <ScrollView
        contentContainerStyle={{
          gap: spacing.lgGap,
          padding: spacing.screenXWide,
          paddingBottom: spacing.bottomSpace,
        }}
      >
        <View style={{ marginBottom: spacing.lgGap }}>
          <Text style={{ ...typography.display, color: dawnNight.text }}>記録</Text>
          <Text style={{ ...typography.subhead, color: dawnNight.text, opacity: dawnNight.textBody, marginTop: spacing.mdGap }}>
            相談から育ったご縁や、保存した神社、御朱印をここから振り返れます。
          </Text>
        </View>

        {recordItemsWithMeta.map((item) => (
          <RecordCard key={item.routeLabel} {...item} onPress={handlePress} />
        ))}
      </ScrollView>
    </View>

    <AuthPrompt
      visible={authPromptVisible}
      onClose={() => setAuthPromptVisible(false)}
      description="ご縁の歩みを見るには、ログインが必要です。"
    />
    </>
  );
}
