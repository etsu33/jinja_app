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
import React, { useMemo, useState } from "react";

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
import { track } from "@/lib/analytics/track";

import type { ShrineTag } from "@/lib/shrine/tags/types";
import type { ShrineCardAdapterProps } from "@/components/shrine/buildShrineCardProps";
import type { ShrineDetailSectionModel } from "@/components/shrine/detail/types";

import { resolveAccessLevel } from "@/lib/premium/accessLevel";
import { getVisibilityForCard } from "@/lib/premium/cardVisibility";

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

function PremiumUpgradePrompt() {
  const { isLoggedIn, loading: authLoading } = useAuth();
  const isGuestUser = !authLoading && !isLoggedIn;
  const href = isGuestUser ? buildLoginHref("/billing/upgrade") : "/billing/upgrade";
  const ctaLabel = isGuestUser ? "ログインして意味を深める" : "なぜ今この神社が合っているのかを深掘りする";

  return (
    <section className="rounded-2xl border border-amber-100 bg-amber-50/70 p-4">
      <div className="space-y-2">
        <p className="text-sm font-semibold leading-6 text-amber-950">
          {isGuestUser
            ? "今の状態整理と、この神社を選ぶ意味を深められます。"
            : "今の状態整理と、この神社を選ぶ意味をPremiumで深められます。"}
        </p>
        <p className="text-xs leading-6 text-slate-600">
          相談内容に基づく状態整理、相性、行動の意味づけを表示します。
        </p>
        <Link
          href={href}
          className="inline-flex items-center rounded-xl bg-amber-700 px-3 py-2 text-xs font-semibold text-white hover:bg-amber-800"
          onClick={() =>
            track("shrine_detail_premium_preview_click", {
              source: "shrine_detail",
              valueProp: "shrine_meaning_subscription",
              funnelStep: "shrine_detail_preview",
              isGuestUser,
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

function ShrineComparisonDisclosure(props: {
  recommendationMeta: {
    rankTitle?: string | null;
    rankBody?: string | null;
    rankComparison?: {
      is_top?: boolean;
      gap_from_top?: number;
    } | null;
  };
}) {
  const rankTitle = props.recommendationMeta.rankTitle?.trim() || "上位候補との違い";
  const rankBody = props.recommendationMeta.rankBody?.trim() || null;

  if (!rankBody) return null;

  return (
    <details className="rounded-2xl border border-slate-200 bg-white p-4">
      <summary className="cursor-pointer list-none text-sm font-medium text-slate-700">
        <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm text-slate-700">
          比較を見る
        </span>
      </summary>

      <div className="mt-4 space-y-2">
        <h2 className="text-base font-semibold text-slate-900">{rankTitle}</h2>
        <p className="text-sm leading-7 text-slate-700">{rankBody}</p>
      </div>
    </details>
  );
}

function ShrineDecisionPrompt() {
  return (
    <section className="rounded-2xl border border-emerald-100 bg-emerald-50/70 p-4">
      <div className="space-y-2">
        <p className="text-sm font-semibold leading-6 text-emerald-900">
          今のあなたの状態なら、この神社を基準に判断して問題ありません。
        </p>
        <p className="text-xs leading-6 text-slate-600">
          今は選択肢を広げるより、1つに絞って動く方が判断しやすい状態です。
        </p>
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
  saveActionNode?: React.ReactNode;
}) {
  const hasRecommendationMeta = Boolean(recommendationMeta?.rankTitle && recommendationMeta?.rankBody);
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
  const firstReasonSectionIndex = freeSections.findIndex((section) => section.kind === "reason");

  const contextReasonSections =
    contextReasonVisibility === "hidden"
      ? freeSections.filter((section) => section.kind !== "reason")
      : contextReasonVisibility === "partial"
        ? freeSections.filter((section, index) => section.kind !== "reason" || index === firstReasonSectionIndex)
        : freeSections;
  const hasContextReasonSections = contextReasonSections.length > 0;

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

  return (
    <article className="space-y-4">
      <section className="space-y-5">
        <ShrineDetailHeroHeader
          title={cardProps.title}
          heroMeaningCopy={isPremiumActive ? heroMeaningCopy : "今の状態と相性が良い候補です。"}
          address={cardProps.address ?? null}
        />

        <ShrineDetailHeroCard title={cardProps.title} imageUrl={heroImageUrl} />
      </section>

      {hasContextReasonSections ? <ShrineDetailSections sections={contextReasonSections} /> : null}

      {personalMeaningVisibility === "visible" && hasPremiumSections ? (
        <ShrineDetailSections sections={premiumSections} />
      ) : null}

      {personalMeaningVisibility === "teaser" && hasPremiumSections ? <PremiumUpgradePrompt /> : null}

      {isPremiumActive && hasPremiumSections ? <ShrineDecisionPrompt /> : null}

      {isPremiumActive && hasRecommendationMeta && recommendationMeta ? (
        <section>
          <ShrineComparisonDisclosure recommendationMeta={recommendationMeta} />
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

      {resolvedSaveActionNode ? (
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
