import * as React from "react";
import { useRouter } from "expo-router";
import { ScrollView, View, Text, TextInput, StyleSheet, Pressable } from "react-native";

export default function Home() {
  const router = useRouter();
  const [consultation, setConsultation] = React.useState("");
  const [selectedTheme, setSelectedTheme] = React.useState<string | null>("心を整える");
  const [showConditions, setShowConditions] = React.useState(false);

  const themes = ["仕事", "恋愛", "人間関係", "金運", "健康", "心を整える", "その他"];

  const openConcierge = () => {
    const params = new URLSearchParams();
    if (consultation.trim()) params.set("q", consultation.trim());
    if (selectedTheme) params.set("theme", selectedTheme);
    const query = params.toString();
    router.push(query ? `/concierge?${query}` : "/concierge");
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <View style={styles.brandRow}>
          <View style={styles.logoMark} />
          <View>
            <Text style={styles.brandName}>神結び</Text>
            <Text style={styles.brandRuby}>kami musubi</Text>
          </View>
        </View>
        <View style={styles.menuIcon}>
          <Text style={styles.menuIconText}>☰</Text>
        </View>
      </View>

      <View style={styles.hero}>
        <Text style={styles.heroLead}>今の悩みや願いから</Text>
        <Text style={styles.heroTitle}>心にあることを、{`\n`}話してみてください</Text>
      </View>

      <View style={styles.chatCard}>
        <TextInput
          placeholder="最近ちょっと疲れていて、これからの方向を整理したくて…"
          placeholderTextColor="#8F846E"
          style={styles.chatInput}
          value={consultation}
          onChangeText={setConsultation}
          multiline
          textAlignVertical="top"
        />
        <View style={styles.chatFooter}>
          <Text style={styles.aiHint}>□ AIがあなたの言葉からご縁を結びます</Text>
          <Pressable onPress={openConcierge} style={styles.sendButton}>
            <Text style={styles.sendButtonText}>↑</Text>
          </Pressable>
        </View>
      </View>

      <View style={styles.themeSection}>
        <Text style={styles.themeLabel}>ことばが浮かばないときは、ここから</Text>
        <View style={styles.themeGrid}>
          {themes.map((theme) => {
            const active = selectedTheme === theme;
            return (
              <Pressable
                key={theme}
                onPress={() => setSelectedTheme(active ? null : theme)}
                style={[styles.themePill, active && styles.themePillActive]}
              >
                <Text style={[styles.themePillText, active && styles.themePillTextActive]}>□ {theme}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      <Pressable onPress={() => setShowConditions((current) => !current)} style={styles.accordionToggle}>
        <Text style={styles.accordionToggleText}>{showConditions ? "− 条件を閉じる" : "+ 条件を追加"}</Text>
      </Pressable>

      {showConditions ? (
        <View style={styles.conditionList}>
          <Text style={styles.conditionItem}>□ 誕生日</Text>
          <Text style={styles.conditionItem}>□ エリア</Text>
          <Text style={styles.conditionItem}>□ ご利益</Text>
          <Text style={styles.conditionItem}>□ 参拝スタイル</Text>
        </View>
      ) : null}

      <Pressable onPress={openConcierge} style={styles.primaryCta}>
        <Text style={styles.primaryCtaText}>□ 神社とのご縁を探す</Text>
      </Pressable>

      <View style={styles.tileGrid}>
        <Pressable onPress={() => router.push("/search")} style={[styles.navTile, styles.navTileActive]}>
          <Text style={styles.tileIcon}>□</Text>
          <Text style={styles.tileTitle}>地図から探す</Text>
          <Text style={styles.tileDescription}>近くの神社を巡る</Text>
        </Pressable>

        <Pressable onPress={() => router.push("/search")} style={styles.navTile}>
          <Text style={styles.tileIcon}>□</Text>
          <Text style={styles.tileTitle}>神社一覧</Text>
          <Text style={styles.tileDescription}>ご利益から見る</Text>
        </Pressable>

        <Pressable onPress={() => router.push("/search")} style={styles.navTile}>
          <Text style={styles.tileIcon}>□</Text>
          <Text style={styles.tileTitle}>よく見られている</Text>
          <Text style={styles.tileDescription}>今戸・神田明神 ほか</Text>
        </Pressable>

        <Pressable onPress={() => router.push("/profile")} style={styles.navTile}>
          <Text style={styles.tileIcon}>□</Text>
          <Text style={styles.tileTitle}>参拝の記録</Text>
          <Text style={styles.tileDescription}>結んだご縁を残す</Text>
        </Pressable>
      </View>

      <View style={styles.bottomNav}>
        <Text style={styles.bottomNavItemActive}>□</Text>
        <Text style={styles.bottomNavItem}>□</Text>
        <Text style={styles.bottomNavItem}>□</Text>
        <Text style={styles.bottomNavItem}>□</Text>
        <Text style={styles.bottomNavItem}>□</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#F4EFE3",
  },
  content: {
    width: "100%",
    maxWidth: 430,
    alignSelf: "center",
    minHeight: "100%",
    backgroundColor: "#07101F",
    paddingHorizontal: 20,
    paddingTop: 22,
    paddingBottom: 0,
  },
  header: {
    height: 60,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottomWidth: 1,
    borderBottomColor: "#1F2A3E",
    marginHorizontal: -20,
    paddingHorizontal: 20,
    marginBottom: 28,
  },
  brandRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  logoMark: {
    width: 22,
    height: 22,
    borderWidth: 2,
    borderColor: "#E0B963",
  },
  brandName: {
    color: "#F7F0E3",
    fontSize: 20,
    fontWeight: "900",
    letterSpacing: 1,
  },
  brandRuby: {
    color: "#A99B80",
    fontSize: 12,
    letterSpacing: 4,
    marginTop: 1,
  },
  menuIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#4B3F2E",
    alignItems: "center",
    justifyContent: "center",
  },
  menuIconText: {
    color: "#E0B963",
    fontSize: 18,
    fontWeight: "900",
  },
  hero: {
    paddingBottom: 24,
  },
  heroLead: {
    color: "#B7AA8E",
    fontSize: 15,
    fontWeight: "700",
    marginBottom: 12,
    letterSpacing: 0.8,
  },
  heroTitle: {
    color: "#F7F0E3",
    fontSize: 31,
    fontWeight: "900",
    lineHeight: 42,
    letterSpacing: 1.2,
  },
  chatCard: {
    minHeight: 154,
    borderRadius: 22,
    backgroundColor: "#101827",
    borderWidth: 1,
    borderColor: "#384154",
    padding: 16,
    shadowColor: "#000",
    shadowOpacity: 0.25,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 10 },
    elevation: 3,
  },
  chatInput: {
    minHeight: 78,
    color: "#F7F0E3",
    fontSize: 16,
    lineHeight: 24,
    padding: 0,
  },
  chatFooter: {
    marginTop: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
  },
  aiHint: {
    flex: 1,
    color: "#8F846E",
    fontSize: 12,
    lineHeight: 18,
  },
  sendButton: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: "#E0B963",
    alignItems: "center",
    justifyContent: "center",
  },
  sendButtonText: {
    color: "#07101F",
    fontSize: 22,
    fontWeight: "900",
  },
  themeSection: {
    marginTop: 24,
  },
  themeLabel: {
    color: "#A99B80",
    fontSize: 13,
    fontWeight: "700",
    marginBottom: 12,
  },
  themeGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  themePill: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
    backgroundColor: "#0B1424",
    borderWidth: 1,
    borderColor: "#374056",
  },
  themePillActive: {
    backgroundColor: "#E0B963",
    borderColor: "#E0B963",
  },
  themePillText: {
    color: "#BDB093",
    fontSize: 13,
    fontWeight: "800",
  },
  themePillTextActive: {
    color: "#07101F",
  },
  accordionToggle: {
    marginTop: 18,
    paddingVertical: 8,
  },
  accordionToggleText: {
    color: "#BDB093",
    fontSize: 14,
    fontWeight: "800",
  },
  conditionList: {
    borderRadius: 18,
    backgroundColor: "#101827",
    borderWidth: 1,
    borderColor: "#384154",
    padding: 14,
    gap: 10,
  },
  conditionItem: {
    color: "#F7F0E3",
    fontSize: 14,
    fontWeight: "800",
  },
  primaryCta: {
    height: 56,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#E0B963",
    marginTop: 18,
  },
  primaryCtaText: {
    color: "#07101F",
    fontSize: 16,
    fontWeight: "900",
  },
  tileGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 14,
    marginTop: 18,
    paddingBottom: 24,
  },
  navTile: {
    width: "48%",
    minHeight: 116,
    borderRadius: 18,
    backgroundColor: "#101827",
    borderWidth: 1,
    borderColor: "#2B3448",
    padding: 16,
    justifyContent: "center",
  },
  navTileActive: {
    borderColor: "#8A6C32",
  },
  tileIcon: {
    color: "#D9C177",
    fontSize: 20,
    fontWeight: "900",
    marginBottom: 18,
  },
  tileTitle: {
    color: "#F7F0E3",
    fontSize: 17,
    fontWeight: "900",
    marginBottom: 6,
  },
  tileDescription: {
    color: "#8F846E",
    fontSize: 13,
    fontWeight: "700",
  },
  bottomNav: {
    height: 78,
    marginHorizontal: -20,
    borderTopWidth: 1,
    borderTopColor: "#1F2A3E",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-around",
  },
  bottomNavItemActive: {
    color: "#E0B963",
    fontSize: 22,
    fontWeight: "900",
  },
  bottomNavItem: {
    color: "#7A735F",
    fontSize: 22,
    fontWeight: "900",
  },
});
