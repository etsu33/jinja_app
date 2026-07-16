

import * as React from "react";
import { StyleSheet, Text, View } from "react-native";

import { kamimusubiDark as theme } from "../../app/theme";
import { spacing } from "../../app/design/spacing";
import { cardSizes } from "../../app/design/cardSizes";
import { radius } from "../../app/design/radius";

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
    color: theme.text,
    fontSize: 15,
    fontWeight: "800",
  },
  stateText: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "600",
  },
});
