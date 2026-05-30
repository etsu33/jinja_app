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
 * ③ 行動意味
 * - detail.shrineMeaning
 * - 今この神社をどう置くかを表示する
 * - 行動意味の接続を扱う
 * - 推薦判断や神社情報はここに混ぜない
 *
 * ④ 神社情報
 * - Shrine API / shrine detail model 側
 * - ご利益 / 象徴 / 相性タグ / 基本情報を補助表示する
 * - 説得の主戦場にしない
 *
 * note:
 * - 詳細画面は「①推薦判断 → ②状態整理 → ③行動意味 → ④神社情報」の順で理解を進める
 * - heroMeaningCopy は ③ 行動意味の入口コピーとして扱う
 * - 比較情報は本文ではなく補助導線として扱う
 * - 比較はデフォルト非表示にし、必要な時だけ開く
 * - 比較カードは主導線（①〜④）の下に置く
 */
import Link from "next/link";
import React, { useEffect, useMemo, useState } from "react";

import PublicGoshuinSection, { type PublicGoshuinItem } from "@/components/shrine/detail/PublicGoshuinSection";
import ShrineJudgeSection from "@/components/shrine/detail/ShrineJudgeSection";
import ShrineProposalSection from "@/components/shrine/detail/ShrineProposalSection";
import ShrineReasonSection from "@/components/shrine/detail/ShrineReasonSection";
import ShrineSupplementSection from "@/components/shrine/detail/ShrineSupplementSection";
import ShrineDetailHeroCard from "@/components/shrine/detail/ShrineDetailHeroCard";
import DetailDisclosureBlock from "@/components/shrine/DetailDisclosureBlock";
import { FAVORITE_LABELS } from "@/lib/ui/labels";
import { useAuth } from "@/lib/auth/AuthProvider";
import { buildLoginHref } from "@/lib/nav/login";


import type { ShrineTag } from "@/lib/shrine/tags/types";
import type { ShrineCardAdapterProps } from "@/components/shrine/buildShrineCardProps";
import type { ShrineDetailSectionModel } from "@/components/shrine/detail/types";

import { resolveAccessLevel } from "@/lib/premium/accessLevel";
import { getVisibilityForCard, type CardVisibilityState } from "@/lib/premium/cardVisibility";
import { trackCardEvent } from "@/lib/analytics/cardEvents";
import { RecommendationMetaSection } from "@/components/shrine/detail/RecommendationMetaSection";
import type { StateDelta } from "@/lib/concierge/stateComparison";
import { toNeedTagLabels } from "@/lib/concierge/needTagLabelMap";


function ShrineDetailSections({ sections }: { sections: ShrineDetailSectionModel[] }) {
  return (
    <div className="space-y-4">
      {sections.map((section, index) => {
        const key = `${section.kind}:${index}`;

        switch (section.kind) {
          case "reason":
            return <ShrineReasonSection key={key} section={section} />;
          case "proposal":
            return <ShrineProposalSection key={key} section={section} />;
          case "meaning":
            return <ShrineJudgeSection key={key} section={section} />;
          case "supplement":
            return <ShrineSupplementSection key={key} section={section} />;
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
}) {
  if (args.visibility === "hidden") return;

  trackCardEvent({
    event: args.visibility === "partial" || args.visibility === "teaser" ? "card_partial_view" : "card_view",
    cardId: args.cardId,
    source: "shrine_detail",
    accessLevel: args.accessLevel,
    visibility: args.visibility,
    payloadSource: args.payloadSource,
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
}: {
  shrineId?: number | string | null;
  ctx?: string | null;
  tid?: string | number | null;
}) {
  const { isLoggedIn, loading: authLoading } = useAuth();
  const isGuestUser = !authLoading && !isLoggedIn;
  const href = isGuestUser ? buildLoginHref("/billing/upgrade") : "/billing/upgrade";
  const ctaLabel = isGuestUser ? "ログインして意味を深掘りする" : "この神社を選ぶ意味を深掘りする";

  return (
    <section className="rounded-2xl border border-amber-100 bg-amber-50/70 p-4">
      <div className="space-y-2">
        <p className="text-sm font-semibold leading-6 text-amber-950">
          {isGuestUser
            ? "今の状態整理と、この神社を選ぶ意味を深められます。"
            : "今の状態整理と、この神社を選ぶ意味をPremiumで深掘りできます。"}
        </p>
        <p className="text-xs leading-6 text-slate-600">相談内容に基づく状態整理、相性、行動の意味づけを表示します。</p>
        <Link
          href={href}
          className="inline-flex items-center rounded-xl bg-amber-700 px-3 py-2 text-xs font-semibold text-white hover:bg-amber-800"
          onClick={() =>
            trackCardEvent({
              event: "premium_preview_click",
              cardId: "premium_preview",
              source: "shrine_detail",
              accessLevel: isGuestUser ? "anonymous" : "free",
              visibility: "teaser",
              ctaType: "continue_with_premium",
              shrineId: shrineId ?? undefined,
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
  const resolvedHeroMeaningCopy = props.heroMeaningCopy?.trim() || "今の状態と相性が良い候補です。";

  return (
    <section className="rounded-2xl border bg-white p-5 shadow-sm">
      <div className="space-y-2">
        <h1 className="text-xl font-semibold tracking-tight text-slate-900">{props.title}</h1>

        <p className="text-[11px] font-semibold tracking-[0.08em] text-slate-500">この神社の意味</p>

        <p className="text-[15px] leading-7 text-slate-800">{resolvedHeroMeaningCopy}</p>

        {props.address ? <p className="text-[11px] leading-5 text-slate-400">{props.address}</p> : null}
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
      <section className="rounded-2xl border border-amber-200 bg-amber-50/80 p-4">
        <div className="space-y-2">
          <p className="text-xs font-semibold tracking-[0.08em] text-amber-700">前回との違い</p>
          <p className="text-sm font-semibold leading-6 text-amber-950">Premiumでは、前回からの変化をこの神社選びとあわせて確認できます。</p>
          <p className="text-xs leading-6 text-slate-600">今回強く出たテーマや、変わらず残っているテーマを見返せます。</p>
          <Link href="/billing/upgrade?source=shrine_detail_state_delta&funnelStep=comparison_preview" className="inline-flex rounded-2xl bg-amber-700 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-800">
            前回との違いを見る
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="space-y-4">
        <div>
          <p className="text-xs font-semibold tracking-[0.08em] text-slate-400">前回との違い</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            {stateDelta.summary ?? "今回の相談内容から、前回との違いを整理しています。相談を重ねるほど、変化の見え方が安定します。"}
          </p>
        </div>

        {stateDelta.transitionNarrative?.summary ? (
          <div className="rounded-2xl bg-emerald-50/60 p-3">
            <p className="text-xs font-semibold text-emerald-700">前回から変わったこと</p>
            <p className="mt-1 text-sm font-semibold leading-6 text-slate-800">{stateDelta.transitionNarrative.title}</p>
            <p className="mt-2 text-sm leading-6 text-slate-700">{stateDelta.transitionNarrative.summary}</p>
          </div>
        ) : null}

        <DetailDisclosureBlock title="テーマの内訳" summary="今優先したいこと・変わらず残っていること" defaultOpen={false}>
          <div className="space-y-3">
            <div className="rounded-2xl bg-slate-50 p-3">
              <p className="text-xs font-semibold text-slate-500">今優先したいこと</p>
              <p className="mt-2 text-sm leading-6 text-slate-700">
                {renderStateDeltaTagSentence(
                  changedNeedTags,
                  "今回は新しく強まったテーマを断定するより、今見えている流れを優先して整理しています。",
                )}
              </p>
            </div>

            <div className="rounded-2xl bg-slate-50 p-3">
              <p className="text-xs font-semibold text-slate-500">変わらず残っていること</p>
              <p className="mt-2 text-sm leading-6 text-slate-700">
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
  meaningPayloadSource = "fallback",
  saveActionNode,
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
  meaningPayloadSource?: "v2" | "fallback";
  saveActionNode?: React.ReactNode;
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
  const savedRecordVisibility = getVisibilityForCard("saved_record", accessLevel);
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

  const resolvedSaveActionNode = useMemo(() => {
    if (!saveActionNode || !React.isValidElement(saveActionNode)) return saveActionNode;

    return React.cloneElement(saveActionNode as React.ReactElement<any>, {
      onToggleSuccess: (nextFav: boolean) => {
        setFavoriteNoticeState(nextFav ? "saved" : "removed");
      },
    });
  }, [saveActionNode]);

  useEffect(() => {
    if (hasContextReasonSections) {
      trackShrineDetailCardView({
        cardId: "context_reason",
        accessLevel,
        visibility: contextReasonVisibility,
        payloadSource: meaningPayloadSource,
      });
    }

    freeMeaningBlockCardIds.forEach((cardId) => {
      trackShrineDetailCardView({
        cardId,
        accessLevel,
        visibility: contextReasonVisibility,
        payloadSource: meaningPayloadSource,
      });
    });

    if (hasPremiumSections) {
      trackShrineDetailCardView({
        cardId: "personal_meaning",
        accessLevel,
        visibility: personalMeaningVisibility,
        payloadSource: meaningPayloadSource,
      });
    }

    premiumMeaningBlockCardIds.forEach((cardId) => {
      trackShrineDetailCardView({
        cardId,
        accessLevel,
        visibility: personalMeaningVisibility,
        payloadSource: meaningPayloadSource,
      });
    });

    if (resolvedSaveActionNode) {
      trackShrineDetailCardView({
        cardId: "saved_record",
        accessLevel,
        visibility: savedRecordVisibility,
        payloadSource: meaningPayloadSource,
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
    recommendationMeta?.rankBody,
    recommendationMeta?.rankTitle,
    recommendationMetaVisibility,
    resolvedSaveActionNode,
    savedRecordVisibility,
    stateDelta,
  ]);

  return (
    <article className="space-y-4">
      <section className="space-y-5">
        <ShrineDetailHeroHeader
          title={cardProps.title}
          heroMeaningCopy={isPremiumActive ? heroMeaningCopy : "今の状態と相性が良い候補です。"}
          address={cardProps.address ?? null}
        />
        <ShrineDetailHeroCard title={cardProps.title} imageUrl={heroImageUrl} />
        <ShrineDetailStateDeltaSection stateDelta={stateDelta} isPremiumActive={isPremiumActive} />
        <RecommendationMetaSection recommendationMeta={recommendationMeta} />
      </section>

      {hasContextReasonSections ? <ShrineDetailSections sections={contextReasonSections} /> : null}

      {personalMeaningVisibility === "visible" && hasPremiumSections ? (
        <ShrineDetailSections sections={premiumSections} />
      ) : null}

      {personalMeaningVisibility === "teaser" && hasPremiumSections ? (
        <PremiumUpgradePrompt shrineId={cardProps.shrineId} ctx={ctx} tid={tid} />
      ) : null}

      {/* Premium比較カードは後続PRで再設計する。 */}

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
                    className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
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
                    className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
                  >
                    {label}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">ご利益情報は準備中です。</p>
            )}
          </DetailDisclosureBlock>
        </div>
      ) : null}

      {savedRecordVisibility === "visible" && resolvedSaveActionNode ? (
        <section className="pt-4">
          <div className="rounded-2xl border bg-emerald-50 p-4">
            <div className="mb-3 space-y-1">
              <p className="text-sm font-semibold text-emerald-900">この神社から始める</p>
              <p className="text-xs leading-5 text-slate-600">{FAVORITE_LABELS.lead}</p>
            </div>

            {favoriteNoticeState === "saved" ? (
              <div className="mb-3 rounded-xl border border-emerald-200 bg-white p-3">
                <p className="text-sm font-semibold text-emerald-700">{FAVORITE_LABELS.saved}</p>
                <p className="mt-1 text-xs text-slate-600">{FAVORITE_LABELS.guide}</p>
                <div className="mt-2">
                  <Link
                    href="/mypage?tab=favorites"
                    className="inline-flex items-center text-sm font-semibold text-emerald-700 hover:underline"
                  >
                    {FAVORITE_LABELS.cta}
                  </Link>
                </div>
              </div>
            ) : null}

            {favoriteNoticeState === "removed" ? (
              <div className="mb-3 rounded-xl border border-slate-200 bg-white p-3">
                <p className="text-sm font-semibold text-emerald-700">{FAVORITE_LABELS.removed}</p>
              </div>
            ) : null}

            {resolvedSaveActionNode}
          </div>
        </section>
      ) : null}
    </article>
  );
}
