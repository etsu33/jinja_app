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
import { appColors as theme, inputAppearance } from "../design/platformTheme";
import { spacing } from "../design/spacing";
import { radius } from "../design/radius";
import { typography } from "../design/typography";

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
              {...inputAppearance}
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
            {errors.username ? <Text accessibilityRole="alert" style={styles.errorText}>{errors.username}</Text> : null}
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>メールアドレス</Text>
            <TextInput
              {...inputAppearance}
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
            {errors.email ? <Text accessibilityRole="alert" style={styles.errorText}>{errors.email}</Text> : null}
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>パスワード</Text>
            <TextInput
              {...inputAppearance}
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
            {errors.password ? <Text accessibilityRole="alert" style={styles.errorText}>{errors.password}</Text> : null}
          </View>

          {errors.form ? <Text accessibilityRole="alert" style={styles.errorText}>{errors.form}</Text> : null}

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
  hint: {
    ...typography.footnote,
    color: theme.muted,
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
