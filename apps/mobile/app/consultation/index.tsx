import * as React from "react";
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Ionicons from "@expo/vector-icons/Ionicons";
import * as Location from "expo-location";

import { appColors as theme } from "../../design/theme";
import { typography } from "../../design/typography";
import { spacing } from "../../design/spacing";
import { radius } from "../../design/radius";
import { ctaSizes } from "../../design/ctaSizes";
import { cardSizes } from "../../design/cardSizes";
import { ConditionFieldsCard } from "../../components/ConditionFieldsCard";
import { resolveGoriyakuTagIds, VISIT_STYLE_OPTIONS, GORIYAKU_OPTIONS } from "../../lib/conditionPayload";
import { getOriginSession, setOriginSession } from "../../lib/originSession";
import type { UserOrigin } from "../../../../packages/shared/userOrigin";

// docs/design/ios-ui-spec-v2.md 08節: 相談の入力を段階化する。
// 旧実装はホーム1画面に相談文・テーマ・誕生日・参拝予定日・出発地点・
// 参拝スタイル・ご利益・補助条件を同居させており、8節が名指しで禁じる形だった。
//
// 入力項目は1つも増減させていない。Concierge へ渡すクエリの組み立ても
// 旧ホームの openConcierge と同じ契約のままにしてある。
//
// 41節で Concierge Input は Guided。(tabs) の外に置くことで、32節の
// 「Guided Journey 中はタブバーを原則非表示」も満たす。

const THEMES = [
  "疲れを整えたい",
  "迷いを整理したい",
  "前に進みたい",
  "静かに考えたい",
  "人との縁を見直したい",
  "仕事の流れを整えたい",
] as const;

// 13節: 質問文そのものを画面の主役にする。
// STEP 3 の問いだけ指示書の例文から変えている。例文「どんな参拝をしたいですか？」は
// 参拝スタイル(STEP 2)に対応する言い方で、ご利益の選択には合わないため。
const STEPS = [
  {
    title: "今、どんなことを\n整理したいですか？",
    support: "今の気持ちに近いものを選んでください。\n正解を選ぶ必要はありません。",
    skippable: false,
  },
  {
    title: "どんな時間を\n過ごしたいですか？",
    support: "参拝の過ごし方の希望があれば選んでください。",
    skippable: true,
  },
  {
    title: "どんなご縁を\n願いますか？",
    support: "気になるものがあれば選んでください。",
    skippable: true,
  },
  {
    title: "必要なら\n条件を追加",
    support: "すべて任意です。入れるほど提案の手がかりが増えます。",
    skippable: true,
  },
] as const;

const TOTAL = STEPS.length;

type SelectionCardProps = {
  label: string;
  selected: boolean;
  onPress: () => void;
};

// 15節: Default は surface + border。Selected は深藍の線 + 薄い深藍の面 + 小さな印。
// 朱でカード全面を塗らない。
function SelectionCard({ label, selected, onPress }: SelectionCardProps) {
  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityState={{ checked: selected }}
      accessibilityLabel={label}
      onPress={onPress}
      style={({ pressed }) => [styles.card, selected && styles.cardSelected, pressed && styles.cardPressed]}
    >
      <Text style={[styles.cardText, selected && styles.cardTextSelected]}>{label}</Text>
      {selected ? <Ionicons name="checkmark" size={18} color={theme.vermilion} /> : null}
    </Pressable>
  );
}

export default function ConsultationScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  // Concierge の「条件を変える」から戻ってくる場合、入力済みの値をそのまま復元する。
  // 受け取るキーは openConcierge が組み立てるクエリと同じもの。項目は増減させていない。
  const params = useLocalSearchParams<{
    q?: string;
    theme?: string;
    birthdate?: string;
    plannedVisitDate?: string;
    visitStyle?: string;
    goriyaku?: string;
    support?: string;
    topicDone?: string;
  }>();

  const restoredOrigin = React.useRef<UserOrigin | null>(getOriginSession()).current;

  // ホームの自由入力は STEP 1 そのものなので、書いてあれば STEP 1 を飛ばす。
  // Concierge の「条件を変える」からは topicDone を渡さない。渡すと相談文を
  // 直す手段が無くなるため、あちらからは STEP 1 を残す。
  const topicDone = params.topicDone === "1" && Boolean((params.q ?? "").trim());
  const firstStep = topicDone ? 1 : 0;

  const [step, setStep] = React.useState(firstStep);
  const [consultation, setConsultation] = React.useState(params.q ?? "");
  const [selectedTheme, setSelectedTheme] = React.useState<string | null>(params.theme || null);
  const [selectedVisitStyle, setSelectedVisitStyle] = React.useState<string | undefined>(params.visitStyle || undefined);
  const [selectedGoriyaku, setSelectedGoriyaku] = React.useState<string | undefined>(params.goriyaku || undefined);
  const [birthdate, setBirthdate] = React.useState(params.birthdate ?? "");
  const [plannedVisitDate, setPlannedVisitDate] = React.useState(params.plannedVisitDate ?? "");
  const [supportText, setSupportText] = React.useState(params.support ?? "");
  const [origin, setOrigin] = React.useState<UserOrigin | null>(restoredOrigin);
  const [locationStatus, setLocationStatus] = React.useState<"idle" | "loading" | "ready" | "error">(
    restoredOrigin ? "ready" : "idle",
  );

  const useCurrentLocation = async () => {
    setLocationStatus("loading");
    const permission = await Location.requestForegroundPermissionsAsync();
    if (permission.status !== "granted") {
      setLocationStatus("error");
      return;
    }
    try {
      const current = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      setOrigin({
        latitude: current.coords.latitude,
        longitude: current.coords.longitude,
        source: "device",
        displayName: "現在地",
        accuracy: "precise",
      });
      setLocationStatus("ready");
    } catch {
      setLocationStatus("error");
    }
  };

  // 旧ホームの openConcierge と同じ契約。渡す値も順序も変えていない。
  const openConcierge = () => {
    void resolveGoriyakuTagIds(selectedGoriyaku);

    const query = new URLSearchParams();
    if (consultation.trim()) query.set("q", consultation.trim());
    if (selectedTheme) query.set("theme", selectedTheme);
    if (birthdate.trim()) query.set("birthdate", birthdate.trim());
    if (plannedVisitDate.trim()) query.set("plannedVisitDate", plannedVisitDate.trim());
    setOriginSession(origin);
    if (selectedVisitStyle) query.set("visitStyle", selectedVisitStyle);
    if (selectedGoriyaku) query.set("goriyaku", selectedGoriyaku);
    if (supportText.trim()) query.set("support", supportText.trim());

    const search = query.toString();
    router.replace(search ? `/concierge?${search}` : "/concierge");
  };

  // 22節: 各ステップで戻れる。最初のステップではホームへ戻る。
  // STEP 1 を飛ばしている場合、戻り先はホーム(相談文を書いた場所)。
  const goBack = () => {
    if (step > firstStep) {
      setStep((current) => current - 1);
      return;
    }
    if (router.canGoBack()) router.back();
    else router.replace("/");
  };

  const goNext = () => {
    if (step < TOTAL - 1) setStep((current) => current + 1);
    else openConcierge();
  };

  // 相談内容を書き換えたのに、前の相談で選んだご縁がそのまま残っている状態。
  // 消さずに知らせるだけにする(誤字の修正でも選択が消えるのは煩わしいため)。
  // 相談文とご縁の「意味が合っているか」は判定しない。それは推薦側の領分で、
  // ここで判断すると Mobile が推薦の意味を作ることになる。
  // 見ているのは「params で受け取った文章から変わったか」という事実だけ。
  const incomingGoriyaku = params.goriyaku || undefined;
  const topicChanged = consultation.trim() !== (params.q ?? "").trim();
  const showGoriyakuNotice =
    topicChanged && Boolean(incomingGoriyaku) && selectedGoriyaku === incomingGoriyaku;

  const isLast = step === TOTAL - 1;
  const current = STEPS[step];

  return (
    <KeyboardAvoidingView
      style={[styles.screen, { paddingTop: insets.top }]}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      {/* 22節: Navigation Header を大きく作らない。21節: Progress を主役にしない。 */}
      <View style={styles.topBar}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={step > firstStep ? "前のステップへ戻る" : "相談をやめて戻る"}
          hitSlop={12}
          onPress={goBack}
          style={styles.backButton}
        >
          <Ionicons name="chevron-back" size={24} color={theme.accent} />
        </Pressable>
        <Text style={styles.stepLabel}>相談</Text>
        <Text style={styles.stepCount}>
          {step + 1} / {TOTAL}
        </Text>
      </View>
      <View
        accessibilityRole="progressbar"
        accessibilityValue={{ min: 1, max: TOTAL, now: step + 1 }}
        style={styles.progressTrack}
      >
        <View style={[styles.progressFill, { flex: step + 1 }]} />
        <View style={{ flex: TOTAL - step - 1 }} />
      </View>

      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text accessibilityRole="header" style={styles.title}>
          {current.title}
        </Text>
        <Text style={styles.support}>{current.support}</Text>

        {step === 0 ? (
          <View style={styles.group}>
            {THEMES.map((item) => (
              <SelectionCard
                key={item}
                label={item}
                selected={selectedTheme === item}
                onPress={() => setSelectedTheme(selectedTheme === item ? null : item)}
              />
            ))}
            <TextInput
              accessibilityLabel="相談内容"
              placeholder="自分の言葉で書いてもかまいません"
              placeholderTextColor={theme.mutedDark}
              style={styles.freeText}
              value={consultation}
              onChangeText={setConsultation}
              multiline
              textAlignVertical="top"
            />
          </View>
        ) : null}

        {step === 1 ? (
          <View style={styles.group}>
            {VISIT_STYLE_OPTIONS.map((item) => (
              <SelectionCard
                key={item}
                label={item}
                selected={selectedVisitStyle === item}
                onPress={() => setSelectedVisitStyle(selectedVisitStyle === item ? undefined : item)}
              />
            ))}
          </View>
        ) : null}

        {step === 2 ? (
          <View style={styles.group}>
            {showGoriyakuNotice ? (
              <View accessibilityRole="alert" style={styles.notice}>
                <Ionicons name="information-circle-outline" size={18} color={theme.warning} />
                <Text style={styles.noticeText}>
                  「{incomingGoriyaku}」は、前の相談で選んだものです。相談内容を書き直したので、
                  必要なら選び直してください。もう一度押すと外せます。
                </Text>
              </View>
            ) : null}
            {GORIYAKU_OPTIONS.map((item) => (
              <SelectionCard
                key={item}
                label={item}
                selected={selectedGoriyaku === item}
                onPress={() => setSelectedGoriyaku(selectedGoriyaku === item ? undefined : item)}
              />
            ))}
          </View>
        ) : null}

        {step === 3 ? (
          <View style={styles.group}>
            {/* 参拝スタイルとご利益は STEP 2 / 3 が持つ。ここでは残りの条件だけを出す。 */}
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
      </ScrollView>

      {/* 19節: Primary CTA は画面下部。1画面に1つ。 */}
      <View style={[styles.footer, { paddingBottom: insets.bottom + spacing.xlGap }]}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={isLast ? "この相談からご縁を見る" : "次へ"}
          onPress={goNext}
          style={({ pressed }) => [styles.cta, pressed && styles.ctaPressed]}
        >
          <Text style={styles.ctaText}>{isLast ? "この相談からご縁を見る" : "次へ"}</Text>
        </Pressable>

        {/* 20節/23節: 任意の条件はスキップできる。Underline は使わない。 */}
        {current.skippable ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={isLast ? "条件を入れずにご縁を見る" : "このステップをスキップする"}
            onPress={goNext}
            style={styles.secondary}
          >
            <Text style={styles.secondaryText}>{isLast ? "条件を入れずに進む" : "スキップ"}</Text>
          </Pressable>
        ) : null}
      </View>
    </KeyboardAvoidingView>
  );
}

const CONTENT_X = spacing.contentX;

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
  },
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.mdGap,
    paddingHorizontal: CONTENT_X,
    paddingTop: spacing.smGap,
    paddingBottom: spacing.inlineGap,
  },
  backButton: {
    minHeight: 44,
    minWidth: 44,
    justifyContent: "center",
    marginLeft: -spacing.mdGap,
  },
  stepLabel: {
    ...typography.label,
    color: theme.mutedSoft,
    flex: 1,
  },
  stepCount: {
    ...typography.footnoteStrong,
    color: theme.mutedSoft,
  },
  progressTrack: {
    flexDirection: "row",
    height: 3,
    marginHorizontal: CONTENT_X,
    borderRadius: radius.pill,
    backgroundColor: theme.border,
    overflow: "hidden",
  },
  progressFill: {
    backgroundColor: theme.accent,
  },
  content: {
    paddingHorizontal: CONTENT_X,
    paddingTop: spacing.sectionTop,
    paddingBottom: spacing.bottomSpace,
  },
  title: {
    ...typography.question,
    color: theme.accent,
  },
  support: {
    ...typography.subhead,
    color: theme.mutedSoft,
    marginTop: spacing.lgGap,
    marginBottom: spacing.sectionTop + spacing.smGap,
  },
  // 注意書き。warning #7E520F は沈み面に対して 5.25 で AA を満たす(実測)。
  // 左罫は Concierge の条件サマリと同じ文法。朱は主アクション専用なので使わない。
  notice: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
    backgroundColor: theme.surfaceSoft,
    borderLeftWidth: 3,
    borderLeftColor: theme.warning,
    borderRadius: radius.sm,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  noticeText: {
    ...typography.footnote,
    color: theme.warning,
    flex: 1,
  },

  group: {
    gap: spacing.mdGap,
  },
  card: {
    minHeight: 56,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.mdGap,
    paddingHorizontal: cardSizes.cardPaddingLg,
    paddingVertical: cardSizes.cardPaddingMd,
    borderRadius: radius.xl,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.border,
    backgroundColor: theme.surface,
  },
  cardSelected: {
    borderWidth: 2,
    borderColor: theme.accent,
    backgroundColor: theme.selectedSurface,
  },
  cardPressed: {
    opacity: 0.8,
  },
  cardText: {
    ...typography.body,
    color: theme.accent,
    flex: 1,
  },
  cardTextSelected: {
    ...typography.bodyStrong,
    color: theme.accent,
  },
  freeText: {
    ...typography.body,
    minHeight: 96,
    color: theme.text,
    backgroundColor: theme.surface,
    borderRadius: radius.xl,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.border,
    paddingHorizontal: cardSizes.cardPaddingLg,
    paddingVertical: cardSizes.cardPaddingMd,
  },
  footer: {
    paddingHorizontal: CONTENT_X,
    paddingTop: spacing.lgGap,
    gap: spacing.lgGap,
    borderTopWidth: cardSizes.borderWidth,
    borderTopColor: theme.borderSoft,
    backgroundColor: theme.background,
  },
  cta: {
    height: ctaSizes.primaryHeight,
    borderRadius: ctaSizes.primaryRadius,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.vermilion,
  },
  ctaPressed: {
    backgroundColor: theme.vermilionDeep,
  },
  ctaText: {
    ...typography.button,
    color: theme.surfaceRaised,
  },
  secondary: {
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  secondaryText: {
    ...typography.label,
    color: theme.accent,
  },
});
