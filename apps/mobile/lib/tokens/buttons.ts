import { radius } from "./radius";
import { spacing } from "./spacing";

export const buttonTokens = {
  radius: radius.full,
  paddingHorizontal: spacing.lg,
  height: {
    sm: 40,
    md: 48,
    lg: 56,
  },
} as const;

export type ButtonSizeKey = keyof typeof buttonTokens.height;
