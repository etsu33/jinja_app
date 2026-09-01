type RecommendationMeta = {
  rankTitle?: string | null;
  rankBody?: string | null;
  rankComparison?: {
    is_top?: boolean;
    gap_from_top?: number;
  } | null;
};

type Props = {
  recommendationMeta?: RecommendationMeta | null;
};

/**
 * recommendation_meta — Evidence / supporting-detail (PR-N3b).
 *
 * Explains "なぜこの順位 / 推薦位置なのか" (rank reason / difference from #1).
 * It is supporting detail, not Meaning and not a shrine Fact: rendered in the
 * Evidence layer of Shrine Detail, after the Meaning layers, at a weak
 * hierarchy — borderless, subdued heading (<h3>), tokened text (dark-safe),
 * no amber / gold / premium accent / badge / CTA / card surface.
 *
 * Render condition is intentionally the same as the existing
 * `recommendation_meta` analytics event (`rankTitle && rankBody`) so the
 * tracked exposure always corresponds to visible DOM. `rankBody` is backend
 * text passed through verbatim; `rankTitle` is a fixed label. No ranking /
 * recommendation logic here.
 */
export function RecommendationMetaSection({ recommendationMeta }: Props) {
  const title = recommendationMeta?.rankTitle;
  const body = recommendationMeta?.rankBody;
  const isTop = Boolean(recommendationMeta?.rankComparison?.is_top);
  const gap = recommendationMeta?.rankComparison?.gap_from_top;

  if (!title || !body) return null;

  return (
    <section data-testid="shrine-detail-recommendation-meta">
      <div className="space-y-1">
        <h3 className="text-xs font-semibold tracking-[0.04em] text-[var(--kt-color-text-muted)]">{title}</h3>
        <p className="text-sm leading-6 text-[var(--kt-color-text-secondary)]">{body}</p>

        {!isTop && typeof gap === "number" && gap > 0 && (
          <p className="text-xs text-[var(--kt-color-text-muted)]">1位との差: {gap.toFixed(2)}</p>
        )}
      </div>
    </section>
  );
}
