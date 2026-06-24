import * as React from "react";
import { View, Text, StyleSheet, Pressable } from "react-native";
import { Link, useFocusEffect } from "expo-router";
import { getCounts } from "../../lib/storage";
import { spacing } from "../../app/design/spacing";
import { cardSizes } from "../../app/design/cardSizes";
import { radius } from "../../app/design/radius";
import { ctaSizes } from "../../app/design/ctaSizes";
import { colors } from "../../app/theme";

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
    backgroundColor: colors.surfaceLight,
    borderWidth: cardSizes.borderWidth,
    borderColor: colors.border,
    borderRadius: radius.xs,
    padding: cardSizes.cardPaddingSm,
  },
  title: { fontWeight: "700" },
  sub: { color: colors.textGray, marginTop: spacing.tightGap, fontSize: 12 },
  metrics: { flexDirection: "row", marginTop: spacing.lgGap },
  pill: {
    marginRight: spacing.smGap,
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.pill,
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
    backgroundColor: colors.accent,
    borderWidth: cardSizes.borderWidth,
    borderColor: colors.border,
  },
  btnPrimary: {
    height: ctaSizes.smallHeight,
    paddingHorizontal: cardSizes.cardPaddingMd,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: ctaSizes.smallRadius,
    backgroundColor: colors.accent,
    borderWidth: cardSizes.borderWidth,
    borderColor: colors.border,
  },
  btnText: { fontWeight: "700", color: colors.textDark },
  btnTextDark: { fontWeight: "700", color: colors.textDark },
});
