import * as React from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";

import Button from "../../components/ui/Button";
import { cardSizes } from "../design/cardSizes";
import { radius } from "../design/radius";
import { spacing } from "../design/spacing";
import { kamimusubiDark as theme } from "../theme";

const BIRTHDAY_STORAGE_KEY = "sanpai:profile:birthday";

function normalizeBirthday(value: string) {
  return value.trim().replaceAll("/", "-");
}

export default function BirthdayScreen() {
  const router = useRouter();
  const [birthday, setBirthday] = React.useState("");
  const [savedBirthday, setSavedBirthday] = React.useState("");
  const [message, setMessage] = React.useState<string | null>(null);

  React.useEffect(() => {
    let mounted = true;

    AsyncStorage.getItem(BIRTHDAY_STORAGE_KEY)
      .then((value) => {
        if (!mounted || !value) return;
        setBirthday(value);
        setSavedBirthday(value);
      })
      .catch(() => undefined);

    return () => {
      mounted = false;
    };
  }, []);

  const handleSave = async () => {
    const next = normalizeBirthday(birthday);

    if (!next) {
      await AsyncStorage.removeItem(BIRTHDAY_STORAGE_KEY);
      setSavedBirthday("");
      setMessage("誕生日を未設定に戻しました。");
      return;
    }

    await AsyncStorage.setItem(BIRTHDAY_STORAGE_KEY, next);
    setBirthday(next);
    setSavedBirthday(next);
    setMessage("誕生日を保存しました。");
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <Pressable
          onPress={() => (router.canGoBack() ? router.back() : router.replace("/mypage"))}
          style={styles.backButton}
        >
          <Text style={styles.backText}>← マイページへ戻る</Text>
        </Pressable>

        <Text style={styles.eyebrow}>BIRTHDAY</Text>
        <Text style={styles.title}>誕生日</Text>

        <Text style={styles.subtitle}>
          コンシェルジュの条件提案を補助するための情報です。占術結果を断定せず、相談内容を補う材料として扱います。
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.label}>誕生日</Text>

        <TextInput
          value={birthday}
          onChangeText={setBirthday}
          placeholder="例: 1984-05-15"
          placeholderTextColor={theme.mutedDark}
          style={styles.input}
          keyboardType="numbers-and-punctuation"
          autoCapitalize="none"
        />

        <Text style={styles.helpText}>形式は YYYY-MM-DD 推奨です。未入力で保存すると未設定に戻ります。</Text>

        <Button title="保存する" variant="primary" onPress={handleSave} accessibilityLabel="誕生日を保存する" />
      </View>

      <View style={styles.statusCard}>
        <Text style={styles.statusLabel}>現在の登録状態</Text>
        <Text style={styles.statusValue}>{savedBirthday || "未設定"}</Text>
        {message ? <Text style={styles.messageText}>{message}</Text> : null}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
  },
  content: {
    padding: spacing.screenXWide,
    paddingBottom: spacing.bottomSpace,
    gap: spacing.lgGap,
  },
  header: {
    gap: spacing.mdGap,
  },
  backButton: {
    alignSelf: "flex-start",
    marginBottom: spacing.smGap,
  },
  backText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "700",
  },
  eyebrow: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "900",
    letterSpacing: 2,
  },
  title: {
    color: theme.gold,
    fontSize: 26,
    fontWeight: "900",
  },
  subtitle: {
    color: theme.text,
    fontSize: 15,
    lineHeight: 23,
    fontWeight: "600",
  },
  card: {
    backgroundColor: theme.surface,
    borderColor: theme.borderHeader,
    borderRadius: radius.lg,
    borderWidth: cardSizes.borderWidth,
    gap: spacing.mdGap,
    padding: cardSizes.cardPaddingLg,
  },
  label: {
    color: theme.gold,
    fontSize: 14,
    fontWeight: "800",
  },
  input: {
    backgroundColor: theme.surfaceSoft,
    borderColor: theme.border,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    color: theme.text,
    fontSize: 16,
    fontWeight: "700",
    paddingHorizontal: cardSizes.cardPaddingMd,
    paddingVertical: 14,
  },
  helpText: {
    color: theme.muted,
    fontSize: 12,
    lineHeight: 19,
    fontWeight: "600",
  },
  statusCard: {
    backgroundColor: theme.surfaceSoft,
    borderColor: theme.borderGold,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    gap: spacing.smGap,
    padding: cardSizes.cardPaddingMd,
  },
  statusLabel: {
    color: theme.goldSoft,
    fontSize: 12,
    fontWeight: "800",
  },
  statusValue: {
    color: theme.text,
    fontSize: 18,
    fontWeight: "900",
  },
  messageText: {
    color: theme.mutedSoft,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "700",
  },
});
