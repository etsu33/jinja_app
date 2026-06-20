// apps/mobile/components/PopularShrineCard.tsx
import React from "react";
import { Pressable, View, Text, StyleSheet, Image } from "react-native";
import { Link } from "expo-router";
import { MaterialIcons } from "@expo/vector-icons";
import { kamimusubiDark as theme } from "../app/theme";
// import { useFavorite } from "@/hooks/useFavorite"; // 共有フックがあるなら使用

type BaseProps = {
  id: number | string;
  name: string;
  address?: string;
  rating?: number;
  photo_url?: string;
  popularity?: number; // バッジ用（任意）
  onPress?: () => void; // 外から押下処理を差し込みたいとき（通常未使用）
};

type WithFavProps = BaseProps & {
  enableFavorite?: boolean; // true なら★を表示（デフォ false）
};

// ---- 純粋な見た目（お気に入りなし） ----
function BaseCard({
  id,
  name,
  address,
  rating,
  photo_url,
  popularity,
  onPress,
}: BaseProps) {
  const href = `/shrines/${id}`;

  const CardBody = (
    <View style={styles.cardInner}>
      <Image
        source={
          photo_url ? { uri: photo_url } : require("../assets/placeholder.png")
        }
        style={styles.image}
      />
      <View style={styles.content}>
        <View style={styles.row}>
          <Text numberOfLines={1} style={styles.name}>
            {name}
          </Text>
          {typeof popularity === "number" && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{Math.round(popularity)}</Text>
            </View>
          )}
        </View>
        {address ? (
          <Text numberOfLines={1} style={styles.addr}>
            {address}
          </Text>
        ) : null}
        <View style={styles.ratingRow}>
          <MaterialIcons name="star" size={14} color={theme.gold} />
          <Text style={styles.ratingText}>{rating ?? "—"}</Text>
        </View>
      </View>
    </View>
  );

  const PressableCard = (
    <Pressable
      android_ripple={{ radius: 280 }}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
      onPress={onPress}
    >
      {CardBody}
    </Pressable>
  );

  // onPress が無ければ Link で宣言的遷移
  if (!onPress) {
    return (
      <Link href={href} asChild>
        {PressableCard}
      </Link>
    );
  }
  return PressableCard;
}

// ---- お気に入り付きバージョン（ここでだけフックを使う） ----
function CardWithFavorite(props: BaseProps) {
  // ここでだけ useFavorite を呼ぶので Hooks ルールを満たす
  // const shrineId =
  //   typeof props.id === "number" ? props.id : Number(props.id);
  // if (!Number.isFinite(shrineId)) return null; // id 異常時は描画しない
  // const { fav, busy, toggle } = useFavorite({ shrineId, initial: false });

  // ↑ フックがまだ無い/モバイル未対応なら、ダミーで繋いでおく:
  const fav = false;
  const busy = false;
  const toggle = () => {};

  const href = `/shrines/${props.id}`;

  const CardBody = (
    <View style={styles.cardInner}>
      <Image
        source={
          props.photo_url
            ? { uri: props.photo_url }
            : require("../assets/placeholder.png")
        }
        style={styles.image}
      />
      <View style={styles.content}>
        <View style={styles.row}>
          <Text numberOfLines={1} style={styles.name}>
            {props.name}
          </Text>

          {/* 右上に☆ボタン */}
          <Pressable onPress={toggle} disabled={busy} hitSlop={8}>
            <MaterialIcons
              name={fav ? "star" : "star-border"}
              size={20}
              color={fav ? "#f5a623" : "#888"}
            />
          </Pressable>
        </View>

        {props.address ? (
          <Text numberOfLines={1} style={styles.addr}>
            {props.address}
          </Text>
        ) : null}

        <View style={styles.ratingRow}>
          <MaterialIcons name="star" size={14} color={theme.gold} />
          <Text style={styles.ratingText}>{props.rating ?? "—"}</Text>
        </View>
      </View>
    </View>
  );

  const PressableCard = (
    <Pressable
      android_ripple={{ radius: 280 }}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
      onPress={props.onPress}
    >
      {CardBody}
    </Pressable>
  );

  if (!props.onPress) {
    return (
      <Link href={href} asChild>
        {PressableCard}
      </Link>
    );
  }
  return PressableCard;
}

// ---- エクスポート：フラグで切り替え（フックを条件呼出ししない） ----
export default function PopularShrineCard(props: WithFavProps) {
  const { enableFavorite = false, ...base } = props;
  return enableFavorite ? <CardWithFavorite {...base} /> : <BaseCard {...base} />;
}

const styles = StyleSheet.create({
  card: {
    width: 220,
    borderRadius: 16,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    shadowColor: "#000",
    shadowOpacity: 0.3,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 5 },
    elevation: 4,
    overflow: "hidden",
  },
  pressed: { opacity: 0.85 },
  cardInner: { backgroundColor: theme.surface },
  image: { width: "100%", aspectRatio: 16 / 9, resizeMode: "cover" },
  content: { padding: 12, gap: 5 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  name: {
    color: theme.text,
    fontSize: 15,
    fontWeight: "800",
    flexShrink: 1,
    marginRight: 6,
  },
  addr: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "600",
  },
  ratingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    marginTop: 2,
  },
  ratingText: {
    color: theme.goldSoft,
    fontSize: 13,
    fontWeight: "700",
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 9999,
    borderWidth: 1,
    borderColor: theme.borderGold,
    backgroundColor: "transparent",
  },
  badgeText: {
    color: theme.gold,
    fontSize: 11,
    fontWeight: "700",
  },
});
