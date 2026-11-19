import * as React from "react";
import { useRouter } from "expo-router";
import { ScrollView, View, Text, TextInput, StyleSheet, Pressable } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { appColors as theme } from "../../design/theme";
import { ctaSizes } from "../../design/ctaSizes";
import Button from "../../components/ui/Button";
import { trackSearchEntryClick } from "../../lib/searchAnalytics";
import { typography } from "../../design/typography";

// 画面内コンテンツの上余白。safe area inset の内側に置く。
const CONTENT_TOP_PADDING = 22;

export default function Home() {
  const router = useRouter();
  // タブ画面はネイティブヘッダーを持たないため、Dynamic Island / ステータスバーの
  // 高さを自分で避ける(下層画面はStackのヘッダーが避けている)。
  const insets = useSafeAreaInsets();
  const [consultation, setConsultation] = React.useState("");

  const openSearch = () => {
    trackSearchEntryClick();
    // Searchへ渡してよいのは、Search側の既存フィルター処理(SHRINES.tags)と
    // 意味が一致する固定ラベル(ご利益)のみ。相談文・誕生日・参拝予定日・出発地点・
    // 参拝スタイル・補助条件は渡さない(docs/product/mobile-user-flow.md 8節・10節)。
    // ご利益の選択は相談フロー(STEP 3)へ移した。ここからは条件なしで開く。
    router.push("/search");
  };

  // 相談の入力は Guided Journey へ移した (ios-ui-spec-v2.md 08節)。
  // ここで書いた文章は STEP 1 へ引き継ぐ。
  const openConsultation = () => {
    const text = consultation.trim();
    router.push(text ? `/consultation?q=${encodeURIComponent(text)}` : "/consultation");
  };

  return (
    <View style={[styles.screen, { paddingTop: insets.top }]}>
      <ScrollView contentContainerStyle={styles.content}>
        {/* ブランドヘッダー。ロゴマークはまだ素材が無い。
            絵文字の鳥居は端末のフォント次第で字形が変わり、ブランドの同一性を
            保てないため置かず、文字組だけで見せる。マークが用意できたら
            brandBlock の前に差し込む。 */}
        <View style={styles.header}>
          <View style={styles.brandBlock}>
            <Text style={styles.brandName}>神結び</Text>
            <Text style={styles.brandRuby}>kami musubi</Text>
          </View>
        </View>

        {/* Hero */}
        <View style={styles.hero}>
          <Text style={styles.heroLead}>今の相談を、神社とのご縁につなげる</Text>
          <Text style={styles.heroSub}>
            ここでは相談内容だけを整えます。次の画面で、今の相談から結ばれた神社を確認できます。
          </Text>
        </View>

        {/* 相談入力 (ios-ui-spec-v2.md 30節)。テーマ・参拝スタイル・ご利益・
            条件の選択は相談フロー(08節の STEP 1〜4)へ移した。
            ここで書いた文章は STEP 1 へ引き継ぐ。 */}
        <View style={styles.chatCard}>
          <TextInput
            accessibilityLabel="相談内容"
            placeholder="例: 迷いを整理して、前に進むきっかけがほしい"
            placeholderTextColor={theme.mutedDark}
            style={styles.chatInput}
            value={consultation}
            onChangeText={setConsultation}
            multiline
            textAlignVertical="top"
          />
          <Text style={styles.aiHint}>このあと4つの質問で、相談を整えます。</Text>
        </View>

        {/* 主CTA。19節: 1画面に1つ。 */}
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="相談を続ける"
          onPress={openConsultation}
          style={({ pressed }) => [styles.primaryCta, pressed && styles.primaryCtaPressed]}
        >
          <Text style={styles.primaryCtaText}>相談を続ける</Text>
        </Pressable>

        {/* Search入口(補助CTA) */}
        <Button
          title="神社を探す"
          variant="outline"
          onPress={openSearch}
          accessibilityLabel="神社を探す"
          style={styles.searchEntryCta}
        />

      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.outside,
  },
  content: {
    width: "100%",
    maxWidth: 430,
    alignSelf: "center",
    minHeight: "100%",
    backgroundColor: theme.background,
    paddingHorizontal: 20,
    paddingTop: CONTENT_TOP_PADDING,
    paddingBottom: 48,
  },

  // ヘッダー
  header: {
    height: 60,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottomWidth: 1,
    borderBottomColor: theme.borderHeader,
    marginHorizontal: -20,
    paddingHorizontal: 20,
    marginBottom: 28,
  },
  brandBlock: {
    justifyContent: "center",
  },
  brandName: {
    color: theme.text,
    fontSize: 20,
    fontWeight: "900",
    letterSpacing: 1,
  },
  brandRuby: {
    color: theme.muted,
    fontSize: 12,
    letterSpacing: 4,
    marginTop: 1,
  },

  // Hero
  hero: {
    paddingBottom: 24,
    gap: 10,
  },
  heroLead: {
    ...typography.subheading,
    color: theme.text,
  },
  heroSub: {
    ...typography.subhead,
    color: theme.mutedSoft,
  },

  // 入力カード
  chatCard: {
    minHeight: 154,
    borderRadius: 22,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    marginTop: 24,
    padding: 16,
  },
  chatInput: {
    ...typography.bodyStrong,
    minHeight: 78,
    color: theme.text,
    padding: 0,
  },
  aiHint: {
    ...typography.footnote,
    flex: 1,
    color: theme.mutedDark,
  },



  // 主CTA
  // 画面でただ一つの朱。ここ以外は深藍で受ける。
  primaryCta: {
    height: ctaSizes.primaryHeight,
    borderRadius: ctaSizes.primaryRadius,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.vermilion,
    marginTop: 20,
  },
  primaryCtaPressed: {
    backgroundColor: theme.vermilionDeep,
  },
  primaryCtaText: {
    ...typography.button,
    color: theme.background,
  },
  searchEntryCta: {
    marginTop: 12,
  },

});
