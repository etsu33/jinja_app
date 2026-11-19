import * as React from "react";
import { useRouter } from "expo-router";
import { ScrollView, View, Text, TextInput, StyleSheet, Pressable } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { appColors as theme } from "../../design/theme";
import { shadows } from "../../design/shadow";
import { ConditionFieldsCard } from "../../components/ConditionFieldsCard";
import Button from "../../components/ui/Button";
import { resolveGoriyakuTagIds } from "../../lib/conditionPayload";
import * as Location from "expo-location";
import type { UserOrigin } from "../../../../packages/shared/userOrigin";
import { setOriginSession } from "../../lib/originSession";
import { trackSearchEntryClick } from "../../lib/searchAnalytics";
import { buildSearchFilters } from "../../lib/searchFilters";
import { typography } from "../../design/typography";
import Ionicons from "@expo/vector-icons/Ionicons";

// 送信ボタンの矢印。旧実装は "↑" のグリフだった。
const SEND_ICON_SIZE = 22;

const THEMES = [
  "疲れを整えたい",
  "迷いを整理したい",
  "前に進みたい",
  "静かに考えたい",
  "人との縁を見直したい",
  "仕事の流れを整えたい",
] as const;

// 画面内コンテンツの上余白。safe area inset の内側に置く。
const CONTENT_TOP_PADDING = 22;

export default function Home() {
  const router = useRouter();
  // タブ画面はネイティブヘッダーを持たないため、Dynamic Island / ステータスバーの
  // 高さを自分で避ける(下層画面はStackのヘッダーが避けている)。
  const insets = useSafeAreaInsets();
  const [consultation, setConsultation] = React.useState("");
  const [selectedTheme, setSelectedTheme] = React.useState<string | null>(null);
  const [showConditions, setShowConditions] = React.useState(false);
  const [selectedVisitStyle, setSelectedVisitStyle] = React.useState<string | undefined>();
  const [birthdate, setBirthdate] = React.useState("");
  const [plannedVisitDate, setPlannedVisitDate] = React.useState("");
  const [origin, setOrigin] = React.useState<UserOrigin | null>(null);
  const [locationStatus, setLocationStatus] = React.useState<"idle" | "loading" | "ready" | "error">("idle");
  const [selectedGoriyaku, setSelectedGoriyaku] = React.useState<string | undefined>();
  const [supportText, setSupportText] = React.useState("");

  const conditionCount = [birthdate.trim(), plannedVisitDate.trim(), selectedVisitStyle, selectedGoriyaku, supportText.trim()].filter(
    Boolean,
  ).length;
  const conditionToggleLabel = `${showConditions ? "条件を閉じる" : "条件を追加"}${
    conditionCount > 0 ? `（${conditionCount}）` : ""
  }`;
  const conditionSummaryText = [
    selectedVisitStyle,
    selectedGoriyaku,
    birthdate.trim() ? "誕生日あり" : undefined,
    plannedVisitDate.trim() ? `参拝予定日 ${plannedVisitDate.trim()}` : undefined,
    supportText.trim() ? "補助条件あり" : undefined,
  ]
    .filter(Boolean)
    .join(" / ");

  const openSearch = () => {
    trackSearchEntryClick();
    // Searchへ渡してよいのは、Search側の既存フィルター処理(SHRINES.tags)と
    // 意味が一致する固定ラベル(ご利益)のみ。相談文・誕生日・参拝予定日・出発地点・
    // 参拝スタイル・補助条件は渡さない(docs/product/mobile-user-flow.md 8節・10節)。
    const filters = buildSearchFilters([selectedGoriyaku]);
    if (!filters) {
      router.push("/search");
      return;
    }
    const params = new URLSearchParams();
    params.set("filters", filters);
    router.push(`/search?${params.toString()}`);
  };

  const openConcierge = () => {
    // Concierge画面側のgoriyaku_tag_ids解決(resolveGoriyakuTagIds)が使うキャッシュを先読みしておく。
    // payload構築は引き続きConcierge画面のsubmit()が担うため、ここでの結果は使わない。
    void resolveGoriyakuTagIds(selectedGoriyaku);

    const params = new URLSearchParams();
    if (consultation.trim()) params.set("q", consultation.trim());
    if (selectedTheme) params.set("theme", selectedTheme);
    if (birthdate.trim()) params.set("birthdate", birthdate.trim());
    if (plannedVisitDate.trim()) params.set("plannedVisitDate", plannedVisitDate.trim());
    setOriginSession(origin);
    if (selectedVisitStyle) params.set("visitStyle", selectedVisitStyle);
    if (selectedGoriyaku) params.set("goriyaku", selectedGoriyaku);
    if (supportText.trim()) params.set("support", supportText.trim());
    const query = params.toString();
    router.push(query ? `/concierge?${query}` : "/concierge");
  };

  const useCurrentLocation = async () => {
    setLocationStatus("loading");
    const permission = await Location.requestForegroundPermissionsAsync();
    if (permission.status !== "granted") { setLocationStatus("error"); return; }
    try {
      const current = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      setOrigin({ latitude: current.coords.latitude, longitude: current.coords.longitude, source: "device", displayName: "現在地", accuracy: "precise" });
      setLocationStatus("ready");
    } catch { setLocationStatus("error"); }
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

        {/* テーマチップ */}
        <View style={styles.themeSection}>
          <Text style={styles.themeLabel}>まずは近い相談テーマを選ぶ</Text>
          <View style={styles.themeGrid}>
            {THEMES.map((t) => {
              const active = selectedTheme === t;
              return (
                <Pressable
                  key={t}
                  accessibilityRole="button"
                  accessibilityLabel={t}
                  accessibilityState={{ selected: active }}
                  onPress={() => setSelectedTheme(active ? null : t)}
                  style={[styles.themePill, active && styles.themePillActive]}
                >
                  <Text style={[styles.themePillText, active && styles.themePillTextActive]}>{t}</Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        {/* 自由入力カード */}
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
          <View style={styles.chatFooter}>
            <Text style={styles.aiHint}>相談内容を整えて、ご縁の神社へ進みます</Text>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="相談内容を送信する"
              onPress={openConcierge}
              style={styles.sendButton}
            >
              <Ionicons name="arrow-up" size={SEND_ICON_SIZE} color={theme.background} />
            </Pressable>
          </View>
        </View>

        {/* 条件追加トグル */}
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={conditionToggleLabel}
          accessibilityState={{ expanded: showConditions }}
          onPress={() => setShowConditions((c) => !c)}
          style={styles.accordionToggle}
        >
          <Text style={styles.accordionToggleText}>{conditionToggleLabel}</Text>
        </Pressable>

        {!showConditions && conditionSummaryText ? (
          <Text style={styles.conditionSummaryText}>{conditionSummaryText}</Text>
        ) : null}

        {showConditions ? (
          <View style={styles.conditionHint}>
            <ConditionFieldsCard
              birthdate={birthdate}
              onChangeBirthdate={setBirthdate}
              plannedVisitDate={plannedVisitDate}
              onChangePlannedVisitDate={setPlannedVisitDate}
              locationStatus={locationStatus}
              onUseCurrentLocation={() => void useCurrentLocation()}
              origin={origin}
              onChangeOrigin={setOrigin}
              selectedVisitStyle={selectedVisitStyle}
              onSelectVisitStyle={setSelectedVisitStyle}
              selectedGoriyaku={selectedGoriyaku}
              onSelectGoriyaku={setSelectedGoriyaku}
              supportText={supportText}
              onChangeSupportText={setSupportText}
            />
          </View>
        ) : null}

        {/* 主CTA */}
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="この相談からご縁を見る"
          onPress={openConcierge}
          style={styles.primaryCta}
        >
          <Text style={styles.primaryCtaText}>この相談からご縁を見る</Text>
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
    ...shadows.softCard,
  },
  chatInput: {
    ...typography.bodyStrong,
    minHeight: 78,
    color: theme.text,
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
    ...typography.footnote,
    flex: 1,
    color: theme.mutedDark,
  },
  sendButton: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: theme.accent,
    alignItems: "center",
    justifyContent: "center",
  },

  // テーマチップ
  themeSection: {
    marginTop: 0,
  },
  themeLabel: {
    ...typography.eyebrow,
    color: theme.muted,
    marginBottom: 12,
  },
  themeGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  themePill: {
    // HIGの最小タップ領域44pt。文字と余白だけでは37ptにしかならない。
    minHeight: 44,
    justifyContent: "center",
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 999,
    backgroundColor: theme.surfaceSoft,
    borderWidth: 1,
    borderColor: theme.borderMuted,
  },
  themePillActive: {
    backgroundColor: theme.accent,
    borderColor: theme.accent,
  },
  themePillText: {
    ...typography.footnoteStrong,
    color: theme.mutedSoft,
  },
  themePillTextActive: {
    color: theme.background,
  },

  // 条件追加
  accordionToggle: {
    // HIGの最小タップ領域44pt。文字と余白だけでは37ptにしかならない。
    minHeight: 44,
    justifyContent: "center",
    marginTop: 18,
    paddingVertical: 8,
  },
  accordionToggleText: {
    ...typography.label,
    color: theme.mutedSoft,
  },
  conditionSummaryText: {
    ...typography.footnote,
    color: theme.muted,
    marginTop: -4,
    marginBottom: 4,
  },
  conditionHint: {
    borderRadius: 14,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    paddingHorizontal: 14,
    paddingVertical: 14,
  },

  // 主CTA
  // 画面でただ一つの朱。ここ以外は深藍で受ける。
  primaryCta: {
    height: 54,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.vermilion,
    marginTop: 20,
    shadowColor: theme.vermilion,
    ...shadows.goldCta,
  },
  primaryCtaText: {
    ...typography.button,
    color: theme.background,
  },
  searchEntryCta: {
    marginTop: 12,
  },

});
