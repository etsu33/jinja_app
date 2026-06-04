import Link from "next/link";

import type { Shrine } from "@/lib/api/shrines";
import type { ConciergeBreakdown } from "@/lib/api/concierge";
import { getConciergeThreadServer, getConciergeThreadsServer } from "@/lib/api/concierge.server";
import { getBillingStatusServer } from "@/lib/api/billing.server";
import { getShrinePublicServer } from "@/lib/api/shrines.server";
import { fetchPublicGoshuinsForShrineServer } from "@/lib/api/publicGoshuins.server";
import { getShrineFavoriteInitialState } from "@/lib/server/favorites.server";

import { serverLog } from "@/lib/server/logging";
import { gmapsDirUrl } from "@/lib/maps";
import { buildShrineHref } from "@/lib/nav/buildShrineHref";
import { buildShrineClose } from "@/lib/navigation/shrineClose";
import { buildDeepReason } from "@/lib/concierge/buildDeepReason";
import { buildRecommendationReasonViewModel } from "@/lib/concierge/buildRecommendationReasonViewModel";
import { buildShrineDetailModel } from "@/lib/shrine/buildShrineDetailModel";
import type { NarrativeFallback } from "@/lib/concierge/narrative/types";
import {
  pickExplanationPayloadFromThread,
  type PickedExplanationPayload,
} from "@/lib/concierge/pickExplanationPayloadFromThread";
import { pickBreakdownFromThread } from "@/lib/concierge/pickBreakdownFromThread";
import { pickReasonFromThread } from "@/lib/concierge/pickReasonFromThread";

import { pickModeFromThread } from "@/lib/concierge/pickModeFromThread";

import { ShrineDetailToast } from "@/components/shrine/ShrineDetailToast";
import { ShrineDetailViewTracker } from "@/components/shrine/ShrineDetailViewTracker";
import ShrineSaveButton from "@/components/shrine/ShrineSaveButton";
import ShrineDetailShell from "@/components/shrine/ShrineDetailShell";
import ShrineDetailArticle from "@/components/shrine/detail/ShrineDetailArticle";
import ScrollToTopOnMount from "@/components/navigation/ScrollToTopOnMount";

import { getBenefitLabels } from "@/lib/shrine/getBenefitLabels";
import {
  buildNeedPrimaryShortCopy,
  isNeedDisplayTag,
  type NeedDisplayTag,
  type ShrineTone,
} from "@/features/concierge/copy/needDisplayCopy";

import { fetchShrineMeaningPayloadV2Server } from "@/lib/api/shrineMeaning.server";

import { buildPreviousConsultationSummary } from "@/lib/concierge/buildPreviousConsultationSummary";
import { compareState } from "@/lib/concierge/compareState";
import type { StateDelta } from "@/lib/concierge/stateComparison";

function normalizeCtx(v?: string | null): "map" | "concierge" | null {
  return v === "map" || v === "concierge" ? v : null;
}

type Props = {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ ctx?: string; tid?: string }>;
};

type RecommendationReasonDetailInput = NonNullable<
  Parameters<typeof buildShrineDetailModel>[0]["recommendationReasonDetail"]
>;

type RecommendationReasonDetailBuildArgs = {
  shrineName: string;
  shrineBenefitLabels?: string[];
  shrineFeatureLabels?: string[];
  conciergeBreakdown: ConciergeBreakdown | null;
  conciergeReason: string | null;
  conciergeExplanationPayload: PickedExplanationPayload | null;
  conciergeMode: "need" | "compat" | null;
  recommendation: Record<string, any> | null;
};

function resolvePrimaryTagFromConcierge(args: {
  primaryReasonLabel?: string | null;
  fallbackTags?: string[] | null;
}): NeedDisplayTag | null {
  const primaryReasonLabel = (args.primaryReasonLabel ?? "").trim();
  const fallbackTags = Array.isArray(args.fallbackTags) ? args.fallbackTags : [];

  if (isNeedDisplayTag(primaryReasonLabel)) {
    return primaryReasonLabel;
  }

  if (fallbackTags.includes("courage")) return "courage";
  if (fallbackTags.includes("money")) return "money";
  if (fallbackTags.includes("career")) return "career";
  if (fallbackTags.includes("mental")) return "mental";
  if (fallbackTags.includes("rest")) return "rest";
  if (fallbackTags.includes("love")) return "love";
  if (fallbackTags.includes("study")) return "study";

  return null;
}

function resolveShrineToneForNarrativeFallback(shrineName: string): ShrineTone {
  const normalizedName = shrineName.replace(/\s+/g, "").trim();

  if (normalizedName.includes("三峯")) return "strong";
  if (normalizedName.includes("伊勢神宮") || normalizedName.includes("内宮")) return "quiet";
  if (normalizedName.includes("乃木")) return "tight";

  return "neutral";
}


export function buildRecommendationReasonDetailInput(
  args: RecommendationReasonDetailBuildArgs,
): {
  recommendationReasonDetail: RecommendationReasonDetailInput | null;
  conciergeDeepReason: NarrativeFallback | null;
} {
  const primaryReasonLabel = args.conciergeExplanationPayload?.primary_reason?.label ?? null;
  const fallbackTags = args.conciergeBreakdown?.matched_need_tags ?? [];
  const primaryTag = resolvePrimaryTagFromConcierge({
    primaryReasonLabel,
    fallbackTags,
  });
  const rawReason = args.conciergeExplanationPayload?.original_reason?.trim() || args.conciergeReason?.trim() || null;
  const shrineTone = resolveShrineToneForNarrativeFallback(args.shrineName);
  const fallbackShort = buildNeedPrimaryShortCopy({
    primaryTag,
    shrineTone,
    fallbackText: rawReason,
  });

  const reasonVm = buildRecommendationReasonViewModel({
    rec: {
      display_name: args.shrineName,
      name: args.shrineName,
      breakdown: args.conciergeBreakdown ?? null,
      fallback_mode: args.recommendation?.fallback_mode ?? null,
      distance_m: args.recommendation?.distance_m ?? null,
      popular_score: args.recommendation?.popular_score ?? null,
      astro_elements: args.recommendation?.astro_elements ?? null,
      astro_priority: args.recommendation?.astro_priority ?? null,
      reason_facts: args.recommendation?.reason_facts ?? args.recommendation?._reason_facts ?? null,
    },
    index: typeof args.recommendation?.rank === "number" ? Math.max(args.recommendation.rank - 1, 0) : 0,
    mode: args.conciergeMode ?? "need",
    needTags: fallbackTags,
    shrineBenefitLabels: args.shrineBenefitLabels ?? [],
    shrineFeatureLabels: args.shrineFeatureLabels ?? [],
  });

  // conciergeDeepReason is a NarrativeFallback for missing detail fields only.
  // Primary source is recommendationReasonDetail from reasonVm.detail.
  // Use this fallback only when detail values are absent.
  const conciergeDeepReason = buildDeepReason({
    shrineName: args.shrineName,
    primaryTag,
    rawReason,
    fallbackShort,
    shrineTone,
  });

  const recommendationReasonDetail: RecommendationReasonDetailInput = {
    heroMeaningCopy: reasonVm.detail.heroMeaningCopy ?? null,
    consultationSummary: reasonVm.detail.consultationSummary ?? conciergeDeepReason?.interpretation ?? null,
    shrineMeaning: reasonVm.detail.shrineMeaning ?? conciergeDeepReason?.shrineMeaning ?? null,
    actionMeaning: reasonVm.detail.actionMeaning ?? conciergeDeepReason?.action ?? null,
  };
  return {
    recommendationReasonDetail,
    conciergeDeepReason,
  };
}

export default async function Page({ params, searchParams }: Props) {

  const { id } = await params;
  const sp = (await searchParams) ?? {};
  const ctx = normalizeCtx(sp?.ctx ?? null);
  const tid = sp?.tid ?? null;

  const hideActions = false;
  const close = buildShrineClose({ ctx, tid });

  const numericId = Number(id);
  if (!Number.isFinite(numericId) || numericId <= 0) {
    return (
      <main className="mx-auto max-w-md space-y-6 p-4">
        <div className="rounded-xl border bg-white p-4 text-center text-sm">不正な神社IDです。</div>
        <Link href="/map" className="inline-flex items-center text-sm text-emerald-700 hover:underline">
          ← 地図に戻る
        </Link>
      </main>
    );
  }

  const qs = new URLSearchParams();
  if (ctx) qs.set("ctx", ctx);
  if (tid) qs.set("tid", String(tid));
  const query = Object.fromEntries(qs.entries());

  let shrine: Shrine | null;
  try {
    shrine = await getShrinePublicServer(numericId);
  } catch (e) {
    serverLog("error", "GET_SHRINE_FAILED", {
      shrineId: numericId,
      message: e instanceof Error ? e.message : String(e),
    });
    shrine = null;
  }

  if (!shrine) {
    return (
      <ShrineDetailShell
        title="神社の詳細"
        subtitle={null}
        close={close}
        ctx={ctx}
        tid={tid}
        addGoshuinHref={null}
        saveAction={null}
        googleDirHref={null}
        googleDirFallbackText="神社情報が見つからなかったため、経路案内を表示できません。"
        hideActions={hideActions}
      >
        <div className="rounded-2xl border bg-white p-4 text-sm text-slate-700">
          神社の詳細情報が見つかりませんでした。
        </div>
      </ShrineDetailShell>
    );
  }

  const s = shrine;
  const pageTitle = (s.name_jp ?? "").trim() || `神社 #${numericId}`;
  const shrineMeaningPayloadV2 = await fetchShrineMeaningPayloadV2Server(numericId);
  const historyThemeForAnalytics = shrineMeaningPayloadV2?.source?.historyTheme ?? null;

  const latNum = Number(s.latitude ?? NaN);
  const lngNum = Number(s.longitude ?? NaN);
  const hasLocation =
    Number.isFinite(latNum) &&
    Number.isFinite(lngNum) &&
    latNum >= -90 &&
    latNum <= 90 &&
    lngNum >= -180 &&
    lngNum <= 180;

  const googleDirHref = hasLocation ? gmapsDirUrl({ dest: { lat: latNum, lng: lngNum }, mode: "walk" }) : null;
  const nextPath = buildShrineHref(numericId, { query: Object.keys(query).length ? query : undefined });

  const addQ = new URLSearchParams();
  addQ.set("shrine", String(numericId));
  addQ.set("shrine_id", String(numericId));
  addQ.set("from", nextPath);
  if (ctx) addQ.set("ctx", ctx);
  if (tid) addQ.set("tid", String(tid));

  const addGoshuinHref = `/goshuin/new?${addQ.toString()}`;
  const shrineBenefitLabels = getBenefitLabels(s);
  const shrineFeatureLabels: string[] = [];

  const billingStatus = await getBillingStatusServer();
  const isPremiumActive = billingStatus.plan === "premium" && billingStatus.is_active === true;


  const { guestMode, ...initialFavorite } = await getShrineFavoriteInitialState(numericId);

  let publicGoshuins: Awaited<ReturnType<typeof fetchPublicGoshuinsForShrineServer>> = [];
  try {
    publicGoshuins = await fetchPublicGoshuinsForShrineServer(numericId);
  } catch (e) {
    serverLog("warn", "GET_PUBLIC_GOSHUINS_FAILED", {
      shrineId: numericId,
      message: e instanceof Error ? e.message : String(e),
    });
    publicGoshuins = [];
  }

  const signals = {
    publicGoshuinsCount: publicGoshuins.length,
  } satisfies NonNullable<Parameters<typeof buildShrineDetailModel>[0]["signals"]>;

  let conciergeBreakdown: ConciergeBreakdown | null = null;
  let conciergeReason: string | null = null;
  let conciergeExplanationPayload: PickedExplanationPayload | null = null;
  let conciergeMode: "need" | "compat" | null = null;

  let recommendationRankExplanation: {
    version: number;
    summary?: string;
    primary_axis?: string;
    primary_axis_ja?: string;
    primary_label?: string | null;
    primary_label_ja?: string | null;
  } | null = null;

  let recommendationRankComparison: {
    version: number;
    rank?: number;
    is_top?: boolean;
    top_name?: string | null;
    gap_from_top?: number;
    comparison_summary?: string | null;
  } | null = null;

  let stateDelta: StateDelta | null = null;
  
  let selectedRecommendation: Record<string, any> | null = null;
  // actionState will be set after selectedRecommendation is determined

  if (ctx === "concierge" && tid) {
    try {
      const thread = await getConciergeThreadServer(String(tid));
      if (thread) {
        conciergeBreakdown = pickBreakdownFromThread(thread, numericId);
        conciergeReason = pickReasonFromThread(thread, numericId);
        conciergeExplanationPayload = pickExplanationPayloadFromThread(thread, numericId);
        conciergeMode = pickModeFromThread(thread);

        const recommendation = (thread.recommendations ?? []).find((r) => Number(r?.shrine_id ?? r?.id) === numericId);
        selectedRecommendation = recommendation ?? null;

        recommendationRankExplanation = recommendation?.rank_explanation as typeof recommendationRankExplanation;
        recommendationRankComparison = recommendation?.rank_comparison as typeof recommendationRankComparison;

        const threads = await getConciergeThreadsServer();
        const currentThreadId = Number(tid);
        const currentIndex = threads.findIndex((t) => t != null && Number(t.id) === currentThreadId);
        const previousThread = currentIndex >= 0 ? (threads[currentIndex + 1] ?? null) : null;
        const previousThreadId = previousThread?.id ?? null;

        if (previousThreadId != null) {
          const previousThreadDetail = await getConciergeThreadServer(String(previousThreadId));
          const currentSummary = buildPreviousConsultationSummary(thread);
          const previousSummary = buildPreviousConsultationSummary(previousThreadDetail);
          stateDelta = compareState(previousSummary, currentSummary);
          serverLog("info", "SHRINE_DETAIL_PREVIOUS_THREAD_RESOLVED", {
            shrineId: numericId,
            tid,
            previousThreadId,
            hasPreviousThreadDetail: Boolean(previousThreadDetail),
            hasStateDelta: Boolean(stateDelta),
          });
        }
      }
    } catch (e) {
      serverLog("warn", "GET_CONCIERGE_THREAD_FAILED", {
        shrineId: numericId,
        tid,
        message: e instanceof Error ? e.message : String(e),
      });
      conciergeBreakdown = null;
      conciergeReason = null;
      conciergeExplanationPayload = null;
      conciergeMode = null;
      recommendationRankExplanation = null;
      recommendationRankComparison = null;
      stateDelta = null;
    }
  }

  // Set actionState after determining selectedRecommendation
  const actionState = selectedRecommendation?.action_state ?? null;
  console.log("[ACTION_STATE_DEBUG]", {
    shrineId: numericId,
    actionState,
    recommendationId: selectedRecommendation?.id ?? null,
    recommendationShrineId: selectedRecommendation?.shrine_id ?? null,
  });

  

  if (ctx === "concierge" && !tid) {
    conciergeMode = "compat";
    conciergeExplanationPayload = {
      primary_need_tag: null,
      primary_need_label_ja: null,
      primary_reason: {
        type: "element",
        label: "element",
        label_ja: "生年月日との相性",
        evidence: [],
        score: 1,
        is_primary: true,
      },
      secondary_reasons: [],
      original_reason: "生年月日との相性を主軸に候補を整理しています。",
      score: {
        element: 3,
        need: 1,
        total: 0.9,
        total_ranked: 2.4,
      },
    };
  }

  let conciergeDeepReason: NarrativeFallback | null = null;
  let recommendationReasonDetail: Parameters<typeof buildShrineDetailModel>[0]["recommendationReasonDetail"] = null;

  if (ctx === "concierge") {
    // detail を主、NarrativeFallback を従にするため、詳細表示用の輸送元をここに集約する。
    const shrineName = (s.name_jp ?? "").trim() || pageTitle;
    serverLog("info", "SHRINE_LABEL_INPUT", {
      shrineId: numericId,
      shrineName,
      shrineBenefitLabels,
      shrineFeatureLabels,
    });
    const builtReasonDetail = buildRecommendationReasonDetailInput({
      shrineName,
      shrineBenefitLabels,
      shrineFeatureLabels,
      conciergeBreakdown,
      conciergeReason,
      conciergeExplanationPayload,
      conciergeMode,
      recommendation: selectedRecommendation,
    });
    recommendationReasonDetail = builtReasonDetail.recommendationReasonDetail;
    conciergeDeepReason = builtReasonDetail.conciergeDeepReason;
  }

  const model = buildShrineDetailModel({
    shrine: s,
    shrineMeaningPayloadV2,
    publicGoshuins,
    conciergeBreakdown,
    conciergeReason,
    conciergeDeepReason,
    conciergeExplanationPayload,
    conciergeMode,
    recommendationReasonDetail,
    recommendationRankExplanation,
    recommendationRankComparison,
    actionState,
    ctx,
    tid,
    signals,
  });
  return (
    <>
      <ScrollToTopOnMount />
      <ShrineDetailViewTracker shrineId={numericId} ctx={ctx} tid={tid} />
      <ShrineDetailToast shrineId={numericId} />
      <ShrineDetailShell
        title={pageTitle}
        subtitle={null}
        close={close}
        shrineId={numericId}
        ctx={ctx}
        tid={tid}
        historyTheme={historyThemeForAnalytics}
        addGoshuinHref={null}
        googleDirHref={googleDirHref}
        googleDirLabel="Googleマップで経路案内"
        saveAction={null}
        hideActions={hideActions}
      >
        <ShrineDetailArticle
          {...model}
          stateDelta={stateDelta}
          isPremiumActive={isPremiumActive}
          historyTheme={historyThemeForAnalytics}
          addGoshuinHref={addGoshuinHref}
          saveActionNode={
            <ShrineSaveButton
              key={`shrine-save-${numericId}`}
              shrineId={numericId}
              ctx={ctx}
              tid={tid}
              nextPath={nextPath}
              guestMode={guestMode}
              initial={initialFavorite}
            />
          }
        />
      </ShrineDetailShell>
    </>
  );
}
