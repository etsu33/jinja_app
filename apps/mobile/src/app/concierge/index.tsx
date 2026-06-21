import * as React from "react";
import {
  KeyboardAvoidingView,
  Platform,
  View,
  Text,
  TextInput,
  Pressable,
  ScrollView,
  StyleSheet,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { kamimusubiDark as theme } from "../../../app/theme";

// ────────────────────────────────────────────
// 型
// ────────────────────────────────────────────
type RecommendationCard = {
  id: string;
  name: string;
  area: string;
  reason: string;
  tags: string[];
  shrineId?: string;
};

// ────────────────────────────────────────────
// ダミーデータ（APIが繋がったら差し替え）
// ────────────────────────────────────────────
const DUMMY_RESULTS: RecommendationCard[] = [
  {
    id: "r1",
    name: "明治神宮",
    area: "東京都渋谷区",
    reason: "仕事の迷いや転機に向き合う際、静かな杜の中で自分を見つめ直せる神域です。",
    tags: ["開運招福", "厄除け", "縁結び"],
    shrineId: "meiji",
  },
  {
    id: "r2",
    name: "神田明神",
    area: "東京都千代田区",
    reason: "仕事運・商売繁盛の御利益で知られ、新しい一歩を踏み出す力を授けてくれます。",
    tags: ["仕事運", "商売繁盛", "厄除け"],
    shrineId: "kanda",
  },
  {
    id: "r3",
    name: "根津神社",
    area: "東京都文京区",
    reason: "静かな境内で心を落ち着かせ、今の気持ちを整理するのに向いています。",
    tags: ["縁結び", "健康長寿"],
    shrineId: "nezu",
  },
];

// ────────────────────────────────────────────
// 推薦結果カード
// ────────────────────────────────────────────
function ResultCard({
  card,
  rank,
  onDetail,
}: {
  card: RecommendationCard;
  rank: number;
  onDetail: () => void;
}) {
  return (
    <View style={styles.card}>
      {/* ランクバッジ */}
      <View style={styles.rankRow}>
        <View style={styles.rankBadge}>
          <Text style={styles.rankBadgeText}>{rank}</Text>
        </View>
        <Text style={styles.rankLabel}>おすすめ候補</Text>
        <View style={styles.rankLine} />
      </View>

      {/* 神社名 + エリア */}
      <View style={styles.cardTitleBlock}>
        <Text style={styles.cardName}>{card.name}</Text>
        <Text style={styles.cardArea}>{card.area}</Text>
      </View>

      {/* 推薦理由 */}
      <Text style={styles.cardReason}>{card.reason}</Text>

      {/* タグ */}
      {card.tags.length > 0 ? (
        <View style={styles.tagRow}>
          {card.tags.map((tag) => (
            <View key={tag} style={styles.tagPill}>
              <Text style={styles.tagText}>{tag}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {/* CTA */}
      <View style={styles.ctaRow}>
        <Pressable onPress={onDetail} style={styles.ctaPrimary}>
          <Text style={styles.ctaPrimaryText}>詳細を見る</Text>
        </Pressable>
      </View>
    </View>
  );
}

// ────────────────────────────────────────────
// メイン画面
// ────────────────────────────────────────────
export default function ConciergeScreen() {
  const params = useLocalSearchParams<{ q?: string; theme?: string }>();
  const router = useRouter();

  const initialQuery = [params.q, params.theme].filter(Boolean).join(" ").trim();

  const [input, setInput] = React.useState(initialQuery);
  const [consultationText, setConsultationText] = React.useState(initialQuery);
  const [submitted, setSubmitted] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState<RecommendationCard[]>([]);
  const lastInitialQueryRef = React.useRef<string | null>(null);

  // URLの相談内容が変わったら自動送信する
  React.useEffect(() => {
    if (!initialQuery || lastInitialQueryRef.current === initialQuery) return;

    lastInitialQueryRef.current = initialQuery;
    setInput(initialQuery);
    void submit(initialQuery);
    // submitはこの画面内の状態更新関数だけを使うため、initialQueryの変更だけを監視する
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  const submit = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    setConsultationText(trimmed);
    setInput("");
    setLoading(true);
    setSubmitted(false);

    // ダミー遅延（APIに差し替え予定）
    await new Promise((r) => setTimeout(r, 1200));

    setResults(DUMMY_RESULTS);
    setLoading(false);
    setSubmitted(true);
  };

  const handleSend = () => void submit(input);

  const handleDetail = (card: RecommendationCard) => {
    if (card.shrineId) {
      router.push(`/shrines/${card.shrineId}`);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* ヘッダー */}
        <View style={styles.header}>
          <Pressable onPress={() => router.back()} style={styles.backBtn}>
            <Text style={styles.backText}>← 戻る</Text>
          </Pressable>
          <Text style={styles.headerTitle}>おすすめの神社</Text>
        </View>

        {/* 相談内容 */}
        <View style={styles.consultationArea}>
          <View style={styles.consultationCard}>
            <Text style={styles.consultationLabel}>相談内容</Text>
            <Text style={styles.consultationText}>
              {consultationText || "ホームで選んだ相談内容をもとに、おすすめの神社を表示します。"}
            </Text>
          </View>

          {loading ? (
            <View style={styles.loadingRow}>
              <Text style={styles.loadingText}>新しい相談内容から、ご縁を結び直しています…</Text>
            </View>
          ) : null}
        </View>

        {/* 結果カード */}
        {submitted && results.length > 0 ? (
          <View style={styles.resultsArea}>
            <View style={styles.resultsIntro}>
              <Text style={styles.resultsLabel}>今の相談から結ばれた神社</Text>
              <Text style={styles.resultsLead}>ホームで選んだ相談内容に近い意味やご利益を持つ神社です。</Text>
            </View>
            {results.map((card, i) => (
              <ResultCard
                key={card.id}
                card={card}
                rank={i + 1}
                onDetail={() => handleDetail(card)}
              />
            ))}
          </View>
        ) : null}
      </ScrollView>

      {/* 入力バー */}
      <View style={styles.inputBar}>
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder="条件を変えたい時だけ、追加で相談を書く"
          placeholderTextColor={theme.mutedDark}
          style={styles.input}
          multiline
          editable={!loading}
        />
        <Pressable
          onPress={handleSend}
          style={[styles.sendBtn, loading && styles.sendBtnDisabled]}
          disabled={loading}
        >
          <Text style={styles.sendText}>↑</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

// ────────────────────────────────────────────
// スタイル
// ────────────────────────────────────────────
const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
  },
  scrollContent: {
    paddingBottom: 104,
  },

  // ヘッダー
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingHorizontal: 18,
    paddingTop: 18,
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: theme.borderHeader,
  },
  backBtn: {
    paddingVertical: 4,
    paddingRight: 8,
  },
  backText: {
    color: theme.gold,
    fontSize: 14,
    fontWeight: "700",
  },
  headerTitle: {
    color: theme.text,
    fontSize: 17,
    fontWeight: "800",
    letterSpacing: 0.5,
  },

  consultationArea: {
    paddingHorizontal: 18,
    paddingTop: 16,
    gap: 8,
  },
  consultationCard: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderGold,
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 14,
    gap: 6,
  },
  consultationLabel: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.2,
  },
  consultationText: {
    color: theme.text,
    fontSize: 15,
    lineHeight: 22,
    fontWeight: "800",
  },

  loadingRow: {
    paddingVertical: 8,
  },
  loadingText: {
    color: theme.muted,
    fontSize: 14,
    fontWeight: "600",
  },

  resultsArea: {
    paddingHorizontal: 16,
    paddingTop: 18,
    gap: 14,
  },
  resultsIntro: {
    gap: 4,
    marginBottom: 2,
  },
  resultsLabel: {
    color: theme.goldSoft,
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  resultsLead: {
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "600",
  },

  // カード
  card: {
    backgroundColor: theme.surface,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: theme.borderGold,
    paddingHorizontal: 18,
    paddingTop: 16,
    paddingBottom: 18,
    gap: 12,
    shadowColor: "#000",
    shadowOpacity: 0.28,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 7 },
    elevation: 4,
  },

  // ランク
  rankRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  rankBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: theme.gold,
    alignItems: "center",
    justifyContent: "center",
  },
  rankBadgeText: {
    color: theme.background,
    fontSize: 12,
    fontWeight: "900",
    lineHeight: 14,
  },
  rankLabel: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
  rankLine: {
    flex: 1,
    height: 1,
    backgroundColor: theme.borderSoft,
  },

  // 神社名・エリア
  cardTitleBlock: {
    gap: 3,
  },
  cardName: {
    color: theme.text,
    fontSize: 19,
    fontWeight: "900",
    letterSpacing: 0.3,
  },
  cardArea: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "600",
    letterSpacing: 0.2,
  },

  // 推薦理由
  cardReason: {
    color: theme.mutedSoft,
    fontSize: 14,
    lineHeight: 24,
    fontWeight: "600",
  },

  // タグ
  tagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
  },
  tagPill: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    backgroundColor: theme.surfaceSoft,
  },
  tagText: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.2,
  },

  // CTA
  ctaRow: {
    flexDirection: "row",
    gap: 8,
    marginTop: 4,
  },
  ctaPrimary: {
    flex: 1,
    height: 50,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.gold,
    shadowColor: theme.gold,
    shadowOpacity: 0.25,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 3 },
  },
  ctaPrimaryText: {
    color: theme.background,
    fontSize: 15,
    fontWeight: "800",
    letterSpacing: 0.3,
  },

  // 入力バー
  inputBar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    paddingHorizontal: 14,
    paddingTop: 10,
    paddingBottom: 18,
    backgroundColor: theme.background,
    borderTopWidth: 1,
    borderTopColor: theme.borderHeader,
  },
  input: {
    flex: 1,
    minHeight: 46,
    maxHeight: 120,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: 16,
    paddingHorizontal: 13,
    paddingVertical: 10,
    color: theme.text,
    fontSize: 15,
    lineHeight: 22,
  },
  sendBtn: {
    width: 50,
    height: 50,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 25,
    backgroundColor: theme.gold,
  },
  sendBtnDisabled: {
    opacity: 0.4,
  },
  sendText: {
    color: theme.background,
    fontSize: 22,
    fontWeight: "900",
  },
});
