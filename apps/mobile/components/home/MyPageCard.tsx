import * as React from "react";
import { View, Text, StyleSheet, Pressable } from "react-native";
import { Link, useFocusEffect } from "expo-router";
import { getCounts } from "../../lib/storage";
import { spacing } from "../../app/design/spacing";
import { cardSizes } from "../../app/design/cardSizes";
import { ctaSizes } from "../../app/design/ctaSizes";

export default function MyPageCard() {
  const [counts, setCounts] = React.useState({ favorites: 0, visits: 0, stamps: 0 });

  useFocusEffect(
    React.useCallback(() => {
      let alive = true;
      (async () => {
        const c = await getCounts();
        if (alive) setCounts(c);
      })();
      return () => { alive = false; };
    }, [])
  );

  return (
    <View style={styles.card}>
      <Text style={styles.title}>マイページ</Text>
      <Text style={styles.sub}>
        御朱印の登録・お気に入り管理・参拝履歴
      </Text>

      <View style={styles.metrics}>
        <View style={styles.pill}><Text style={styles.pillText}>♡ {counts.favorites}</Text></View>
        <View style={styles.pill}><Text style={styles.pillText}>参拝 {counts.visits}</Text></View>
        <View style={styles.pill}><Text style={styles.pillText}>御朱印 {counts.stamps}</Text></View>
      </View>

      <View style={styles.actionRow}>
        <Link href="/goshuin/upload" asChild>
          <Pressable style={styles.btnPrimary}><Text style={styles.btnTextDark}>御朱印を登録</Text></Pressable>
        </Link>
        {/* 任意：一覧を見る導線 */}
        <View style={styles.inlineSpacer} />
        <Link href="/goshuin" asChild>
          <Pressable style={styles.btn}><Text style={styles.btnText}>一覧を見る</Text></Pressable>
        </Link>
      </View>

      <View style={styles.verticalSpacer} />

  {/* ★ マイページ（プロフィール）を開く */}
  <Link href="/profile" asChild>
    <Pressable style={styles.btn}><Text style={styles.btnText}>開く</Text></Pressable>
  </Link>
    </View>
  );
}


const styles = StyleSheet.create({
  card: {
    marginHorizontal: spacing.screenX,
    marginTop: spacing.lgGap,
    backgroundColor: "#fff",
    borderWidth: cardSizes.borderWidth,
    borderColor: "#e6e6e6",
    borderRadius: cardSizes.radiusSm,
    padding: cardSizes.cardPaddingSm,
  },
  title: { fontWeight: "700" },
  sub: { color: "#666", marginTop: spacing.tightGap, fontSize: 12 },
  metrics: { flexDirection: "row", marginTop: spacing.lgGap },
  pill: {
    marginRight: spacing.smGap,
    backgroundColor: "#F4F4F5",
    borderRadius: cardSizes.pillRadius,
    paddingHorizontal: ctaSizes.pillPaddingXSm,
    paddingVertical: ctaSizes.pillPaddingYSm,
  },
  pillText:{ fontSize:12 },
  actionRow: { flexDirection: "row", marginTop: spacing.lgGap },
  inlineSpacer: { width: spacing.smGap },
  verticalSpacer: { height: spacing.smGap },
  btn: {
    height: ctaSizes.smallHeight,
    paddingHorizontal: cardSizes.cardPaddingMd,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: ctaSizes.smallRadius,
    backgroundColor: "#F2C94C",
    borderWidth: cardSizes.borderWidth,
    borderColor: "#e6e6e6",
  },
  btnPrimary: {
    height: ctaSizes.smallHeight,
    paddingHorizontal: cardSizes.cardPaddingMd,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: ctaSizes.smallRadius,
    backgroundColor: "#F2C94C",
    borderWidth: cardSizes.borderWidth,
    borderColor: "#e6e6e6",
  },
  btnText: { fontWeight: "700", color: "#111" },
  btnTextDark:{ fontWeight:"700", color:"#111" },
});
