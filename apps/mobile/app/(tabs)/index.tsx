import * as React from "react";
import { useFocusEffect, useRouter } from "expo-router";
import { ScrollView, View, Text, TextInput, StyleSheet, Pressable, Image, Platform, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { appColors as theme, homeIndigo } from "../../design/theme";
import { StatusBar } from "expo-status-bar";
import { LinearGradient } from "expo-linear-gradient";
import { ctaSizes } from "../../design/ctaSizes";
import Button from "../../components/ui/Button";
import { trackSearchEntryClick } from "../../lib/searchAnalytics";
import { typography } from "../../design/typography";

// 画面内コンテンツの上余白。safe area inset の内側に置く。
const CONTENT_TOP_PADDING = 22;
const isIndigoHome = Platform.OS === "ios";
const HOME_GRADIENT = [homeIndigo.background, homeIndigo.backgroundSubtle] as const;

// 既存のViewだけで描く独自の雲文様。画像・追加ライブラリ・連続描画は不要。
function HomeCloud() {
  return (
    <View style={indigoStyles.cloud}>
      <View style={indigoStyles.cloudUpper} />
      <View style={indigoStyles.cloudMiddle} />
      <View style={indigoStyles.cloudLower} />
    </View>
  );
}

export default function Home() {
  const router = useRouter();
  // タブ画面はネイティブヘッダーを持たないため、Dynamic Island / ステータスバーの
  // 高さを自分で避ける(下層画面はStackのヘッダーが避けている)。
  const insets = useSafeAreaInsets();
  const { fontScale } = useWindowDimensions();
  const [consultation, setConsultation] = React.useState("");
  const [isHomeFocused, setHomeFocused] = React.useState(false);

  useFocusEffect(React.useCallback(() => {
    if (!isIndigoHome) return;
    setHomeFocused(true);
    return () => setHomeFocused(false);
  }, []));

  const openSearch = () => {
    trackSearchEntryClick();
    // Searchへ渡してよいのは、Search側の既存フィルター処理(SHRINES.tags)と
    // 意味が一致する固定ラベル(ご利益)のみ。相談文・誕生日・参拝予定日・出発地点・
    // 参拝スタイル・補助条件は渡さない(docs/product/mobile-user-flow.md 8節・10節)。
    // ご利益の選択は相談フロー(STEP 3)へ移した。ここからは条件なしで開く。
    router.push("/search");
  };

  // 相談の入力は Guided Journey へ移した (ios-ui-spec-v2.md 08節)。
  // ここの自由入力は STEP 1「今、どんなことを整理したいですか？」そのものなので、
  // 書いてあれば topicDone を付けて STEP 1 を飛ばす。同じ問いを二度出さない。
  // 空のまま進んだ場合は STEP 1 で選ぶ。
  const openConsultation = () => {
    const text = consultation.trim();
    if (!text) {
      router.push("/consultation");
      return;
    }
    router.push(`/consultation?q=${encodeURIComponent(text)}&topicDone=1`);
  };

  return (
    <View style={[styles.screen, isIndigoHome && indigoStyles.screen, { paddingTop: insets.top }]}>
      {isIndigoHome && isHomeFocused ? <StatusBar style="light" /> : null}
      {isIndigoHome ? (
        <View style={StyleSheet.absoluteFill} pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          <LinearGradient colors={HOME_GRADIENT} style={StyleSheet.absoluteFill} />
          <View style={[indigoStyles.cloudTopLeft, { top: insets.top + 2 }]}><HomeCloud /></View>
          <View style={[indigoStyles.cloudTopRight, { top: insets.top + 2 }]}><HomeCloud /></View>
          <View style={indigoStyles.cloudBottomLeft}><HomeCloud /></View>
          <View style={indigoStyles.cloudBottomRight}><HomeCloud /></View>
        </View>
      ) : null}
      <ScrollView contentContainerStyle={[styles.content, isIndigoHome && indigoStyles.content]}>
        {/* 既存ロゴはiOSホームだけで使用する。文字ロゴが名前を伝える。 */}
        <View style={[styles.header, isIndigoHome && indigoStyles.header]}>
          {isIndigoHome ? <Image source={require("../../assets/icon.png")} style={indigoStyles.logo} resizeMode="contain" accessible={false} /> : null}
          <View style={[styles.brandBlock, isIndigoHome && indigoStyles.brandBlock]}>
            <Text style={[styles.brandName, isIndigoHome && indigoStyles.brandName]}>神結び</Text>
            <Text style={[styles.brandRuby, isIndigoHome && indigoStyles.brandRuby]}>kami musubi</Text>
          </View>
        </View>

        {/* Hero */}
        <View style={styles.hero}>
          <Text style={[styles.heroLead, isIndigoHome && indigoStyles.heroLead]}>今の相談を、神社とのご縁につなげる</Text>
          <Text style={[styles.heroSub, isIndigoHome && indigoStyles.heroSub]}>
            ここでは相談内容だけを整えます。次の画面で、今の相談から結ばれた神社を確認できます。
          </Text>
        </View>

        {/* 相談入力 (ios-ui-spec-v2.md 30節)。テーマ・参拝スタイル・ご利益・
            条件の選択は相談フロー(08節の STEP 1〜4)へ移した。
            ここで書いた文章は STEP 1 へ引き継ぐ。 */}
        <View style={[styles.chatCard, isIndigoHome && indigoStyles.chatCard]}>
          <TextInput
            accessibilityLabel="相談内容"
            placeholder="例: 迷いを整理して、前に進むきっかけがほしい"
            placeholderTextColor={isIndigoHome ? homeIndigo.secondaryText : theme.mutedDark}
            selectionColor={isIndigoHome ? homeIndigo.action : undefined}
            keyboardAppearance={isIndigoHome ? "dark" : undefined}
            style={[styles.chatInput, isIndigoHome && indigoStyles.chatInput, isIndigoHome && { minHeight: 78 * fontScale }]}
            value={consultation}
            onChangeText={setConsultation}
            multiline
            textAlignVertical="top"
          />
          <Text style={[styles.aiHint, isIndigoHome && indigoStyles.aiHint]}>
            {consultation.trim()
              ? "このあと3つの質問で、相談を整えます。"
              : "このあと4つの質問で、相談を整えます。"}
          </Text>
        </View>

        {/* 主CTA。19節: 1画面に1つ。 */}
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="相談を続ける"
          onPress={openConsultation}
          style={({ pressed }) => [styles.primaryCta, isIndigoHome && indigoStyles.primaryCta, pressed && (isIndigoHome ? indigoStyles.primaryCtaPressed : styles.primaryCtaPressed)]}
        >
          <Text style={[styles.primaryCtaText, isIndigoHome && indigoStyles.primaryCtaText]}>相談を続ける</Text>
        </Pressable>

        {/* Search入口(補助CTA) */}
        <Button
          title="神社を探す"
          variant="outline"
          onPress={openSearch}
          accessibilityLabel="神社を探す"
          style={isIndigoHome ? indigoStyles.searchEntryCta : styles.searchEntryCta}
          textStyle={isIndigoHome ? indigoStyles.searchEntryText : undefined}
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

// 既存のWeb/Androidスタイルを保ち、iOSホームだけに重ねる。
const indigoStyles = StyleSheet.create({
  screen: { backgroundColor: homeIndigo.background },
  content: { backgroundColor: "transparent" },
  header: { height: undefined, minHeight: 60, justifyContent: "flex-start", gap: 12, borderBottomWidth: 0, marginBottom: 24 },
  brandBlock: { flex: 1, minWidth: 0 },
  logo: { width: 48, height: 48, borderRadius: 12 },
  brandName: { ...typography.subheading, color: homeIndigo.text },
  brandRuby: { ...typography.caption, color: homeIndigo.secondaryText },
  heroLead: { color: homeIndigo.text },
  heroSub: { color: homeIndigo.secondaryText },
  chatCard: { backgroundColor: homeIndigo.surface, borderColor: homeIndigo.border, marginTop: 12 },
  chatInput: { ...typography.body, lineHeight: undefined, color: homeIndigo.text },
  aiHint: { color: homeIndigo.secondaryText },
  primaryCta: { minHeight: ctaSizes.primaryHeight, height: "auto", paddingVertical: 16, paddingHorizontal: 20, backgroundColor: homeIndigo.action },
  primaryCtaPressed: { opacity: 0.82 },
  primaryCtaText: { color: homeIndigo.actionText },
  searchEntryCta: { marginTop: 12, minHeight: ctaSizes.mediumHeight, height: "auto", paddingVertical: 12, paddingHorizontal: 20, borderColor: homeIndigo.action, backgroundColor: "transparent" },
  searchEntryText: { color: homeIndigo.action },
  cloudTopLeft: { position: "absolute", left: -22 },
  cloudTopRight: { position: "absolute", right: -22, transform: [{ scaleX: -1 }] },
  cloudBottomLeft: { position: "absolute", bottom: 30, left: -18 },
  cloudBottomRight: { position: "absolute", bottom: 30, right: -18, transform: [{ scaleX: -1 }] },
  cloud: { width: 110, height: 36, opacity: 0.32 },
  cloudUpper: { position: "absolute", top: 0, left: 0, width: 76, height: 12, borderWidth: 1, borderColor: homeIndigo.ornament, borderRadius: 8 },
  cloudMiddle: { position: "absolute", top: 11, left: 26, width: 84, height: 12, borderWidth: 1, borderColor: homeIndigo.ornament, borderRadius: 8 },
  cloudLower: { position: "absolute", top: 22, left: 8, width: 60, height: 12, borderWidth: 1, borderColor: homeIndigo.ornament, borderRadius: 8 },
});
