// apps/mobile/components/ui/Button.tsx
import { ActivityIndicator, Pressable, StyleSheet, Text, type ViewStyle } from "react-native";

import { ctaSizes } from "../../app/design/ctaSizes";
import { semanticRadius } from "../../app/design/radius";
import { semanticShadow } from "../../app/design/shadow";
import { kamimusubiDarkSemanticTheme } from "../../app/theme";

type Props = {
  title: string;
  variant?: "primary" | "accent" | "neutral";
  style?: ViewStyle;
  onPress?: () => void;
  disabled?: boolean;
  loading?: boolean;
  accessibilityLabel?: string;
};

export default function Button({
  title,
  variant = "neutral",
  style,
  onPress,
  disabled = false,
  loading = false,
  accessibilityLabel,
}: Props) {
  const isDisabled = disabled || loading;

  const theme = variant === "primary" ? styles.btnPrimary : variant === "accent" ? styles.btnAccent : styles.btnNeutral;

  const textStyle =
    variant === "primary" ? styles.btnPrimaryText : variant === "accent" ? styles.btnAccentText : styles.btnText;

  const indicatorColor =
    variant === "primary"
      ? kamimusubiDarkSemanticTheme["action.primaryText"]
      : variant === "accent"
        ? kamimusubiDarkSemanticTheme["text.inverse"]
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
        theme,
        pressed && !isDisabled ? styles.btnPressed : null,
        isDisabled ? styles.btnDisabled : null,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={indicatorColor} />
      ) : (
        <Text style={[styles.btnTextBase, textStyle]}>{title}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  btn: {
    height: ctaSizes.mediumHeight,
    borderRadius: semanticRadius.control,
    alignItems: "center",
    justifyContent: "center",
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
  btnText: {
    color: kamimusubiDarkSemanticTheme["text.primary"],
  },
  btnPrimaryText: {
    color: kamimusubiDarkSemanticTheme["action.primaryText"],
  },
  btnAccentText: {
    color: kamimusubiDarkSemanticTheme["text.inverse"],
  },
});
