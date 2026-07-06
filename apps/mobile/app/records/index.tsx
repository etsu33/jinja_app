import { useEffect, useMemo, useRef, useState } from "react";
import { Animated, Pressable, ScrollView, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { kamimusubiDark } from "../theme";

import { getFavoriteShrines, getRecentViewed } from "../../lib/shrineStorage";
import { getCounts } from "../../lib/storage";
import { listShrineReflections, type ShrineReflectionResponse } from "../../lib/reflections";

type RecordCardProps = {
  title: string;
  description: string;
  meta: string;
  iconText: string;
  routeLabel: string;
};

const recordItems: readonly RecordCardProps[] = [
  {
    title: "お気に入り",
    description: "保存した神社を見返す",
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
  {
    title: "参拝履歴",
    description: "訪れた神社を振り返る",
    meta: "行動の記録",
    iconText: "参",
    routeLabel: "visit-history",
  },
  {
    title: "最近見た神社",
    description: "閲覧した神社をもう一度見る",
    meta: "閲覧履歴",
    iconText: "見",
    routeLabel: "recently-viewed",
  },
];

const ROUTE_MAP: Record<string, string> = {
  favorites: "/favorites",
  goshuin: "/goshuin",
  "visit-history": "/visit-history",
  "recently-viewed": "/recently-viewed",
};

function RecordCard({ title, description, meta, iconText, routeLabel }: RecordCardProps) {
  const router = useRouter();
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
        onPress={() => {
          const route = ROUTE_MAP[routeLabel];
          if (route) router.push(route as any);
        }}
        onPressIn={() => animateScale(0.98)}
        onPressOut={() => animateScale(1)}
        style={{
          alignItems: "center",
          backgroundColor: kamimusubiDark.surface,
          borderColor: kamimusubiDark.borderHeader,
          borderRadius: 16,
          borderWidth: 1,
          flexDirection: "row",
          gap: 16,
          minHeight: 104,
          padding: 16,
        }}
      >
        <View
          style={{
            alignItems: "center",
            borderColor: kamimusubiDark.borderGold,
            borderRadius: 14,
            borderWidth: 1,
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
          <Text
            style={{
              color: kamimusubiDark.gold,
              fontSize: 18,
              fontWeight: "700",
            }}
          >
            {title}
          </Text>
          <Text
            style={{
              color: kamimusubiDark.text,
              fontSize: 14,
              marginTop: 5,
            }}
          >
            {description}
          </Text>
          <Text
            style={{
              color: kamimusubiDark.muted,
              fontSize: 12,
              marginTop: 5,
            }}
          >
            {meta}
          </Text>
        </View>

        <Text accessibilityElementsHidden style={{ color: kamimusubiDark.muted, fontSize: 20 }}>
          ›
        </Text>
      </Pressable>
    </Animated.View>
  );
}

export default function RecordsScreen() {
  const [recentCount, setRecentCount] = useState<number | null>(null);
  const [favCount, setFavCount] = useState<number | null>(null);
  const [visitCount, setVisitCount] = useState<number | null>(null);
  const [reflections, setReflections] = useState<ShrineReflectionResponse[]>([]);
  const [reflectionLoading, setReflectionLoading] = useState(true);
  const [reflectionError, setReflectionError] = useState(false);

  useEffect(() => {
    let mounted = true;

    getRecentViewed(3)
      .then((items) => { if (mounted) setRecentCount(items.length); })
      .catch(() => { if (mounted) setRecentCount(0); });

    getFavoriteShrines()
      .then((items) => { if (mounted) setFavCount(items.length); })
      .catch(() => { if (mounted) setFavCount(0); });

    getCounts()
      .then(({ visits }) => { if (mounted) setVisitCount(visits); })
      .catch(() => { if (mounted) setVisitCount(0); });

    listShrineReflections()
      .then((items) => {
        if (mounted) {
          setReflections(items);
          setReflectionError(false);
        }
      })
      .catch(() => {
        if (mounted) {
          setReflections([]);
          setReflectionError(true);
        }
      })
      .finally(() => {
        if (mounted) setReflectionLoading(false);
      });

    return () => { mounted = false; };
  }, []);

  const recordItemsWithRecentMeta = useMemo(
    () =>
      recordItems.map((item) => {
        if (item.routeLabel === "recently-viewed") {
          return {
            ...item,
            meta:
              recentCount === null
                ? "閲覧履歴を確認中"
                : recentCount > 0
                  ? `${recentCount}件の閲覧履歴`
                  : "閲覧履歴はまだありません",
          };
        }
        if (item.routeLabel === "visit-history") {
          return {
            ...item,
            meta:
              visitCount === null || reflectionLoading
                ? "参拝履歴を確認中"
                : reflectionError
                  ? "振り返り履歴を確認できません"
                  : visitCount === 0 && reflections.length === 0
                    ? "参拝記録はまだありません"
                    : `参拝 ${visitCount ?? 0}回 / 振り返り ${reflections.length}件`,
          };
        }
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
    [recentCount, favCount, visitCount, reflectionLoading, reflectionError, reflections.length],
  );

  return (
    <ScrollView
      style={{ backgroundColor: kamimusubiDark.background, flex: 1 }}
      contentContainerStyle={{ gap: 12, padding: 24, paddingBottom: 40 }}
    >
      <View style={{ marginBottom: 12 }}>
        <Text
          style={{
            color: kamimusubiDark.gold,
            fontSize: 26,
            fontWeight: "700",
          }}
        >
          記録
        </Text>
        <Text
          style={{
            color: kamimusubiDark.text,
            fontSize: 15,
            lineHeight: 23,
            marginTop: 10,
          }}
        >
          保存した神社や参拝の記録を、ここから振り返れます。
        </Text>
      </View>

      {recordItemsWithRecentMeta.map((item) => (
        <RecordCard key={item.routeLabel} {...item} />
      ))}

      {recentCount === 0 ? (
        <View
          style={{
            backgroundColor: kamimusubiDark.surfaceSoft,
            borderColor: kamimusubiDark.borderHeader,
            borderRadius: 16,
            borderWidth: 1,
            padding: 16,
          }}
        >
          <Text
            style={{
              color: kamimusubiDark.text,
              fontSize: 14,
              fontWeight: "700",
            }}
          >
            最近見た神社はまだありません
          </Text>
          <Text
            style={{
              color: kamimusubiDark.muted,
              fontSize: 12,
              lineHeight: 18,
              marginTop: 6,
            }}
          >
            神社詳細を見ると、閲覧履歴としてここに反映されます。
          </Text>
        </View>
      ) : null}
    </ScrollView>
  );
}
