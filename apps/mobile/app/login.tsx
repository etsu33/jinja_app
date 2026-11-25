import * as React from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { post } from "../lib/http";
import Button from "../components/ui/Button";
import { setTokens } from "../lib/authTokens";
import { appColors as theme, inputAppearance, isIndigoIOS } from "../design/platformTheme";
import { spacing } from "../design/spacing";
import { radius } from "../design/radius";
import { typography } from "../design/typography";

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
    <ScrollView style={styles.screen} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" automaticallyAdjustKeyboardInsets={isIndigoIOS}>
      <View style={styles.card}>
        <Text style={styles.eyebrow}>LOGIN</Text>
        <Text style={styles.title}>ログイン</Text>
        <Text style={styles.subtitle}>行動ログや保存情報を記録するためにログインします。</Text>

        <View style={styles.form}>
          <View style={styles.field}>
            <Text style={styles.label}>ユーザー名</Text>
            <TextInput
              {...inputAppearance}
              accessibilityLabel="ユーザー名"
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
              {...inputAppearance}
              accessibilityLabel="パスワード"
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

          {errorMessage ? (
            <Text accessibilityRole="alert" style={styles.errorText}>{errorMessage}</Text>
          ) : null}

          <Button
            title="ログインする"
            variant="primary"
            onPress={onSubmit}
            disabled={!canSubmit}
            loading={submitting}
            accessibilityLabel="ログインする"
          />

          <Pressable
            onPress={() => router.replace("/signup")}
            style={styles.linkButton}
            accessibilityRole="link"
          >
            <Text style={styles.linkButtonText}>アカウントをお持ちでない方は 新規登録はこちら</Text>
          </Pressable>
        </View>
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
    flexGrow: 1,
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
    ...typography.eyebrow,
    color: theme.accent,
  },
  title: {
    ...typography.display,
    color: theme.text,
  },
  subtitle: {
    ...typography.body,
    color: theme.muted,
  },
  form: {
    gap: spacing.mdGap,
    marginTop: spacing.smGap,
  },
  field: {
    gap: spacing.smGap,
  },
  label: {
    ...typography.label,
    color: theme.text,
  },
  input: {
    ...typography.bodyStrong,
    minHeight: 48,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.contentX,
    color: theme.text,
    backgroundColor: theme.background,
  },
  errorText: {
    ...typography.subhead,
    color: theme.error,
  },
  linkButton: {
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  linkButtonText: {
    ...typography.label,
    color: theme.accent,
  },
});
