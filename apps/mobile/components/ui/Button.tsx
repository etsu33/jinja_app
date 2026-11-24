// apps/mobile/components/ui/Button.tsx
import { ActivityIndicator, Pressable, StyleSheet, Text, type TextStyle, type ViewStyle } from "react-native";

import { ctaSizes } from "../../design/ctaSizes";
import { semanticRadius } from "../../design/radius";
import { semanticShadow } from "../../design/shadow";
import { appSemanticTheme, isIndigoIOS } from "../../design/platformTheme";
import { typography } from "../../design/typography";

type Props = {
  title: string;
  variant?: "primary" | "accent" | "neutral" | "outline" | "success";
  size?: "default" | "compact";
  style?: ViewStyle;
  /** 呼び出し元の背景に合わせる任意の文字スタイル。既定の色は維持する。 */
  textStyle?: TextStyle;
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
  textStyle: textStyleOverride,
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
      ? appSemanticTheme["action.primaryText"]
      : variant === "accent"
        ? appSemanticTheme["text.inverse"]
        : variant === "outline"
          ? appSemanticTheme["premium.accent"]
          : variant === "success"
            ? appSemanticTheme["status.successText"]
            : appSemanticTheme["text.primary"];

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
        isIndigoIOS && size === "default" ? styles.btnIOS : null,
        theme,
        pressed && !isDisabled ? styles.btnPressed : null,
        isDisabled ? styles.btnDisabled : null,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={indicatorColor} />
      ) : (
        <Text style={[styles.btnTextBase, size === "compact" ? styles.btnTextCompact : null, textStyle, textStyleOverride]}>{title}</Text>
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
  btnIOS: {
    height: "auto",
    minHeight: ctaSizes.mediumHeight,
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  btnCompact: {
    alignSelf: "flex-start",
    minHeight: ctaSizes.smallHeight,
    borderRadius: semanticRadius.pill,
    paddingHorizontal: ctaSizes.pillPaddingX,
    paddingVertical: ctaSizes.pillPaddingY,
  },
  btnPrimary: {
    backgroundColor: appSemanticTheme["action.primary"],
    ...semanticShadow.brand,
  },
  btnAccent: {
    backgroundColor: appSemanticTheme["premium.accent"],
    ...semanticShadow.brand,
  },
  btnNeutral: {
    backgroundColor: appSemanticTheme["surface.default"],
    ...semanticShadow.low,
  },
  btnOutline: {
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: appSemanticTheme["premium.border"],
  },
  btnSuccess: {
    backgroundColor: appSemanticTheme["status.successSurface"],
    borderWidth: 1,
    borderColor: appSemanticTheme["status.successBorder"],
  },
  btnPressed: {
    opacity: 0.85,
  },
  btnDisabled: {
    opacity: 0.5,
  },
  btnTextBase: {
    ...typography.button,
  },
  btnTextCompact: {
    ...typography.buttonCompact,
  },
  btnText: {
    color: appSemanticTheme["text.primary"],
  },
  btnPrimaryText: {
    color: appSemanticTheme["action.primaryText"],
  },
  btnAccentText: {
    color: appSemanticTheme["text.inverse"],
  },
  btnOutlineText: {
    color: appSemanticTheme["premium.accent"],
  },
  btnSuccessText: {
    color: appSemanticTheme["status.successText"],
  },
});
