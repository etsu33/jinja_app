// apps/mobile/components/ui/Button.tsx
import { Pressable, Text, StyleSheet, ViewStyle } from "react-native";
import { kamimusubiDarkSemanticTheme } from "../../app/theme";
import { ctaSizes } from "../../app/design/ctaSizes";
import { semanticRadius } from "../../app/design/radius";
import { semanticShadow } from "../../app/design/shadow";

type Props = {
  title: string;
  variant?: "primary" | "accent" | "neutral";
  style?: ViewStyle;
  onPress?: () => void;
};
export default function Button({ title, variant="neutral", style, onPress }: Props) {
  const theme =
    variant === "primary" ? styles.btnPrimary :
    variant === "accent"  ? styles.btnAccent  : styles.btnNeutral;
  const textStyle =
    variant === "primary" ? styles.btnPrimaryText :
    variant === "accent"  ? styles.btnAccentText  : styles.btnText;
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={[styles.btn, theme, style]}>
      <Text style={[styles.btnTextBase, textStyle]}>{title}</Text>
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
  btnTextBase:{ fontWeight: "600", fontSize: 16 },
  btnText:    { color: kamimusubiDarkSemanticTheme["text.primary"] },
  btnPrimaryText: { color: kamimusubiDarkSemanticTheme["action.primaryText"] },
  btnAccentText:{ color: kamimusubiDarkSemanticTheme["text.inverse"] },
});
