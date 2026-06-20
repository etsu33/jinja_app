import { radius } from "./radius";
import { spacing } from "./spacing";

export const cardTokens = {
  radius: radius.lg,
  padding: spacing.lg,
  gap: spacing.md,
  minHeight: {
    sm: 120,
    md: 160,
    lg: 220,
  },
} as const;

export type CardSizeKey = keyof typeof cardTokens.minHeight;
