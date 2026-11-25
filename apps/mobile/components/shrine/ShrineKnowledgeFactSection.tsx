// apps/mobile/components/shrine/ShrineKnowledgeFactSection.tsx
import * as React from "react";
import { StyleSheet, Text, View } from "react-native";

import { appColors as theme } from "../../design/theme";
import { spacing } from "../../design/spacing";
import { cardSizes } from "../../design/cardSizes";
import { radius } from "../../design/radius";
import { ctaSizes } from "../../design/ctaSizes";
import { typography } from "../../design/typography";
import {
  hasVisibleKnowledgeFact,
  isDisputedDisplayState,
  type ShrineFactViewModel,
} from "../../lib/shrineKnowledgeFact";

// docs/knowledge/shrine-knowledge-contract.md「分類案（To-Be）」の定義に基づく固定ラベル。
// apps/web/src/lib/shrine/buildShrineFactSection.tsのHISTORY_TYPE_LABELSと同じ対応表
// （コードは共有せず、文言の意味だけを揃える）。宗教的・歴史的な意味を新たに解釈しない。
const HISTORY_TYPE_LABELS: Record<string, string> = {
  official_origin: "由緒",
  founding: "創始",
  historical_event: "歴史",
  tradition: "伝承",
  regional_context: "地域史",
  editorial_summary: "要約",
};

function resolveHistoryTypeLabel(historyType: string): string {
  return HISTORY_TYPE_LABELS[historyType] ?? historyType;
}

// disputed Factに付与する状態ラベル。文言はここ1箇所でのみ定義する。
// Webの「異なる見解を含む情報」と意味を揃えるが、Webコンポーネントはimportしない。
const FACT_DISPUTED_LABEL = "異なる見解を含む情報";

type ShrineKnowledgeFactSectionProps = {
  factViewModel: ShrineFactViewModel;
};

// Mobile Shrine Detail「祭神・由緒」Section。
//
// 責務: Knowledge Fact Section自体の表示可否・Deity/History描画・displayStateによる
// 状態ラベル表示・Mobile向けlayoutのみ。
// 責務ではないもの: API fetch・toShrine・Evidence判定・Recommendation・Navigation・
// Analytics・Storage・Favorites・Auth（propsはShrineFactViewModelのみを受け取り、
// verification_status文字列はこのcomponent内で一切判定しない）。
export function ShrineKnowledgeFactSection({ factViewModel }: ShrineKnowledgeFactSectionProps) {
  if (!hasVisibleKnowledgeFact(factViewModel)) return null;

  return (
    <View style={styles.factCard}>
      <Text style={styles.sectionTitle}>祭神・由緒</Text>

      {factViewModel.deities.length > 0 ? (
        <View style={styles.factSection}>
          <Text style={styles.factSubLabel}>御祭神</Text>
          <View style={styles.factDeityRow}>
            {factViewModel.deities.map((deity, index) => (
              <View key={`${deity.displayName}:${index}`} style={styles.factDeityPill}>
                <Text style={styles.factDeityText}>{deity.displayName}</Text>
                {isDisputedDisplayState(deity.displayState) ? (
                  <View style={styles.factDisputedBadge}>
                    <Text style={styles.factDisputedBadgeText}>{FACT_DISPUTED_LABEL}</Text>
                  </View>
                ) : null}
              </View>
            ))}
          </View>
        </View>
      ) : null}

      {factViewModel.histories.length > 0 ? (
        <View style={styles.factSection}>
          <Text style={styles.factSubLabel}>由緒・歴史</Text>
          <View style={styles.factHistoryList}>
            {factViewModel.histories.map((history, index) => (
              <View key={`${history.title}:${index}`} style={styles.factHistoryItem}>
                <View style={styles.factHistoryMetaRow}>
                  <Text style={styles.factHistoryTypeLabel}>
                    {resolveHistoryTypeLabel(history.historyType)}
                  </Text>
                  {history.periodText ? (
                    <Text style={styles.factHistoryPeriod}>{history.periodText}</Text>
                  ) : null}
                  {isDisputedDisplayState(history.displayState) ? (
                    <View style={styles.factDisputedBadge}>
                      <Text style={styles.factDisputedBadgeText}>{FACT_DISPUTED_LABEL}</Text>
                    </View>
                  ) : null}
                </View>
                {history.title ? <Text style={styles.factHistoryTitle}>{history.title}</Text> : null}
                {history.content ? (
                  <Text style={styles.factHistoryContent}>{history.content}</Text>
                ) : null}
              </View>
            ))}
          </View>
        </View>
      ) : null}
    </View>
  );
}

export default ShrineKnowledgeFactSection;

const styles = StyleSheet.create({
  factCard: {
    marginHorizontal: spacing.screenX,
    marginTop: spacing.sectionTop,
    backgroundColor: theme.surface,
    borderRadius: radius.xl,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.border,
    padding: cardSizes.cardPaddingLg,
    gap: spacing.mdGap,
  },
  // apps/mobile/app/shrines/[id].tsxのstyles.cardTitleと同一の値（他セクション見出しとの
  // 視覚的整合を保つため）。componentをscreenのstylesから独立させるためここで複製する。
  sectionTitle: {
    ...typography.title,
    color: theme.text,
  },
  factSection: {
    gap: spacing.smGap,
  },
  factSubLabel: {
    ...typography.eyebrow,
    color: theme.accentSoft,
  },
  factDeityRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.inlineGap,
  },
  factDeityPill: {
    flexDirection: "row",
    flexWrap: "wrap",
    alignItems: "center",
    maxWidth: "100%",
    flexShrink: 1,
    gap: spacing.tightGap,
    paddingHorizontal: ctaSizes.pillPaddingX,
    paddingVertical: 5,
    borderRadius: radius.pill,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderSoft,
    backgroundColor: theme.surfaceSoft,
  },
  factDeityText: {
    ...typography.subhead,
    color: theme.text,
    flexShrink: 1,
  },
  factHistoryList: {
    gap: spacing.smGap,
  },
  factHistoryItem: {
    borderRadius: radius.md,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.borderSoft,
    backgroundColor: theme.surfaceSoft,
    padding: cardSizes.cardPaddingMd,
    gap: spacing.tightGap,
  },
  factHistoryMetaRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    alignItems: "center",
    gap: spacing.inlineGap,
  },
  factHistoryTypeLabel: {
    ...typography.eyebrow,
    color: theme.muted,
  },
  factHistoryPeriod: {
    ...typography.footnote,
    color: theme.muted,
  },
  factHistoryTitle: {
    ...typography.title,
    color: theme.text,
  },
  factHistoryContent: {
    ...typography.subhead,
    color: theme.mutedSoft,
  },
  factDisputedBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: radius.pill,
    borderWidth: cardSizes.borderWidth,
    borderColor: theme.border,
    backgroundColor: "transparent",
  },
  factDisputedBadgeText: {
    ...typography.caption,
    color: theme.muted,
  },
});
