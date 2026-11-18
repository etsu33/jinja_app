import { useEffect, useMemo, useRef, useState } from "react";
import { Animated, Pressable, ScrollView, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { kamimusubiDark } from "../../../design/theme";
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
  iconText: string;
  routeLabel: string;
};

type RecordCardProps = RecordItemConfig & {
  onPress: (routeLabel: string) => void;
};

const recordItems: readonly RecordItemConfig[] = [
  {
    title: "ご縁の歩み",
    description: "相談から提案、参拝、振り返りまでを時系列で見返す",
    meta: "時系列の記録",
    iconText: "歩",
    routeLabel: "journey",
  },
  {
    title: "保存した神社",
    description: "あとで訪れたい神社を見返す",
    meta: "あとで行きたい場所",
    iconText: "♡",
    routeLabel: "favorites",
  },
  {
    title: "御朱印",
    description: "登録した御朱印を確認する",
    meta: "参拝の記録",
    iconText: "朱",
    routeLabel: "goshuin",
  },
];

const ROUTE_MAP: Record<string, string> = {
  journey: "/journey",
  favorites: "/favorites",
  goshuin: "/goshuin",
};

function RecordCard({ title, description, meta, iconText, routeLabel, onPress }: RecordCardProps) {
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
          backgroundColor: kamimusubiDark.surface,
          borderColor: kamimusubiDark.borderHeader,
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
            borderColor: kamimusubiDark.borderGold,
            borderRadius: radius.sm,
            borderWidth: cardSizes.borderWidth,
            height: 48,
            justifyContent: "center",
            width: 48,
          }}
        >
          <Text
            style={{
              color: kamimusubiDark.gold,
              fontSize: 22,
              fontWeight: "700",
            }}
          >
            {iconText}
          </Text>
        </View>

        <View style={{ flex: 1 }}>
          <Text style={{ ...typography.subheading, color: kamimusubiDark.gold }}>{title}</Text>
          <Text style={{ ...typography.body, color: kamimusubiDark.text, marginTop: 5 }}>{description}</Text>
          <Text style={{ ...typography.footnote, color: kamimusubiDark.muted, marginTop: 5 }}>{meta}</Text>
        </View>

        <Text accessibilityElementsHidden style={{ color: kamimusubiDark.muted, fontSize: 20 }}>
          ›
        </Text>
      </Pressable>
    </Animated.View>
  );
}

export default function RecordsScreen() {
  const router = useRouter();
  // タブ画面はネイティブヘッダーを持たないため、Dynamic Island / ステータスバーの
  // 高さを自分で避ける(下層画面はStackのヘッダーが避けている)。
  const insets = useSafeAreaInsets();
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
    <ScrollView
      style={{ backgroundColor: kamimusubiDark.background, flex: 1 }}
      contentContainerStyle={{
        gap: spacing.lgGap,
        paddingHorizontal: spacing.screenXWide,
        paddingTop: insets.top + spacing.screenXWide,
        paddingBottom: spacing.bottomSpace,
      }}
    >
      <View style={{ marginBottom: spacing.lgGap }}>
        <Text style={{ ...typography.display, color: kamimusubiDark.gold }}>記録</Text>
        <Text style={{ ...typography.subhead, color: kamimusubiDark.text, marginTop: spacing.mdGap }}>
          相談から育ったご縁や、保存した神社、御朱印をここから振り返れます。
        </Text>
      </View>

      {recordItemsWithMeta.map((item) => (
        <RecordCard key={item.routeLabel} {...item} onPress={handlePress} />
      ))}
    </ScrollView>

    <AuthPrompt
      visible={authPromptVisible}
      onClose={() => setAuthPromptVisible(false)}
      description="ご縁の歩みを見るには、ログインが必要です。"
    />
    </>
  );
}
