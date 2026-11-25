// apps/mobile/app/compass/index.tsx
//
// 今月の参拝コンパス。Web の /compass（apps/web/src/features/compass/CompassClient.tsx）と
// 同じ流れ: 目的 → 出発地点 → 生年月日 → 今月の方向 → 参拝候補 → 神社詳細。
//
// 役割の線引き（ドライブ「KAMI MUSUBI コンシェルジュとコンパスの役割の線引き」2026-11-25）:
// コンパスは「生年月日 × 方位」。相談文の入力は置かない（相談はコンシェルジュ）。
//
// 「今週のテーマ・注目の神社」（Weekly）はこの画面には入れない（次のPRで扱う）。
import * as React from "react";
import { Linking, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import * as Location from "expo-location";

import Button from "../../components/ui/Button";
import { MobileOriginSelector } from "../../components/MobileOriginSelector";
import { CompassDirectionGrid } from "../../components/compass/CompassDirectionGrid";
import { appColors as theme, inputAppearance } from "../../design/platformTheme";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";
import { spacing } from "../../design/spacing";
import { typography } from "../../design/typography";
import {
  COMPASS_NOTICES,
  COMPASS_PURPOSES_ORDERED,
  COMPASS_PURPOSE_LABELS_JA,
  buildCompassRouteUrl,
  fetchCompassRecommendations,
  formatBirthdate,
  formatCompassDistance,
  formatTargetMonth,
  getDirectionNote,
  getDirectionStatusLabel,
  isValidBirthdate,
  parseBirthdate,
  resolveCompassCandidateMeaning,
  resolveCompassCandidateShrineFacts,
  resolveCompassShrineId,
  type BirthdateParts,
  type CompassNoticeState,
  type CompassPurpose,
  type CompassRecommendation,
  type CompassRecommendationsResponse,
} from "../../lib/compass";
import { trackCompassEntry, trackCompassResult } from "../../lib/compassAnalytics";
import { useProfileStore } from "../../store/profileStore";
import { pushBirthdayToServer } from "../../lib/birthdaySync";
import type { UserOrigin } from "../../../../packages/shared/userOrigin";

// 最初に見せる目的の数。Web と同じく、残りは「ほかの目的」で開く。
const PRIMARY_PURPOSE_COUNT = 6;

type UiState = "initial" | "loading" | "result" | "backend_error";

function PurposeChip({ purpose, selected, onPress }: { purpose: CompassPurpose; selected: boolean; onPress: () => void }) {
  const label = COMPASS_PURPOSE_LABELS_JA[purpose];
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="radio"
      accessibilityLabel={label}
      accessibilityState={{ checked: selected }}
      style={({ pressed }) => [styles.chip, selected && styles.chipSelected, pressed && styles.pressed]}
    >
      <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{label}</Text>
    </Pressable>
  );
}

function CandidateCard({
  rec,
  origin,
  onOpenShrine,
}: {
  rec: CompassRecommendation;
  origin: UserOrigin | null;
  onOpenShrine: (shrineId: string) => void;
}) {
  const shrineId = resolveCompassShrineId(rec);
  const name = typeof rec.name === "string" ? rec.name : "";
  const address = typeof rec.address === "string" && rec.address.trim() ? rec.address : null;
  const distance = formatCompassDistance(rec.distance_m);
  const meaning = resolveCompassCandidateMeaning(rec);
  const facts = resolveCompassCandidateShrineFacts(rec);
  const routeUrl = buildCompassRouteUrl(rec, origin);

  return (
    <View style={styles.candidate}>
      <View style={styles.candidateHeader}>
        <Text style={styles.candidateName}>{name}</Text>
        {distance ? <Text style={styles.candidateDistance}>{distance}</Text> : null}
      </View>
      {address ? <Text style={styles.candidateAddress}>{address}</Text> : null}

      {meaning ? (
        <View style={styles.candidateBlock}>
          <Text style={styles.blockLabel}>今のあなたとの接点</Text>
          <Text style={styles.blockText}>
            {meaning.text}
            {meaning.isKamiMusubiInterpretation ? <Text style={styles.blockNote}>（KAMI MUSUBIの解釈）</Text> : null}
          </Text>
        </View>
      ) : null}

      {facts ? (
        <View style={styles.candidateBlock}>
          <Text style={styles.blockLabel}>この神社について</Text>
          {facts.deityName ? (
            <Text style={styles.blockText}>
              <Text style={styles.blockNote}>祭神　</Text>
              {facts.deityName}
            </Text>
          ) : null}
          {facts.history ? (
            <>
              {facts.history.typeLabel ? <Text style={styles.blockNote}>{facts.history.typeLabel}</Text> : null}
              <Text style={styles.blockTextSecondary} numberOfLines={2}>
                {facts.history.content}
              </Text>
            </>
          ) : null}
        </View>
      ) : null}

      <View style={styles.candidateActions}>
        {shrineId ? (
          <Button
            title="神社を見る"
            variant="outline"
            size="compact"
            onPress={() => onOpenShrine(shrineId)}
            accessibilityLabel={`${name}の詳細を見る`}
          />
        ) : null}
        {routeUrl ? (
          <Button
            title="経路を見る"
            variant="neutral"
            size="compact"
            onPress={() => void Linking.openURL(routeUrl)}
            accessibilityLabel={`${name}への経路を地図で見る`}
          />
        ) : null}
      </View>
    </View>
  );
}

export default function CompassScreen() {
  const router = useRouter();
  const { ref } = useLocalSearchParams<{ ref?: string }>();
  const savedBirthday = useProfileStore((state) => state.userProfile.birthday);
  const setBirthday = useProfileStore((state) => state.setBirthday);

  const [now] = React.useState(() => new Date());
  const [purpose, setPurpose] = React.useState<CompassPurpose | null>(null);
  const [showAllPurposes, setShowAllPurposes] = React.useState(false);
  const [origin, setOrigin] = React.useState<UserOrigin | null>(null);
  const [locationStatus, setLocationStatus] = React.useState<"idle" | "loading" | "ready" | "error">("idle");
  const [birthdate, setBirthdate] = React.useState<BirthdateParts>(() => parseBirthdate(savedBirthday));
  const [attempted, setAttempted] = React.useState(false);
  const [uiState, setUiState] = React.useState<UiState>("initial");
  const [result, setResult] = React.useState<CompassRecommendationsResponse | null>(null);
  // 結果を得たときに送った出発地点。送信後に出発地点を変えても、経路の出発地がずれないよう別に持つ。
  const [resultOrigin, setResultOrigin] = React.useState<UserOrigin | null>(null);

  const birthdateEdited = React.useRef(false);
  const entryTracked = React.useRef(false);
  const monthRef = React.useRef<React.ComponentRef<typeof TextInput>>(null);
  const dayRef = React.useRef<React.ComponentRef<typeof TextInput>>(null);

  React.useEffect(() => {
    if (entryTracked.current) return;
    entryTracked.current = true;
    trackCompassEntry(ref === "home" ? "home" : "direct");
  }, [ref]);

  // プロフィールの読み込みが後から終わったときも、まだ触っていなければ反映する。
  React.useEffect(() => {
    if (!savedBirthday || birthdateEdited.current) return;
    setBirthdate(parseBirthdate(savedBirthday));
  }, [savedBirthday]);

  const useCurrentLocation = async () => {
    setLocationStatus("loading");
    try {
      const permission = await Location.requestForegroundPermissionsAsync();
      if (permission.status !== "granted") {
        setLocationStatus("error");
        return;
      }
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

  const hasBirthdateInput = Boolean(birthdate.year || birthdate.month || birthdate.day);
  const validBirthdate = isValidBirthdate(birthdate);
  const missingPurpose = attempted && !purpose;
  const missingOrigin = attempted && !origin;
  const missingBirthdate = attempted && !hasBirthdateInput;
  const invalidBirthdate = attempted && hasBirthdateInput && !validBirthdate;

  const editBirthdate = (patch: Partial<BirthdateParts>) => {
    birthdateEdited.current = true;
    setBirthdate((current) => ({ ...current, ...patch }));
  };

  const submit = async () => {
    setAttempted(true);
    if (!purpose || !origin || !validBirthdate) return;

    const submittedBirthdate = formatBirthdate(birthdate);
    setUiState("loading");
    setResult(null);
    setResultOrigin(null);

    const fetched = await fetchCompassRecommendations({ purpose, birthdate: submittedBirthdate, origin });

    if (!fetched.ok) {
      setUiState("backend_error");
      trackCompassResult({
        resultState: "backend_error",
        purpose,
        originMode: origin.source,
        recommendationCount: null,
        recommendationInstanceId: null,
        calculationMethod: null,
        distanceStageKm: null,
        directionCandidateCount: null,
        distanceCandidateCount: null,
      });
      return;
    }

    const body = fetched.response;
    setResult(body);
    setResultOrigin(origin);
    setUiState("result");

    // 方位の計算に使えた生年月日は、プロフィールに保存して次回から入れておく。
    if (body.state !== "invalid_purpose") {
      setBirthday(submittedBirthdate);
      // マイページと同じく、ログイン中ならサーバーにも保存する（lib/birthdaySync.ts）。
      void pushBirthdayToServer(submittedBirthdate);
    }

    trackCompassResult({
      resultState: body.state,
      purpose,
      originMode: origin.source,
      recommendationCount: body.state === "recommendation_success" ? (body.recommendations?.length ?? 0) : null,
      recommendationInstanceId: body.recommendation_instance_id ?? null,
      calculationMethod: body.direction_context?.calculationMethod ?? null,
      distanceStageKm: body.distance_stage_km ?? null,
      directionCandidateCount: body.direction_candidate_count ?? null,
      distanceCandidateCount: body.distance_candidate_count ?? null,
    });
  };

  const isLoading = uiState === "loading";
  const directionContext = result?.direction_context ?? null;
  const statusLabel = directionContext ? getDirectionStatusLabel(directionContext.calculationMethod) : null;
  const noticeState: CompassNoticeState | null =
    uiState === "backend_error"
      ? "backend_error"
      : result && result.state !== "recommendation_success" && result.state !== "invalid_purpose"
        ? result.state
        : null;
  const notice = noticeState ? COMPASS_NOTICES[noticeState] : null;
  const purposes = showAllPurposes ? COMPASS_PURPOSES_ORDERED : COMPASS_PURPOSES_ORDERED.slice(0, PRIMARY_PURPOSE_COUNT);

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <View style={styles.intro}>
        <Text style={styles.eyebrow}>{formatTargetMonth(now)}</Text>
        <Text style={styles.heading} accessibilityRole="header">今月の参拝コンパス</Text>
        <Text style={styles.lead}>今月の流れと目的から、向かう方向と参拝候補を見つけます。</Text>
      </View>

      {/* 目的 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle} accessibilityRole="header">目的</Text>
        <View style={styles.chipRow} accessibilityRole="radiogroup">
          {purposes.map((value) => (
            <PurposeChip key={value} purpose={value} selected={purpose === value} onPress={() => setPurpose(value)} />
          ))}
        </View>
        {!showAllPurposes ? (
          <Pressable
            onPress={() => setShowAllPurposes(true)}
            accessibilityRole="button"
            accessibilityLabel="ほかの目的を表示する"
            style={({ pressed }) => [styles.moreButton, pressed && styles.pressed]}
          >
            <Text style={styles.moreText}>ほかの目的</Text>
          </Pressable>
        ) : null}
        {missingPurpose ? <Text accessibilityRole="alert" style={styles.error}>目的を選択してください。</Text> : null}
      </View>

      {/* 出発地点 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle} accessibilityRole="header">出発地点</Text>
        <MobileOriginSelector
          origin={origin}
          onChange={setOrigin}
          onUseDevice={() => void useCurrentLocation()}
          locationStatus={locationStatus}
          disabled={isLoading}
        />
        {missingOrigin ? <Text accessibilityRole="alert" style={styles.error}>出発地点を選択してください。</Text> : null}
      </View>

      {/* 生年月日 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle} accessibilityRole="header">生年月日（方位計算に使用）</Text>
        <View style={styles.birthRow} accessibilityLabel="生年月日">
          <TextInput
            {...inputAppearance}
            accessibilityLabel="生年月日の年"
            value={birthdate.year}
            onChangeText={(value) => {
              const year = value.replace(/\D/g, "").slice(0, 4);
              editBirthdate({ year });
              if (year.length === 4) monthRef.current?.focus();
            }}
            placeholder="YYYY"
            placeholderTextColor={theme.mutedDark}
            keyboardType="number-pad"
            maxLength={4}
            style={[styles.birthInput, styles.birthInputYear]}
          />
          <Text style={styles.birthUnit}>年</Text>
          <TextInput
            {...inputAppearance}
            ref={monthRef}
            accessibilityLabel="生年月日の月"
            value={birthdate.month}
            onChangeText={(value) => {
              const month = value.replace(/\D/g, "").slice(0, 2);
              editBirthdate({ month });
              if (month.length === 2 && Number(month) >= 1 && Number(month) <= 12) dayRef.current?.focus();
            }}
            placeholder="MM"
            placeholderTextColor={theme.mutedDark}
            keyboardType="number-pad"
            maxLength={2}
            style={styles.birthInput}
          />
          <Text style={styles.birthUnit}>月</Text>
          <TextInput
            {...inputAppearance}
            ref={dayRef}
            accessibilityLabel="生年月日の日"
            value={birthdate.day}
            onChangeText={(value) => editBirthdate({ day: value.replace(/\D/g, "").slice(0, 2) })}
            placeholder="DD"
            placeholderTextColor={theme.mutedDark}
            keyboardType="number-pad"
            maxLength={2}
            style={styles.birthInput}
          />
          <Text style={styles.birthUnit}>日</Text>
        </View>
        <Text style={styles.hint}>入力した生年月日はこの端末のプロフィールに保存し、次回から自動で入ります。</Text>
        {missingBirthdate ? <Text accessibilityRole="alert" style={styles.error}>生年月日を入力してください。</Text> : null}
        {invalidBirthdate ? <Text accessibilityRole="alert" style={styles.error}>正しい生年月日を入力してください。</Text> : null}
      </View>

      <Button
        title={isLoading ? "確認しています…" : "今月の方向を確認する"}
        variant="primary"
        onPress={() => void submit()}
        loading={isLoading}
        accessibilityLabel="今月の方向を確認する"
        style={styles.submit}
      />

      {/* 今月の方向 */}
      {directionContext ? (
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionTitle} accessibilityRole="header">今月、意識したい方向</Text>
            {statusLabel ? <Text style={styles.statusPill}>{statusLabel}</Text> : null}
          </View>
          <CompassDirectionGrid referenceDirections={directionContext.referenceDirections} />
          <Text style={styles.directionNote}>{getDirectionNote(directionContext.calculationMethod)}（参考情報です）</Text>
        </View>
      ) : null}

      {/* うまく出なかったとき */}
      {notice ? (
        <View style={styles.notice} accessibilityLiveRegion="polite">
          <Text style={styles.noticeTitle}>{notice.title}</Text>
          <Text style={styles.noticeText}>{notice.description}</Text>
          {notice.offerConcierge ? (
            <Button
              title="コンシェルジュで相談する"
              variant="outline"
              size="compact"
              onPress={() => router.push("/consultation")}
              accessibilityLabel="コンシェルジュで相談する"
              style={styles.noticeAction}
            />
          ) : null}
        </View>
      ) : null}

      {/* 参拝候補 */}
      {result?.state === "recommendation_success" ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle} accessibilityRole="header">この方向の参拝候補</Text>
          {result.recommendations.map((rec, index) => (
            <CandidateCard
              key={resolveCompassShrineId(rec) ?? `candidate-${index}`}
              rec={rec}
              origin={resultOrigin}
              onOpenShrine={(shrineId) => router.push(`/shrines/${shrineId}`)}
            />
          ))}
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
  },
  content: {
    paddingHorizontal: spacing.screenX,
    paddingTop: spacing.sectionTop,
    paddingBottom: spacing.bottomSpaceLg,
    gap: spacing.xlGap,
  },
  intro: {
    gap: spacing.smGap,
  },
  eyebrow: {
    ...typography.eyebrow,
    color: theme.accent,
  },
  heading: {
    ...typography.heading,
    color: theme.text,
  },
  lead: {
    ...typography.subhead,
    color: theme.mutedSoft,
  },
  section: {
    gap: spacing.lgGap,
    paddingTop: spacing.xlGap,
    borderTopWidth: cardSizes.borderWidth,
    borderTopColor: theme.borderHeader,
  },
  sectionHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.smGap,
  },
  sectionTitle: {
    ...typography.title,
    color: theme.text,
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.smGap,
  },
  chip: {
    minHeight: 44,
    paddingHorizontal: spacing.xlGap,
    borderRadius: radius.pill,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.border,
    backgroundColor: theme.surfaceSoft,
    justifyContent: "center",
  },
  chipSelected: {
    borderColor: theme.accent,
    backgroundColor: theme.surface,
  },
  chipText: {
    ...typography.label,
    color: theme.mutedSoft,
  },
  chipTextSelected: {
    color: theme.accent,
    fontWeight: "700",
  },
  moreButton: {
    alignSelf: "flex-start",
    minHeight: 44,
    justifyContent: "center",
  },
  moreText: {
    ...typography.footnoteStrong,
    color: theme.accent,
  },
  pressed: {
    opacity: 0.8,
  },
  birthRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.smGap,
  },
  birthInput: {
    ...typography.body,
    flex: 1,
    minHeight: 44,
    borderRadius: radius.xs,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.border,
    backgroundColor: theme.surfaceSoft,
    color: theme.text,
    textAlign: "center",
    paddingHorizontal: spacing.smGap,
  },
  birthInputYear: {
    flex: 1.4,
  },
  birthUnit: {
    ...typography.subhead,
    color: theme.muted,
  },
  hint: {
    ...typography.footnote,
    color: theme.muted,
  },
  error: {
    ...typography.footnote,
    color: theme.error,
  },
  submit: {
    marginTop: spacing.smGap,
  },
  statusPill: {
    ...typography.caption,
    color: theme.mutedSoft,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.border,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.smGap,
    paddingVertical: 2,
    overflow: "hidden",
  },
  directionNote: {
    ...typography.footnote,
    color: theme.muted,
    textAlign: "center",
  },
  notice: {
    gap: spacing.smGap,
    padding: cardSizes.cardPaddingLg,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderHeader,
    backgroundColor: theme.surfaceSoft,
  },
  noticeTitle: {
    ...typography.title,
    color: theme.text,
  },
  noticeText: {
    ...typography.subhead,
    color: theme.muted,
  },
  noticeAction: {
    alignSelf: "flex-start",
    marginTop: spacing.smGap,
  },
  candidate: {
    gap: spacing.smGap,
    paddingVertical: spacing.lgGap,
    borderBottomWidth: cardSizes.borderWidth,
    borderBottomColor: theme.borderHeader,
  },
  candidateHeader: {
    flexDirection: "row",
    alignItems: "baseline",
    justifyContent: "space-between",
    gap: spacing.smGap,
  },
  candidateName: {
    ...typography.bodyStrong,
    color: theme.text,
    flexShrink: 1,
  },
  candidateDistance: {
    ...typography.footnote,
    color: theme.muted,
  },
  candidateAddress: {
    ...typography.footnote,
    color: theme.muted,
  },
  candidateBlock: {
    gap: spacing.tightGap,
    marginTop: spacing.tightGap,
  },
  blockLabel: {
    ...typography.caption,
    color: theme.accent,
  },
  blockText: {
    ...typography.subhead,
    color: theme.text,
  },
  blockTextSecondary: {
    ...typography.subhead,
    color: theme.mutedSoft,
  },
  blockNote: {
    ...typography.footnote,
    color: theme.muted,
  },
  candidateActions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.smGap,
    marginTop: spacing.smGap,
  },
});
