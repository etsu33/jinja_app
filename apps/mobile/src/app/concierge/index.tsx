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
  ActivityIndicator,
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

type Msg = { id: string; role: "user" | "assistant"; content: string };

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
  onMap,
}: {
  card: RecommendationCard;
  rank: number;
  onDetail: () => void;
  onMap: () => void;
}) {
  return (
    <View style={styles.card}>
      {/* ランク + 神社名 */}
      <View style={styles.cardHeader}>
        <Text style={styles.rankBadge}>{rank}</Text>
        <View style={styles.cardTitleBlock}>
          <Text style={styles.cardName}>{card.name}</Text>
          <Text style={styles.cardArea}>{card.area}</Text>
        </View>
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
        <Pressable onPress={onMap} style={styles.ctaSecondary}>
          <Text style={styles.ctaSecondaryText}>地図</Text>
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
  const [submitted, setSubmitted] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState<RecommendationCard[]>([]);
  const [messages, setMessages] = React.useState<Msg[]>([
    {
      id: "sys1",
      role: "assistant",
      content: "今の気持ちや願いを教えてください。あなたに合う神社とのご縁を探します。",
    },
  ]);

  // 初期クエリがあれば自動送信
  React.useEffect(() => {
    if (initialQuery) {
      void submit(initialQuery);
    }
    // 初回のみ
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const submit = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const userMsg: Msg = { id: String(Date.now()), role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setSubmitted(false);
    setResults([]);

    // ダミー遅延（APIに差し替え予定）
    await new Promise((r) => setTimeout(r, 1200));

    const aiMsg: Msg = {
      id: String(Date.now() + 1),
      role: "assistant",
      content: `「${trimmed}」をもとに、あなたに合う神社を3社選びました。`,
    };
    setMessages((prev) => [...prev, aiMsg]);
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

  const handleMap = (_card: RecommendationCard) => {
    router.push("/search");
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
          <Text style={styles.headerTitle}>神社との縁を探す</Text>
        </View>

        {/* チャット */}
        <View style={styles.chatArea}>
          {messages.map((m) => (
            <View
              key={m.id}
              style={[styles.bubble, m.role === "user" ? styles.bubbleUser : styles.bubbleAssistant]}
            >
              <Text
                style={[
                  styles.bubbleText,
                  m.role === "user" ? styles.bubbleTextUser : styles.bubbleTextAssistant,
                ]}
              >
                {m.content}
              </Text>
            </View>
          ))}

          {loading ? (
            <View style={styles.loadingRow}>
              <ActivityIndicator size="small" color={theme.gold} />
              <Text style={styles.loadingText}>ご縁を探しています…</Text>
            </View>
          ) : null}
        </View>

        {/* 結果カード */}
        {submitted && results.length > 0 ? (
          <View style={styles.resultsArea}>
            <Text style={styles.resultsLabel}>推薦結果</Text>
            {results.map((card, i) => (
              <ResultCard
                key={card.id}
                card={card}
                rank={i + 1}
                onDetail={() => handleDetail(card)}
                onMap={() => handleMap(card)}
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
          placeholder="今の気持ちや願いを書いてください"
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
    paddingBottom: 180,
  },

  // ヘッダー
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 16,
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

  // チャット
  chatArea: {
    paddingHorizontal: 20,
    paddingTop: 20,
    gap: 10,
  },
  bubble: {
    maxWidth: "84%",
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  bubbleUser: {
    alignSelf: "flex-end",
    backgroundColor: theme.gold,
  },
  bubbleAssistant: {
    alignSelf: "flex-start",
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
  },
  bubbleText: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: "600",
  },
  bubbleTextUser: {
    color: theme.background,
  },
  bubbleTextAssistant: {
    color: theme.text,
  },
  loadingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 8,
  },
  loadingText: {
    color: theme.muted,
    fontSize: 14,
    fontWeight: "600",
  },

  // 結果
  resultsArea: {
    paddingHorizontal: 16,
    paddingTop: 24,
    gap: 14,
  },
  resultsLabel: {
    color: theme.mutedSoft,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 2,
    textTransform: "uppercase",
    marginBottom: 4,
  },

  // カード
  card: {
    backgroundColor: theme.surface,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: theme.border,
    padding: 18,
    gap: 12,
    shadowColor: "#000",
    shadowOpacity: 0.3,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
    elevation: 4,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
  },
  rankBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: theme.borderGold,
    color: theme.gold,
    fontSize: 13,
    fontWeight: "900",
    textAlign: "center",
    lineHeight: 28,
    overflow: "hidden",
  },
  cardTitleBlock: {
    flex: 1,
    gap: 2,
  },
  cardName: {
    color: theme.text,
    fontSize: 18,
    fontWeight: "900",
    letterSpacing: 0.3,
  },
  cardArea: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "600",
  },
  cardReason: {
    color: theme.mutedSoft,
    fontSize: 14,
    lineHeight: 22,
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
    borderColor: theme.borderGold,
    backgroundColor: "transparent",
  },
  tagText: {
    color: theme.goldSoft,
    fontSize: 12,
    fontWeight: "700",
  },

  // CTA
  ctaRow: {
    flexDirection: "row",
    gap: 8,
    marginTop: 4,
  },
  ctaPrimary: {
    flex: 1,
    height: 44,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.gold,
  },
  ctaPrimaryText: {
    color: theme.background,
    fontSize: 14,
    fontWeight: "800",
  },
  ctaSecondary: {
    width: 64,
    height: 44,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: theme.borderGold,
    backgroundColor: "transparent",
  },
  ctaSecondaryText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "700",
  },

  // 入力バー
  inputBar: {
    width: "100%",
    maxWidth: 430,
    alignSelf: "center",
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 10,
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 18,
    backgroundColor: theme.background,
    borderTopWidth: 1,
    borderColor: theme.borderHeader,
  },
  input: {
    flex: 1,
    minHeight: 50,
    maxHeight: 120,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: theme.text,
    fontSize: 15,
    lineHeight: 22,
  },
  sendBtn: {
    width: 54,
    height: 54,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 27,
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
