// apps/mobile/components/search/SelectedShrineMapCard.tsx
import * as React from "react";
import { Image, StyleSheet, Text, View } from "react-native";

import { kamimusubiDark as theme } from "../../design/theme";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";
import { spacing } from "../../design/spacing";
import Button from "../ui/Button";
import type { ShrineMapPoint } from "../../lib/shrineMap";

type Props = {
  shrine: ShrineMapPoint;
  onDetail: () => void;
};

export function SelectedShrineMapCard({ shrine, onDetail }: Props) {
  return (
    <View style={styles.card} accessibilityLabel={`選択中の神社: ${shrine.name}`}>
      {shrine.imageUrl ? (
        <Image source={{ uri: shrine.imageUrl }} style={styles.image} />
      ) : (
        <View style={styles.imagePlaceholder}>
          <Text style={styles.imagePlaceholderText}>⛩</Text>
        </View>
      )}

      <View style={styles.body}>
        <Text style={styles.name} numberOfLines={1}>
          {shrine.name}
        </Text>
        {shrine.address ? (
          <Text style={styles.address} numberOfLines={1}>
            {shrine.address}
          </Text>
        ) : null}

        <View style={styles.detailWrap}>
          <Button
            title="詳細を見る"
            variant="primary"
            size="compact"
            onPress={onDetail}
            accessibilityLabel={`${shrine.name}の詳細を見る`}
          />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: theme.surface,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderGold,
    borderRadius: radius.lg,
    padding: cardSizes.cardPaddingMd,
    gap: spacing.mdGap,
  },
  image: {
    width: cardSizes.imageSm,
    height: cardSizes.imageSm,
    borderRadius: radius.xs,
    backgroundColor: theme.surfaceSoft,
  },
  imagePlaceholder: {
    width: cardSizes.imageSm,
    height: cardSizes.imageSm,
    borderRadius: radius.xs,
    backgroundColor: theme.surfaceSoft,
    alignItems: "center",
    justifyContent: "center",
  },
  imagePlaceholderText: {
    fontSize: 26,
  },
  body: {
    flex: 1,
    gap: spacing.tightGap,
  },
  name: {
    color: theme.text,
    fontSize: 15,
    fontWeight: "900",
  },
  address: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  detailWrap: {
    alignSelf: "flex-start",
    marginTop: spacing.tightGap,
  },
});
