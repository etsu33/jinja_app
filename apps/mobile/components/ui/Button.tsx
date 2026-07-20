// apps/mobile/components/ui/Button.tsx
import { ActivityIndicator, Pressable, StyleSheet, Text, type ViewStyle } from "react-native";

import { ctaSizes } from "../../app/design/ctaSizes";
import { semanticRadius } from "../../app/design/radius";
import { semanticShadow } from "../../app/design/shadow";
import { kamimusubiDarkSemanticTheme } from "../../app/theme";

type Props = {
  title: string;
  variant?: "primary" | "accent" | "neutral" | "outline" | "success";
  size?: "default" | "compact";
  style?: ViewStyle;
  onPress?: () => void;
  disabled?: boolean;
  loading?: boolean;
  accessibilityLabel?: string;
};

export default function Button({
  title,
  variant = "neutral",
  size = "default",
  style,
  onPress,
  disabled = false,
  loading = false,
  accessibilityLabel,
}: Props) {
  const isDisabled = disabled || loading;

  const theme =
    variant === "primary"
      ? styles.btnPrimary
      : variant === "accent"
        ? styles.btnAccent
        : variant === "outline"
          ? styles.btnOutline
          : variant === "success"
            ? styles.btnSuccess
            : styles.btnNeutral;

  const textStyle =
    variant === "primary"
      ? styles.btnPrimaryText
      : variant === "accent"
        ? styles.btnAccentText
        : variant === "outline"
          ? styles.btnOutlineText
          : variant === "success"
            ? styles.btnSuccessText
            : styles.btnText;

  const indicatorColor =
    variant === "primary"
      ? kamimusubiDarkSemanticTheme["action.primaryText"]
      : variant === "accent"
        ? kamimusubiDarkSemanticTheme["text.inverse"]
        : variant === "outline"
          ? kamimusubiDarkSemanticTheme["premium.accent"]
          : variant === "success"
            ? kamimusubiDarkSemanticTheme["status.successText"]
            : kamimusubiDarkSemanticTheme["text.primary"];

  return (
    <Pressable
      accessibilityLabel={accessibilityLabel ?? title}
      accessibilityRole="button"
      accessibilityState={{
        disabled: isDisabled,
        busy: loading,
      }}
      disabled={isDisabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.btn,
        size === "compact" ? styles.btnCompact : styles.btnDefault,
        theme,
        pressed && !isDisabled ? styles.btnPressed : null,
        isDisabled ? styles.btnDisabled : null,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={indicatorColor} />
      ) : (
        <Text style={[styles.btnTextBase, size === "compact" ? styles.btnTextCompact : null, textStyle]}>{title}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  btn: {
    alignItems: "center",
    justifyContent: "center",
  },
  btnDefault: {
    height: ctaSizes.mediumHeight,
    borderRadius: semanticRadius.control,
  },
  btnCompact: {
    alignSelf: "flex-start",
    minHeight: ctaSizes.smallHeight,
    borderRadius: semanticRadius.pill,
    paddingHorizontal: ctaSizes.pillPaddingX,
    paddingVertical: ctaSizes.pillPaddingY,
  },
  btnPrimary: {
    backgroundColor: kamimusubiDarkSemanticTheme["action.primary"],
    ...semanticShadow.brand,
  },
  btnAccent: {
    backgroundColor: kamimusubiDarkSemanticTheme["premium.accent"],
    ...semanticShadow.brand,
  },
  btnNeutral: {
    backgroundColor: kamimusubiDarkSemanticTheme["surface.default"],
    ...semanticShadow.low,
  },
  btnOutline: {
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: kamimusubiDarkSemanticTheme["premium.border"],
  },
  btnSuccess: {
    backgroundColor: kamimusubiDarkSemanticTheme["status.successSurface"],
    borderWidth: 1,
    borderColor: kamimusubiDarkSemanticTheme["status.successBorder"],
  },
  btnPressed: {
    opacity: 0.85,
  },
  btnDisabled: {
    opacity: 0.5,
  },
  btnTextBase: {
    fontWeight: "600",
    fontSize: 16,
  },
  btnTextCompact: {
    fontWeight: "800",
    fontSize: 13,
  },
  btnText: {
    color: kamimusubiDarkSemanticTheme["text.primary"],
  },
  btnPrimaryText: {
    color: kamimusubiDarkSemanticTheme["action.primaryText"],
  },
  btnAccentText: {
    color: kamimusubiDarkSemanticTheme["text.inverse"],
  },
  btnOutlineText: {
    color: kamimusubiDarkSemanticTheme["premium.accent"],
  },
  btnSuccessText: {
    color: kamimusubiDarkSemanticTheme["status.successText"],
  },
});
