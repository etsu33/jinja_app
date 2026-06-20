import { useRef } from "react";
import { Animated, Pressable, ScrollView, Text, View } from "react-native";
import { kamimusubiDark } from "../theme";

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

function RecordCard({ title, description, meta, iconText, routeLabel }: RecordCardProps) {
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
        onPress={() => console.log(`Record route: ${routeLabel}`)}
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

      {recordItems.map((item) => (
        <RecordCard key={item.routeLabel} {...item} />
      ))}
    </ScrollView>
  );
}
