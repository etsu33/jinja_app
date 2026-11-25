import * as React from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { appColors as theme, appSemanticTheme } from "../../design/theme";
import { spacing } from "../../design/spacing";
import { radius } from "../../design/radius";
import Button from "../ui/Button";
import { typography } from "../../design/typography";

type AuthPromptProps = {
  visible: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  closeLabel?: string;
};

export function AuthPrompt({
  visible,
  onClose,
  title = "ログインが必要です",
  description = "保存や参拝記録、ご縁の歩みの閲覧には、ログインが必要です。",
  closeLabel = "あとで",
}: AuthPromptProps) {
  const router = useRouter();

  const handleLogin = () => {
    onClose();
    router.push("/login");
  };

  const handleSignup = () => {
    onClose();
    router.push("/signup");
  };

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <View style={styles.card} onStartShouldSetResponder={() => true}>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.description}>{description}</Text>

          <Button
            title="ログインする"
            variant="primary"
            onPress={handleLogin}
            accessibilityLabel="ログインする"
            style={styles.loginButtonSpacing}
          />

          <Pressable onPress={handleSignup} style={styles.signupButton} accessibilityRole="link">
            <Text style={styles.signupButtonText}>アカウントをお持ちでない方は 新規登録はこちら</Text>
          </Pressable>

          <Pressable onPress={onClose} style={styles.closeButton} accessibilityRole="button">
            <Text style={styles.closeButtonText}>{closeLabel}</Text>
          </Pressable>
        </View>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: appSemanticTheme["overlay.default"],
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.screenX,
  },
  card: {
    width: "100%",
    maxWidth: 360,
    borderWidth: 1,
    borderColor: theme.borderAccent,
    borderRadius: radius.cardLg,
    backgroundColor: theme.surface,
    padding: spacing.contentX,
    gap: spacing.mdGap,
  },
  title: {
    ...typography.subheading,
    color: theme.accent,
  },
  description: {
    ...typography.body,
    color: theme.text,
  },
  signupButton: {
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  signupButtonText: {
    ...typography.label,
    color: theme.accent,
  },
  closeButton: {
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  closeButtonText: {
    ...typography.label,
    color: theme.muted,
  },
  loginButtonSpacing: {
    marginTop: spacing.smGap,
  },
});
