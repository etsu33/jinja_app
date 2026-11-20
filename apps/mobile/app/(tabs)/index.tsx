import * as React from "react";
import { useFocusEffect, useRouter } from "expo-router";
import { ScrollView, View, Text, TextInput, StyleSheet, Pressable } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { setStatusBarStyle } from "expo-status-bar";
import { appColors as theme, dawnNight } from "../../design/theme";
import { LinearGradient } from "expo-linear-gradient";
import { WaPattern } from "../../components/common/WaPattern";
import { ctaSizes } from "../../design/ctaSizes";
import Button from "../../components/ui/Button";
import { trackSearchEntryClick } from "../../lib/searchAnalytics";
import { typography } from "../../design/typography";

// 紺の帯(masthead)の上下余白。上は safe area inset に足す。
// 帯は深藍の面なので、ステータスバーの下まで伸ばしてよい。文字は inset の
// 内側に収める。
const MASTHEAD_TOP_PADDING = 10;
// 帯に敷く文様の描画高さ。帯の実寸よりやや大きく取り、途中で切れて見えないようにする。
const MASTHEAD_PATTERN_HEIGHT = 220;
const MASTHEAD_BOTTOM_PADDING = 24;

// 帯の下、本文側の上余白。
const CONTENT_TOP_PADDING = 22;

export default function Home() {
  const router = useRouter();
  // タブ画面はネイティブヘッダーを持たないため、Dynamic Island / ステータスバーの
  // 高さを自分で避ける(下層画面はStackのヘッダーが避けている)。
  const insets = useSafeAreaInsets();
  const [consultation, setConsultation] = React.useState("");

  // 画面上端が深藍の帯なので、この画面だけステータスバーを明色にする。
  // root の _layout.tsx は地が生成りの前提で "dark" を指定しているため、
  // 離れるときに戻す。
  useFocusEffect(
    React.useCallback(() => {
      setStatusBarStyle("light");
      return () => setStatusBarStyle("dark");
    }, []),
  );

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
    <View style={styles.screen}>
      <View style={styles.column}>
        {/* 深藍の帯。アイコン(紺地に金の紋)と起動画面(濃藍から始まる朝焼け)から、
            本編の生成りへ降りる間を受け持つ。深藍は89箇所で文字色として使われて
            いるが、面として立つ場所がほとんど無かった。
            ロゴマークはまだ素材が無い。絵文字の鳥居は端末のフォント次第で字形が
            変わるため置かず、文字組だけで見せる。マークが用意できたら
            brandName の前に差し込む。
            スクロールさせない。帯が流れると生成りが明色のステータスバーの下へ
            来てしまう。 */}
        <View
          style={[
            styles.masthead,
            { paddingTop: insets.top + MASTHEAD_TOP_PADDING },
          ]}
        >
          {/* 地は相談フローと同じ藍。起動画面 → 帯 → 相談フローで色が繋がる。 */}
          <LinearGradient
            colors={[dawnNight.colors[0], dawnNight.colors[1]]}
            start={{ x: 0.1, y: 0 }}
            end={{ x: 0.9, y: 1 }}
            style={StyleSheet.absoluteFill}
          />
          {/* 帯は低いので流水は出さず、青海波だけ。 */}
          <View style={StyleSheet.absoluteFill} pointerEvents="none">
            <WaPattern height={MASTHEAD_PATTERN_HEIGHT} withStream={false} />
          </View>
          <Text style={styles.brandName}>神結び</Text>
          <Text style={styles.brandRuby}>kami musubi</Text>
          <Text style={styles.heroLead}>今の相談を、神社とのご縁につなげる</Text>
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.heroSub}>
            ここでは相談内容だけを整えます。次の画面で、今の相談から結ばれた神社を確認できます。
          </Text>

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
          <Text style={styles.aiHint}>
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
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.outside,
  },
  // 帯とスクロール領域を同じ幅の柱に収める。
  column: {
    flex: 1,
    width: "100%",
    maxWidth: 430,
    alignSelf: "center",
    backgroundColor: theme.background,
  },
  content: {
    paddingHorizontal: 20,
    paddingTop: CONTENT_TOP_PADDING,
    paddingBottom: 48,
  },

  // 深藍の帯
  // 文字はすべて生成り。紺の面に対して 12.59 で、UI部品の 3.0 も本文の 4.5 も満たす。
  masthead: {
    // 実際の地は LinearGradient。読み込み前の下地として同系色を置く。
    backgroundColor: dawnNight.colors[0],
    overflow: "hidden",
    paddingHorizontal: 20,
    paddingBottom: MASTHEAD_BOTTOM_PADDING,
    gap: 2,
  },
  brandName: {
    color: theme.background,
    fontSize: 20,
    fontWeight: "900",
    letterSpacing: 1,
  },
  brandRuby: {
    ...typography.caption,
    color: theme.background,
    opacity: 0.68,
    letterSpacing: 4,
  },
  heroLead: {
    ...typography.subheading,
    color: theme.background,
    marginTop: 14,
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
