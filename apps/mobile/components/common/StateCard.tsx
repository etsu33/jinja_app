

import * as React from "react";
import { StyleSheet, Text, View } from "react-native";

import { appColors as theme } from "../../design/platformTheme";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";
import { typography } from "../../design/typography";

type StateCardProps = {
  title: string;
  description: string;
};

export function StateCard({ title, description }: StateCardProps) {
  return (
    <View style={styles.stateCard}>
      <Text style={styles.stateTitle}>{title}</Text>
      <Text style={styles.stateText}>{description}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  stateCard: {
    backgroundColor: theme.surfaceSoft,
    borderColor: theme.borderHeader,
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.smGap,
  },
  stateTitle: {
    ...typography.title,
    color: theme.text,
  },
  stateText: {
    ...typography.subhead,
    color: theme.muted,
  },
});
