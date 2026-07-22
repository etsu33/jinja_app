import * as React from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { post } from "../lib/http";
import Button from "../components/ui/Button";
import { setTokens } from "../lib/authTokens";
import { kamimusubiDark as theme } from "../design/theme";
import { spacing } from "../design/spacing";
import { radius } from "../design/radius";

type JwtCreateResponse = {
  access: string;
  refresh: string;
};

export default function LoginScreen() {
  const router = useRouter();
  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  const canSubmit = username.trim().length > 0 && password.length > 0 && !submitting;

  const onSubmit = React.useCallback(async () => {
    if (!canSubmit) return;

    setSubmitting(true);
    setErrorMessage(null);

    try {
      const data = await post<JwtCreateResponse>("/auth/jwt/create/", {
        username: username.trim(),
        password,
      });

      await setTokens(data.access, data.refresh);
      router.replace("/mypage");
    } catch {
      setErrorMessage("ログインできませんでした。ユーザー名とパスワードを確認してください。");
    } finally {
      setSubmitting(false);
    }
  }, [canSubmit, password, router, username]);

  return (
    <View style={styles.screen}>
      <View style={styles.card}>
        <Text style={styles.eyebrow}>LOGIN</Text>
        <Text style={styles.title}>ログイン</Text>
        <Text style={styles.subtitle}>行動ログや保存情報を記録するためにログインします。</Text>

        <View style={styles.form}>
          <View style={styles.field}>
            <Text style={styles.label}>ユーザー名</Text>
            <TextInput
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
              autoCorrect={false}
              textContentType="username"
              placeholder="morietsu"
              placeholderTextColor={theme.muted}
              style={styles.input}
            />
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>パスワード</Text>
            <TextInput
              value={password}
              onChangeText={setPassword}
              autoCapitalize="none"
              autoCorrect={false}
              secureTextEntry
              textContentType="password"
              placeholder="パスワード"
              placeholderTextColor={theme.muted}
              style={styles.input}
            />
          </View>

          {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}

          <Button
            title="ログインする"
            variant="primary"
            onPress={onSubmit}
            disabled={!canSubmit}
            loading={submitting}
            accessibilityLabel="ログインする"
          />

          <Pressable
            onPress={() => (router.canGoBack() ? router.back() : router.replace("/mypage"))}
            style={styles.backButton}
          >
            <Text style={styles.backButtonText}>戻る</Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
    justifyContent: "center",
    padding: spacing.screenX,
  },
  card: {
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: radius.cardLg,
    backgroundColor: theme.surface,
    padding: spacing.contentX,
    gap: spacing.mdGap,
  },
  eyebrow: {
    color: theme.gold,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.4,
  },
  title: {
    color: theme.text,
    fontSize: 28,
    fontWeight: "800",
  },
  subtitle: {
    color: theme.muted,
    fontSize: 14,
    lineHeight: 21,
  },
  form: {
    gap: spacing.mdGap,
    marginTop: spacing.smGap,
  },
  field: {
    gap: spacing.smGap,
  },
  label: {
    color: theme.text,
    fontSize: 13,
    fontWeight: "700",
  },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.contentX,
    color: theme.text,
    backgroundColor: theme.background,
    fontSize: 16,
  },
  errorText: {
    color: "#FCA5A5",
    fontSize: 13,
    lineHeight: 19,
  },
  backButton: {
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  backButtonText: {
    color: theme.muted,
    fontSize: 14,
    fontWeight: "700",
  },
});
