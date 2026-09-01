"use client";
/**
 * ShrineDetailArticle
 *
 * UI section responsibility (fixed contract)
 *
 * ① 推薦判断
 * - list.primaryPhrase / list.secondaryPhrase / rank.*
 * - なぜこの神社が候補に入ったのかを表示する
 * - 推薦判断の主理由 / 補助理由 / 1位理由を扱う
 * - 状態整理や行動意味はここに混ぜない
 *
 * ② 状態整理
 * - detail.consultationSummary
 * - 今どういう状態なのかを表示する
 * - 判断が散りやすい理由 / 今の優先順位を扱う
 * - 神社説明や推薦判断はここに混ぜない
 *
 * ③ この神社で受け取る意味
 * - detail.shrineMeaning
 * - 今この神社と今の状態がどう重なるかを表示する
 * - 参拝するときの視点（行動意味）はここに混ぜない
 *
 * ④ 参拝するときの視点
 * - detail.actionMeaning
 * - 参拝時にどう向き合うかを独立したsectionとして表示する
 * - 推薦判断や状態整理、神社情報はここに混ぜない
 *
 * 神社情報（補足）
 * - Shrine API / shrine detail model 側
 * - ご利益 / 象徴 / 相性タグ / 基本情報を補助表示する
 * - 説得の主戦場にしない
 *
 * note:
 * - 詳細画面は「①推薦判断 → ②状態整理 → ③この神社で受け取る意味 → ④参拝するときの視点」の順で理解を進める
 * - heroMeaningCopy は ③ の入口コピーとして扱う
 * - 比較情報は本文ではなく補助導線として扱う
 * - 比較はデフォルト非表示にし、必要な時だけ開く
 * - 比較カードは主導線（①〜④）の下に置く
 */
import Link from "next/link";
import React, { useEffect, useMemo, useState } from "react";

import PublicGoshuinSection, { type PublicGoshuinItem } from "@/components/shrine/detail/PublicGoshuinSection";
import ShrineActionSection from "@/components/shrine/detail/ShrineActionSection";
import ShrineJudgeSection from "@/components/shrine/detail/ShrineJudgeSection";
import ShrineProposalSection from "@/components/shrine/detail/ShrineProposalSection";
import ShrineReasonSection from "@/components/shrine/detail/ShrineReasonSection";
import ShrineSupplementSection from "@/components/shrine/detail/ShrineSupplementSection";
import ShrineFactSection from "@/components/shrine/detail/ShrineFactSection";
import ShrineDetailHeroCard from "@/components/shrine/detail/ShrineDetailHeroCard";
import DetailDisclosureBlock from "@/components/shrine/DetailDisclosureBlock";
import { FAVORITE_LABELS } from "@/lib/ui/labels";
import { useAuth } from "@/lib/auth/AuthProvider";
import { buildLoginHref } from "@/lib/nav/login";


import type { ShrineTag } from "@/lib/shrine/tags/types";
import type { ShrineCardAdapterProps } from "@/components/shrine/buildShrineCardProps";
import type { DetailFactSection, ShrineDetailSectionModel } from "@/components/shrine/detail/types";

import { resolveAccessLevel } from "@/lib/premium/accessLevel";
import { getVisibilityForCard, type CardVisibilityState } from "@/lib/premium/cardVisibility";
import { trackCardEvent } from "@/lib/analytics/cardEvents";
import type { StateDelta } from "@/lib/concierge/stateComparison";
import { toNeedTagLabels } from "@/lib/concierge/needTagLabelMap";

import { addVisit, getVisits, type Visit } from "@/lib/api/visits";

import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import { ShrineReflectionPrompt } from "@/components/shrine/detail/ShrineReflectionPrompt";
import { ShrineDeepDivePrompt } from "@/components/shrine/detail/ShrineDeepDivePrompt";
import {
  recommendationAnalyticsProperties,
  type RecommendationAnalyticsProvenance,
} from "../../../../../../packages/shared/recommendationAnalyticsProvenance";


function ShrineDetailSections({ sections }: { sections: ShrineDetailSectionModel[] }) {
  // PR-G3 (docs/design/premium-meaning-ui-direction.md §6, Direction C): the
  // interpretation layer reads as one editorial narrative -- borderless
  // sections separated by whitespace, not a stack of repeated cards. Shrine
  // facts (ShrineFactSection) keep their card so the fact / interpretation
  // boundary stays visible. No content / analytics / Premium change.
  return (
    <div className="space-y-6">
      {sections.map((section, index) => {
        const key = `${section.kind}:${index}`;

        switch (section.kind) {
          case "reason":
            return <ShrineReasonSection key={key} section={section} variant="plain" />;
          case "proposal":
            return <ShrineProposalSection key={key} section={section} variant="plain" />;
          case "meaning":
            return <ShrineJudgeSection key={key} section={section} variant="plain" />;
          case "action":
            return <ShrineActionSection key={key} section={section} variant="plain" />;
          case "supplement":
            return <ShrineSupplementSection key={key} section={section} variant="plain" />;
          default:
            return null;
        }
      })}
    </div>
  );
}

function buildContextReasonSections(args: {
  sections: ShrineDetailSectionModel[];
  visibility: "hidden" | "partial" | "teaser" | "visible";
}) {
  const { sections, visibility } = args;

  if (visibility === "hidden") {
    return sections.filter((section) => section.kind !== "reason");
  }

  if (visibility === "partial") {
    const firstReasonSectionIndex = sections.findIndex((section) => section.kind === "reason");
    return sections.filter((section, index) => section.kind !== "reason" || index === firstReasonSectionIndex);
  }

  return sections;
}

type ShrineDetailTrackedCardId =
  | "context_reason"
  | "personal_meaning"
  | "saved_record"
  | "consultation_summary"
  | "shrine_meaning"
  | "action_meaning";

function trackShrineDetailCardView(args: {
  cardId: ShrineDetailTrackedCardId;
  accessLevel: "anonymous" | "free" | "premium";
  visibility: CardVisibilityState;
  payloadSource?: "v2" | "fallback";
  shrineId?: number | string;
  historyTheme?: string | null;
  // Result <-> Detail duplicate-exposure join key (with shrineId) -- see
  // docs/audit/recommendation-result-detail-instrumentation-contract.md §7.
  recommendationInstanceId?: string | null;
}) {
  if (args.visibility === "hidden") return;

  trackCardEvent({
    event: args.visibility === "partial" || args.visibility === "teaser" ? "card_partial_view" : "card_view",
    cardId: args.cardId,
    source: "shrine_detail",
    accessLevel: args.accessLevel,
    visibility: args.visibility,
    shrineId: args.shrineId,
    historyTheme: args.historyTheme,
    payloadSource: args.payloadSource,
    recommendationInstanceId: args.recommendationInstanceId ?? null,
  });
}

function collectMeaningBlockCardIds(sections: ShrineDetailSectionModel[]): ShrineDetailTrackedCardId[] {
  const ids = new Set<ShrineDetailTrackedCardId>();

  sections.forEach((section) => {
    if (section.kind !== "meaning") return;

    section.items.forEach((item) => {
      if (item.key === "consultation_summary") ids.add("consultation_summary");
      if (item.key === "shrine_meaning") ids.add("shrine_meaning");
      if (item.key === "action_meaning") ids.add("action_meaning");
    });
  });

  return [...ids];
}

function PremiumUpgradePrompt({
  shrineId,
  ctx,
  tid,
  historyTheme,
}: {
  shrineId?: number | string | null;
  ctx?: string | null;
  tid?: string | number | null;
  historyTheme?: string | null;
}) {
  const { isLoggedIn, loading: authLoading } = useAuth();
  const isGuestUser = !authLoading && !isLoggedIn;
  const href = isGuestUser ? buildLoginHref("/billing/upgrade") : "/billing/upgrade";
  // CTA-A responsibility = Meaning Depth: the deep recommendation reason,
  // personal meaning and action meaning for this shrine. Consultation Summary
  // ("状態整理") is FREE and must not be pitched here; continuity ("前回との
  // 違い") is CTA-B and lives on the state-delta card.
  const ctaLabel = isGuestUser ? "ログインして意味を深掘りする" : "この神社を選ぶ意味を深掘りする";

  return (
    <section className="rounded-[var(--kt-radius-card)] border border-amber-100 bg-amber-50/70 p-4">
      <div className="space-y-2">
        <p className="text-sm font-semibold leading-6 text-amber-950">
          {isGuestUser
            ? "この神社が選ばれた深い理由と、あなたにとっての意味を深められます。"
            : "この神社が選ばれた深い理由と、あなたにとっての意味を、Premiumで深掘りできます。"}
        </p>
        <p className="text-xs leading-6 text-[var(--kt-color-text-secondary)]">相談内容に基づく、選定理由の掘り下げ・相性・行動の意味づけを表示します。</p>
        <Link
          href={href}
          className="inline-flex items-center rounded-[var(--kt-radius-panel)] bg-[var(--kt-color-premium-accent)] px-3 py-2 text-xs font-semibold text-[var(--kt-color-text-inverse)] hover:bg-amber-800"
          onClick={() =>
            trackCardEvent({
              event: "premium_preview_click",
              cardId: "premium_preview",
              source: "shrine_detail",
              accessLevel: isGuestUser ? "anonymous" : "free",
              visibility: "teaser",
              ctaType: "continue_with_premium",
              shrineId: shrineId ?? undefined,
              historyTheme,
              threadId: tid != null ? String(tid) : undefined,
              mode: ctx === "concierge" ? "need" : undefined,
            })
          }
        >
          {ctaLabel}
        </Link>
      </div>
    </section>
  );
}

function ShrineDetailHeroHeader(props: { title: string; heroMeaningCopy?: string | null; address?: string | null }) {
  const resolvedHeroMeaningCopy = props.heroMeaningCopy?.trim() || "今のあなたと静かに重なる神社です。";

  return (
    <section className="rounded-[var(--kt-radius-card)] border bg-[var(--kt-color-surface-default)] p-5 shadow-[var(--kt-shadow-medium)]">
      <div className="space-y-2">
        <h1 className="text-xl font-semibold tracking-tight text-[var(--kt-color-text-primary)]">{props.title}</h1>

        <p className="text-[11px] font-semibold tracking-[0.08em] text-[var(--kt-color-text-muted)]">この神社の意味</p>

        <p className="text-[15px] leading-7 text-[var(--kt-color-text-primary)]">{resolvedHeroMeaningCopy}</p>

        {props.address ? <p className="text-[11px] leading-5 text-[var(--kt-color-text-muted)]">{props.address}</p> : null}
      </div>
    </section>
  );
}


function renderStateDeltaTagSentence(tags: string[] | undefined | null, emptyText: string) {
  if (!Array.isArray(tags) || tags.length === 0) {
    return emptyText;
  }

  if (tags.length === 1) {
    return `「${tags[0]}」が見えています。`;
  }

  return `「${tags.join("」「")}」が見えています。`;
}

type VisitSummary = {
  visitCount: number;
  latestVisitedAt: string | null;
};

function getVisitShrineId(visit: Visit): number | string | null {
  const shrine = visit.shrine as any;
  if (typeof shrine === "number" || typeof shrine === "string") return shrine;
  return shrine?.id ?? shrine?.shrine_id ?? null;
}

function getVisitTime(value: string | null) {
  if (!value) return 0;
  const time = new Date(value).getTime();
  return Number.isNaN(time) ? 0 : time;
}

function buildVisitSummary(visits: Visit[], shrineId: number | string): VisitSummary {
  const currentShrineId = String(shrineId);
  const matchedVisits = visits.filter((visit) => {
    const visitShrineId = getVisitShrineId(visit);
    return visitShrineId != null && String(visitShrineId) === currentShrineId;
  });

  const latestVisitedAt = matchedVisits.reduce<string | null>((latest, visit) => {
    if (!latest) return visit.visited_at;
    return getVisitTime(visit.visited_at) > getVisitTime(latest) ? visit.visited_at : latest;
  }, null);

  return {
    visitCount: matchedVisits.length,
    latestVisitedAt,
  };
}

function ShrineDetailStateDeltaSection({
  stateDelta,
  isPremiumActive,
}: {
  stateDelta?: StateDelta | null;
  isPremiumActive: boolean;
}) {
  if (!stateDelta) return null;

  const changedNeedTags = toNeedTagLabels(stateDelta.changedNeedTags ?? []);
  const continuedNeedTags = toNeedTagLabels(stateDelta.continuedNeedTags ?? []);

  if (!isPremiumActive) {
    return (
      <section className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-premium-border)] bg-amber-50/80 p-4">
        <div className="space-y-2">
          <p className="text-xs font-semibold tracking-[0.08em] text-[var(--kt-color-premium-accent)]">前回との違い</p>
          <p className="text-sm font-semibold leading-6 text-amber-950">Premiumでは、前回からの変化をこの神社選びとあわせて確認できます。</p>
          <p className="text-xs leading-6 text-[var(--kt-color-text-secondary)]">今回強く出たテーマや、変わらず残っているテーマを見返せます。</p>
          <Link href="/billing/upgrade?source=shrine_detail_state_delta&funnelStep=comparison_preview" className="inline-flex rounded-[var(--kt-radius-card)] bg-[var(--kt-color-premium-accent)] px-4 py-2 text-sm font-semibold text-[var(--kt-color-text-inverse)] hover:bg-amber-800">
            前回との違いを見る
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4 shadow-[var(--kt-shadow-medium)]">
      <div className="space-y-4">
        <div>
          <p className="text-xs font-semibold tracking-[0.08em] text-[var(--kt-color-text-muted)]">前回との違い</p>
          <p className="mt-2 text-sm leading-6 text-[var(--kt-color-text-secondary)]">
            {stateDelta.summary ??
              "今回の相談内容から、前回との違いを整理しています。相談を重ねるほど、変化の見え方が安定します。"}
          </p>
        </div>

        {stateDelta.transitionNarrative?.summary ? (
          <div className="rounded-[var(--kt-radius-card)] bg-emerald-50/60 p-3">
            <p className="text-xs font-semibold text-emerald-700">前回から変わったこと</p>
            <p className="mt-1 text-sm font-semibold leading-6 text-[var(--kt-color-text-primary)]">
              {stateDelta.transitionNarrative.title}
            </p>
            <p className="mt-2 text-sm leading-6 text-[var(--kt-color-text-secondary)]">{stateDelta.transitionNarrative.summary}</p>
          </div>
        ) : null}

        {stateDelta.actionReflection ? (
          <div className="rounded-[var(--kt-radius-card)] bg-amber-50/70 p-3">
            <p className="text-xs font-semibold text-[var(--kt-color-premium-accent)]">前回の行動</p>
            <p className="mt-1 text-sm font-semibold leading-6 text-[var(--kt-color-text-primary)]">{stateDelta.actionReflection.title}</p>
            <p className="mt-2 text-sm leading-6 text-[var(--kt-color-text-secondary)]">{stateDelta.actionReflection.summary}</p>
            <p className="mt-2 text-xs font-semibold text-[var(--kt-color-premium-accent)]">{stateDelta.actionReflection.nextActionLabel}</p>
          </div>
        ) : null}

        <DetailDisclosureBlock
          title="テーマの内訳"
          summary="今優先したいこと・変わらず残っていること"
          defaultOpen={false}
        >
          <div className="space-y-3">
            <div className="rounded-[var(--kt-radius-card)] bg-[var(--kt-color-background-subtle)] p-3">
              <p className="text-xs font-semibold text-[var(--kt-color-text-muted)]">今優先したいこと</p>
              <p className="mt-2 text-sm leading-6 text-[var(--kt-color-text-secondary)]">
                {renderStateDeltaTagSentence(
                  changedNeedTags,
                  "今回は新しく強まったテーマを断定するより、今見えている流れを優先して整理しています。",
                )}
              </p>
            </div>

            <div className="rounded-[var(--kt-radius-card)] bg-[var(--kt-color-background-subtle)] p-3">
              <p className="text-xs font-semibold text-[var(--kt-color-text-muted)]">変わらず残っていること</p>
              <p className="mt-2 text-sm leading-6 text-[var(--kt-color-text-secondary)]">
                {renderStateDeltaTagSentence(
                  continuedNeedTags,
                  "今回は前回と同じテーマが中心に続くというより、別の方向に意識が向き始めています。",
                )}
              </p>
            </div>
          </div>
        </DetailDisclosureBlock>
      </div>
    </section>
  );
}



export default function ShrineDetailArticle({
  cardProps,
  heroImageUrl,
  heroMeaningCopy,
  benefitLabels,
  tags: _tags = [],
  addGoshuinHref,
  publicGoshuinsPreview = [],
  publicGoshuinsViewAllHref = "",
  showGoshuinSection = false,
  sections = [],
  freeDisplaySections = [],
  premiumDisplaySections = [],
  isPremiumActive = false,
  recommendationMeta = null,
  stateDelta = null,
  ctx = null,
  tid = null,
  historyTheme = null,
  analyticsProvenance,
  recommendationInstanceId = null,
  meaningPayloadSource = "fallback",
  saveActionNode,
  actionState,
  directionSupportCopy = null,
  factSection = null,
}: {
  cardProps: ShrineCardAdapterProps;
  heroImageUrl?: string | null;
  heroMeaningCopy?: string | null;
  benefitLabels: string[];
  tags?: ShrineTag[];
  publicGoshuinsPreview: PublicGoshuinItem[];
  publicGoshuinsViewAllHref: string;
  addGoshuinHref?: string | null;
  showGoshuinSection?: boolean;
  sections?: ShrineDetailSectionModel[];
  freeDisplaySections?: { section: ShrineDetailSectionModel }[];
  premiumDisplaySections?: { section: ShrineDetailSectionModel }[];
  isPremiumActive?: boolean;
  recommendationMeta?: {
    rankTitle?: string | null;
    rankBody?: string | null;
    rankComparison?: {
      is_top?: boolean;
      gap_from_top?: number;
    } | null;
  } | null;
  stateDelta?: StateDelta | null;
  ctx?: string | null;
  tid?: string | number | null;
  historyTheme?: string | null;
  analyticsProvenance?: RecommendationAnalyticsProvenance;
  recommendationInstanceId?: string | null;
  meaningPayloadSource?: "v2" | "fallback";
  saveActionNode?: React.ReactNode;
  actionState?: "none" | "detail_viewed" | "saved" | "route_opened" | "visited" | "reflected" | null;
  directionSupportCopy?: string | null;
  factSection?: DetailFactSection | null;
}) {

  const hasLayeredSections = freeDisplaySections.length > 0 || premiumDisplaySections.length > 0;
  const freeSections = hasLayeredSections ? freeDisplaySections.map((item) => item.section) : sections;
  const premiumSections = premiumDisplaySections.map((item) => item.section);
  const hasFreeSections = freeSections.length > 0;
  const hasPremiumSections = premiumSections.length > 0;
  const hasSections = hasFreeSections || (isPremiumActive && hasPremiumSections);

  const accessLevel = resolveAccessLevel(
    {
      plan: isPremiumActive ? "premium" : "free",
      is_active: isPremiumActive,
    },
    true,
  );

  const contextReasonVisibility = getVisibilityForCard("context_reason", accessLevel);
  const personalMeaningVisibility = getVisibilityForCard("personal_meaning", accessLevel);
  const savedRecordVisibility: CardVisibilityState = "visible";
  const recommendationMetaVisibility = getVisibilityForCard("recommendation_meta", accessLevel);
  const previousComparisonVisibility: CardVisibilityState = isPremiumActive
    ? getVisibilityForCard("previous_comparison", accessLevel)
    : "teaser";

  const contextReasonSections = buildContextReasonSections({
    sections: freeSections,
    visibility: contextReasonVisibility,
  });
  const hasContextReasonSections = contextReasonSections.length > 0;
  const freeMeaningBlockCardIds = collectMeaningBlockCardIds(contextReasonSections);
  const premiumMeaningBlockCardIds = collectMeaningBlockCardIds(premiumSections);
  const freeMeaningBlockCardIdKey = freeMeaningBlockCardIds.join("|");
  const premiumMeaningBlockCardIdKey = premiumMeaningBlockCardIds.join("|");

  const benefitTagObjs = _tags.filter(
    (t) => t.type === "benefit" && (t.confidence === "high" || t.confidence === "mid"),
  );

  const benefitSummary =
    benefitTagObjs.length > 0
      ? benefitTagObjs
          .map((t) => t.label)
          .filter(Boolean)
          .slice(0, 2)
          .join(" / ")
      : benefitLabels.length > 0
        ? benefitLabels.slice(0, 2).join(" / ")
        : "準備中";

  const [favoriteNoticeState, setFavoriteNoticeState] = useState<"saved" | "removed" | null>(null);
  const [visitSubmitting, setVisitSubmitting] = useState(false);
  const [visitError, setVisitError] = useState(false);
  const visitSubmittingRef = React.useRef(false);
  const [visitSummary, setVisitSummary] = useState<VisitSummary>({ visitCount: 0, latestVisitedAt: null });
  const hasVisitHistory = visitSummary.visitCount > 0;

  const resolvedSaveActionNode = useMemo(() => {
    if (!saveActionNode || !React.isValidElement(saveActionNode)) return saveActionNode;

    return React.cloneElement(saveActionNode as React.ReactElement<any>, {
      onToggleSuccess: (nextFav: boolean) => {
        setFavoriteNoticeState(nextFav ? "saved" : "removed");
      },
    });
  }, [saveActionNode]);

  useEffect(() => {
    if (!cardProps.shrineId) return;

    let cancelled = false;

    (async () => {
      try {
        const visits = await getVisits();
        if (cancelled) return;
        setVisitSummary(buildVisitSummary(visits, cardProps.shrineId));
      } catch {
        if (!cancelled) setVisitSummary({ visitCount: 0, latestVisitedAt: null });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [cardProps.shrineId]);

  useEffect(() => {
    if (hasContextReasonSections) {
      trackShrineDetailCardView({
        cardId: "context_reason",
        accessLevel,
        visibility: contextReasonVisibility,
        shrineId: cardProps.shrineId,
        historyTheme,
        payloadSource: meaningPayloadSource,
        recommendationInstanceId,
      });
    }

    freeMeaningBlockCardIds.forEach((cardId) => {
      trackShrineDetailCardView({
        cardId,
        accessLevel,
        visibility: contextReasonVisibility,
        shrineId: cardProps.shrineId,
        historyTheme,
        payloadSource: meaningPayloadSource,
        recommendationInstanceId,
      });
    });

    if (hasPremiumSections) {
      trackShrineDetailCardView({
        cardId: "personal_meaning",
        accessLevel,
        visibility: personalMeaningVisibility,
        shrineId: cardProps.shrineId,
        historyTheme,
        payloadSource: meaningPayloadSource,
        recommendationInstanceId,
      });
    }

    premiumMeaningBlockCardIds.forEach((cardId) => {
      trackShrineDetailCardView({
        cardId,
        accessLevel,
        visibility: personalMeaningVisibility,
        shrineId: cardProps.shrineId,
        historyTheme,
        payloadSource: meaningPayloadSource,
        recommendationInstanceId,
      });
    });

    if (resolvedSaveActionNode) {
      trackShrineDetailCardView({
        cardId: "saved_record",
        accessLevel,
        visibility: savedRecordVisibility,
        shrineId: cardProps.shrineId,
        historyTheme,
        payloadSource: meaningPayloadSource,
        recommendationInstanceId,
      });
    }

    if (recommendationMeta?.rankTitle && recommendationMeta?.rankBody) {
      trackCardEvent({
        event:
          recommendationMetaVisibility === "partial" || recommendationMetaVisibility === "teaser"
            ? "card_partial_view"
            : "card_view",
        cardId: "recommendation_meta",
        source: "shrine_detail",
        accessLevel,
        visibility: recommendationMetaVisibility,
        shrineId: cardProps.shrineId,
        historyTheme,
        payloadSource: meaningPayloadSource,
      });
    }

    if (stateDelta && previousComparisonVisibility !== "hidden") {
      trackCardEvent({
        event:
          previousComparisonVisibility === "partial" || previousComparisonVisibility === "teaser"
            ? "card_partial_view"
            : "card_view",
        cardId: "previous_comparison",
        source: "shrine_detail",
        accessLevel,
        visibility: previousComparisonVisibility,
        shrineId: cardProps.shrineId,
        historyTheme,
        payloadSource: meaningPayloadSource,
      });
    }
  }, [
    accessLevel,
    cardProps.shrineId,
    contextReasonVisibility,
    freeMeaningBlockCardIdKey,
    freeMeaningBlockCardIds,
    hasContextReasonSections,
    hasPremiumSections,
    meaningPayloadSource,
    personalMeaningVisibility,
    premiumMeaningBlockCardIdKey,
    premiumMeaningBlockCardIds,
    previousComparisonVisibility,
    recommendationInstanceId,
    recommendationMeta?.rankBody,
    recommendationMeta?.rankTitle,
    recommendationMetaVisibility,
    resolvedSaveActionNode,
    savedRecordVisibility,
    stateDelta,
    historyTheme,
  ]);

  // Determine if after-visit copy should be shown
  const showAfterVisitCopy =
    actionState === "visited" || actionState === "reflected";

  // ShrineDetailStateDeltaSection only if actionState is "visited" or "reflected"
  const showStateDeltaSection = showAfterVisitCopy;

  return (
    <article className="space-y-4">
      <section className="space-y-5">
        <ShrineDetailHeroHeader
          title={cardProps.title}
          heroMeaningCopy={isPremiumActive ? heroMeaningCopy : "今のあなたと静かに重なる神社です。"}
          address={cardProps.address ?? null}
        />
        <ShrineDetailHeroCard title={cardProps.title} imageUrl={heroImageUrl} />
        {directionSupportCopy ? (
          <div className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] px-4 py-3">
            <p className="text-xs leading-5 text-[var(--kt-color-text-muted)]">{directionSupportCopy}</p>
          </div>
        ) : null}
        {showStateDeltaSection ? (
          <ShrineDetailStateDeltaSection stateDelta={stateDelta} isPremiumActive={isPremiumActive} />
        ) : null}
        {/* 参拝後文言 (after-visit copy) */}
        {showAfterVisitCopy ? (
          <div className="rounded-[var(--kt-radius-card)] border border-emerald-200 bg-[var(--kt-color-surface-default)] p-3 mt-2">
            <p className="text-sm font-semibold text-emerald-700">参拝お疲れさまでした</p>
            <p className="mt-1 text-xs text-[var(--kt-color-text-secondary)]">
              あなたの参拝が記録されました。次回の相談で前回の行動として振り返ることができます。
            </p>
          </div>
        ) : null}
      </section>

      {/* 神社Fact（祭神・由緒・歴史）。PR-G3: Fact -> Interpretation の順で読ませるため
          Hero直後・解釈レイヤーの前に置く。Interpretation/Recommendation/Actionとは
          独立した表示責務で、Fact は spine としてカード表示を維持する（Fact/Meaning境界）。
          Premium gatingの対象にせず、Knowledge未登録（deities/historiesとも空）ならnullで非表示。 */}
      {factSection ? <ShrineFactSection section={factSection} /> : null}

      {hasContextReasonSections ? <ShrineDetailSections sections={contextReasonSections} /> : null}

      {personalMeaningVisibility === "visible" && hasPremiumSections ? (
        <ShrineDetailSections sections={premiumSections} />
      ) : null}

      {personalMeaningVisibility === "teaser" && hasPremiumSections ? (
        <PremiumUpgradePrompt shrineId={cardProps.shrineId} ctx={ctx} tid={tid} historyTheme={historyTheme} />
      ) : null}

      {/* Premium比較カードは後続PRで再設計する。 */}

      {/* Deep Dive Q&A。readiness/Fact選択/Source選択はすべてBackend Authority
          (POST /api/deep-dive/ask/)。Frontend側でreadinessを先読みして表示可否を
          判断しない(質問してみるまでnot_readyかどうかは分からない扱いにする)ため、
          factSectionの有無に関わらず常に表示する。 */}
      <ShrineDeepDivePrompt shrineId={cardProps.shrineId} />

      {resolvedSaveActionNode ? (
        <section className="pt-4">
          <div className="overflow-hidden rounded-[var(--kt-radius-card)] border border-emerald-200 bg-[var(--kt-color-surface-default)]">
            <div className="space-y-2 p-4">
              {resolvedSaveActionNode}
              <p className="text-xs leading-5 text-[var(--kt-color-text-secondary)]">あとで記録から見返せます</p>
              <Link
                href="/favorites"
                className="inline-flex items-center text-sm font-semibold text-emerald-700 hover:underline"
              >
                保存した神社を見る
              </Link>

              {favoriteNoticeState === "saved" ? (
                <p className="text-xs font-semibold text-[var(--kt-color-saved-text)]">{FAVORITE_LABELS.saved}</p>
              ) : null}

              {favoriteNoticeState === "removed" ? (
                <p className="text-xs font-semibold text-[var(--kt-color-text-secondary)]">{FAVORITE_LABELS.removed}</p>
              ) : null}
            </div>

            <div className="border-t border-[var(--kt-color-border-default)] p-4">
              <div className="space-y-2">
                {hasVisitHistory ? (
                  <div className="rounded-[var(--kt-radius-panel)] border border-emerald-200 bg-emerald-50/70 p-3">
                    <p className="text-sm font-semibold text-emerald-700">参拝を記録しました</p>
                    <p className="mt-1 text-xs text-[var(--kt-color-text-secondary)]">次回の相談で、前回の行動として振り返れます。</p>
                  </div>
                ) : (
                  <p className="text-xs leading-5 text-[var(--kt-color-text-muted)]">参拝後に記録できます</p>
                )}

                {hasVisitHistory ? (
                  <ShrineReflectionPrompt
                    shrineId={cardProps.shrineId}
                    historyTheme={historyTheme}
                    threadId={tid != null ? String(tid) : null}
                    ctx={ctx}
                    accessLevel={accessLevel}
                    analyticsProvenance={analyticsProvenance}
                    recommendationInstanceId={recommendationInstanceId}
                  />
                ) : null}

                {visitError ? (
                  <div className="rounded-[var(--kt-radius-panel)] border border-rose-200 bg-[var(--kt-color-surface-default)] p-3">
                    <p className="text-sm font-semibold text-rose-700">参拝記録に失敗しました</p>
                  </div>
                ) : null}

                {!hasVisitHistory ? (
                  <button
                    type="button"
                    disabled={visitSubmitting}
                    onClick={async () => {
                      if (visitSubmittingRef.current) return;
                      visitSubmittingRef.current = true;
                      setVisitSubmitting(true);
                      setVisitError(false);
                      try {
                        await addVisit(cardProps.shrineId, tid);
                        // PR-C (docs/analytics/compass-analytics-contract.md):
                        // only "compass" is distinguished; concierge/map/direct
                        // keep the existing "shrine_detail" value unchanged.
                        trackSearchEvent("visit_done", {
                          source: ctx === "compass" ? "compass" : "shrine_detail",
                          shrineId: cardProps.shrineId,
                          threadId: tid != null ? String(tid) : undefined,
                          historyTheme: historyTheme ?? undefined,
                          accessLevel,
                          mode: ctx === "concierge" ? "need" : undefined,
                          recommendationInstanceId,
                          ...(analyticsProvenance ? recommendationAnalyticsProperties(analyticsProvenance) : {}),
                        });
                        const now = new Date().toISOString();
                        setVisitSummary((current) => ({
                          visitCount: current.visitCount + 1,
                          latestVisitedAt: now,
                        }));
                      } catch {
                        setVisitError(true);
                      } finally {
                        visitSubmittingRef.current = false;
                        setVisitSubmitting(false);
                      }
                    }}
                    className="w-full rounded-[var(--kt-radius-card)] border border-emerald-200 bg-[var(--kt-color-surface-default)] px-4 py-2 text-sm font-semibold text-emerald-800 hover:bg-emerald-50 disabled:opacity-60"
                  >
                    {visitSubmitting ? "記録中..." : "参拝しました"}
                  </button>
                ) : null}
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {showGoshuinSection ? (
        <section id="goshuins">
          <PublicGoshuinSection
            items={publicGoshuinsPreview}
            addGoshuinHref={addGoshuinHref}
            sendingLabel={undefined}
            limit={3}
            seeAllHref={publicGoshuinsViewAllHref ? publicGoshuinsViewAllHref : null}
            seeAllLabel="すべて見る"
          />
        </section>
      ) : null}

      {!hasSections ? (
        <div className="space-y-2">
          <DetailDisclosureBlock title="ご利益" summary={benefitSummary} defaultOpen={false}>
            {benefitTagObjs.length ? (
              <div className="flex flex-wrap gap-1">
                {benefitTagObjs.map((t) => (
                  <span
                    key={t.id}
                    className="inline-flex items-center rounded-[var(--kt-radius-pill)] bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
                  >
                    {t.label}
                  </span>
                ))}
              </div>
            ) : benefitLabels.length ? (
              <div className="flex flex-wrap gap-1">
                {benefitLabels.map((label) => (
                  <span
                    key={label}
                    className="inline-flex items-center rounded-[var(--kt-radius-pill)] bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
                  >
                    {label}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[var(--kt-color-text-muted)]">ご利益情報は準備中です。</p>
            )}
          </DetailDisclosureBlock>
        </div>
      ) : null}
    </article>
  );
}
