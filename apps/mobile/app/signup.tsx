import * as React from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import Button from "../components/ui/Button";
import {
  PASSWORD_MIN_LENGTH,
  hasSignupErrors,
  signupAndLogin,
  validateSignupInput,
  type SignupFieldErrors,
} from "../lib/signup";
import { kamimusubiDark as theme } from "../design/theme";
import { spacing } from "../design/spacing";
import { radius } from "../design/radius";

export default function SignupScreen() {
  const router = useRouter();
  const [username, setUsername] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [errors, setErrors] = React.useState<SignupFieldErrors>({});
  const inFlight = React.useRef(false);

  const onSubmit = React.useCallback(async () => {
    if (inFlight.current) return;

    const input = { username, email, password };
    const validationErrors = validateSignupInput(input);
    if (hasSignupErrors(validationErrors)) {
      setErrors(validationErrors);
      return;
    }

    inFlight.current = true;
    setSubmitting(true);
    setErrors({});

    try {
      const result = await signupAndLogin(input);
      if (result.kind === "success") {
        router.replace("/mypage");
        return;
      }
      if (result.kind === "validation") {
        setErrors(result.errors);
      } else {
        setErrors({ form: result.message });
      }
    } finally {
      inFlight.current = false;
      setSubmitting(false);
    }
  }, [email, password, router, username]);

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <View style={styles.card}>
        <Text style={styles.eyebrow}>SIGN UP</Text>
        <Text style={styles.title}>新規登録</Text>
        <Text style={styles.subtitle}>アカウントを作成すると、行動ログや保存情報を記録できます。</Text>

        <View style={styles.form}>
          <View style={styles.field}>
            <Text style={styles.label}>ユーザー名</Text>
            <TextInput
              value={username}
              onChangeText={setUsername}
              editable={!submitting}
              autoCapitalize="none"
              autoCorrect={false}
              textContentType="username"
              autoComplete="username"
              placeholder="ユーザー名"
              placeholderTextColor={theme.muted}
              style={styles.input}
              accessibilityLabel="ユーザー名"
            />
            {errors.username ? <Text style={styles.errorText}>{errors.username}</Text> : null}
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>メールアドレス</Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              editable={!submitting}
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="email-address"
              textContentType="emailAddress"
              autoComplete="email"
              placeholder="example@example.com"
              placeholderTextColor={theme.muted}
              style={styles.input}
              accessibilityLabel="メールアドレス"
            />
            {errors.email ? <Text style={styles.errorText}>{errors.email}</Text> : null}
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>パスワード</Text>
            <TextInput
              value={password}
              onChangeText={setPassword}
              editable={!submitting}
              autoCapitalize="none"
              autoCorrect={false}
              secureTextEntry
              textContentType="newPassword"
              autoComplete="new-password"
              placeholder={`${PASSWORD_MIN_LENGTH}文字以上`}
              placeholderTextColor={theme.muted}
              style={styles.input}
              accessibilityLabel="パスワード"
            />
            <Text style={styles.hint}>{PASSWORD_MIN_LENGTH}文字以上</Text>
            {errors.password ? <Text style={styles.errorText}>{errors.password}</Text> : null}
          </View>

          {errors.form ? <Text style={styles.errorText}>{errors.form}</Text> : null}

          <Button
            title="アカウントを作成する"
            variant="primary"
            onPress={onSubmit}
            disabled={submitting}
            loading={submitting}
            accessibilityLabel="アカウントを作成する"
          />

          <Pressable
            onPress={() => router.replace("/login")}
            style={styles.linkButton}
            accessibilityRole="link"
          >
            <Text style={styles.linkButtonText}>アカウントをお持ちの方は ログインはこちら</Text>
          </Pressable>

          <Pressable
            onPress={() => (router.canGoBack() ? router.back() : router.replace("/mypage"))}
            style={styles.backButton}
          >
            <Text style={styles.backButtonText}>戻る</Text>
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
  hint: {
    color: theme.muted,
    fontSize: 12,
  },
  errorText: {
    color: "#FCA5A5",
    fontSize: 13,
    lineHeight: 19,
  },
  linkButton: {
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  linkButtonText: {
    color: theme.gold,
    fontSize: 14,
    fontWeight: "700",
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
