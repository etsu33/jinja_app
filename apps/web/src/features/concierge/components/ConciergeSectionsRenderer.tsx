"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";
import DetailSection from "@/components/shrine/DetailSection";
import PlaceShrineCard from "@/components/shrine/PlaceShrineCard";
import ShrineSaveButton from "@/components/shrine/ShrineSaveButton";
import ConciergeFilterPanel from "@/features/concierge/components/ConciergeFilterPanel";
import ModeBadge from "@/features/concierge/components/ModeBadge";
import { buildRecommendationReasonViewModel } from "@/lib/concierge/buildRecommendationReasonViewModel";
import { buildHeroReasonV4Sections } from "@/features/concierge/buildHeroReasonV4Sections";
import ConciergeTopRecommendationHero from "@/features/concierge/components/ConciergeTopRecommendationHero";
import ShrineCardCompact from "@/components/shrines/ShrineCardCompact";

import { labelNeedDisplayTag } from "@/features/concierge/copy/needDisplayCopy";
import { buildLoginHref } from "@/lib/nav/login";
import { resolveAccessLevel } from "@/lib/premium/accessLevel";
import { getVisibilityForCard } from "@/lib/premium/cardVisibility";
import ConciergeConsultationSummary from "@/features/concierge/components/ConciergeConsultationSummary";
import DirectionReferenceCard from "@/features/concierge/components/DirectionReferenceCard";

import { trackCardEvent, type CardAnalyticsPayload } from "@/lib/analytics/cardEvents";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import { trackWebDirection } from "@/lib/analytics/directionEvents";
import { withDirectionRouteContext } from "@/lib/analytics/directionRouteContext";
import { buildRecommendationReasonDisplay } from "../../../../../../packages/shared/recommendationReasonDisplay";
import {
  buildRecommendationResultSetId,
  recommendationAnalyticsProperties,
} from "../../../../../../packages/shared/recommendationAnalyticsProvenance";

import type {
  ConciergeSectionsPayload,
  ConciergeSection,
  ConciergeFilterState,
  RegisteredShrineItem,
  PlaceShrineItem,
  RendererAction,
} from "@/features/concierge/sections/types";

import { buildConciergeCardRoutes } from "@/lib/concierge/conciergeCardRoutes";

type MetaMode = NonNullable<ConciergeSectionsPayload["meta"]>["mode"];
type AnalyticsContext = Pick<
  CardAnalyticsPayload,
  "mode" | "flow" | "hasBirthdate" | "recommendationCount" | "historyTheme" | "consultationAxis"
>;

// Design Token v1: 実値が完全一致する箇所のみ --kt-* 参照へ置換 (docs/design/design-token.md)
const conciergeSoftCardClass =
  "rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] shadow-[var(--kt-shadow-medium)] p-4";
// border-amber-200 / bg-amber-50 は値としてはPremium Tokenと一致するが、
// 本カードの意味は「Notice(警告・注意喚起)」でありPremiumではないため、
// 意味の異なるTokenを流用しないよう非適用とする(radius/shadowのみ置換)。
const conciergeNoticeCardClass = "rounded-[var(--kt-radius-card)] border border-amber-200 bg-amber-50 shadow-[var(--kt-shadow-medium)] p-4";
const conciergePremiumCardClass =
  "rounded-[var(--kt-radius-card)] border border-[var(--kt-color-premium-border)] bg-amber-50/80 shadow-[var(--kt-shadow-medium)] p-4";

/**
 * Conciergeではfavorite操作を提供しない。
 *
 * 理由:
 * - 本画面は discovery / comparison の導線に特化
 * - 保存操作は shrine詳細に集約する
 * - UI責務の肥大化と状態管理の複雑化を防ぐ
 */

function normalizeConciergeMode(mode: MetaMode | null | undefined): "need" | "compat" {
  if (!mode) return "need";

  if (typeof mode === "string") {
    return mode === "compat" ? "compat" : "need";
  }

  if (typeof mode === "object") {
    if ("kind" in mode && mode.kind === "compat") return "compat";
    if ("mode" in mode && mode.mode === "compat") return "compat";
  }

  return "need";
}

function pickAnalyticsString(...values: unknown[]): string | undefined {
  for (const value of values) {
    if (typeof value !== "string") continue;
    const trimmed = value.trim();
    if (trimmed) return trimmed;
  }
  return undefined;
}

function consultationAxisAnalytics(axis: unknown): Pick<CardAnalyticsPayload, "consultationAxis"> | Record<string, never> {
  const consultationAxis = pickAnalyticsString(axis);
  return consultationAxis ? { consultationAxis } : {};
}

function AstroCard(props: { sunSign?: string; element?: string; reason?: string }) {
  const { sunSign, element, reason } = props;
  return (
    <DetailSection title="占星術による選定">
      <div className={conciergeNoticeCardClass}>
        <div className="text-sm font-semibold text-[var(--kt-color-text-primary)]">
          {sunSign || "不明"} / {element || "不明"}
        </div>
        <div className="mt-2 text-sm leading-7 text-[var(--kt-color-text-secondary)]">{reason || "（理由なし）"}</div>
      </div>
    </DetailSection>
  );
}

function ConciergePremiumEntryCard(props: {
  shrineId?: number | null;
  tid?: string | null;
  isGuestUser?: boolean;
  accessLevel: "anonymous" | "free" | "premium";
  analyticsContext?: AnalyticsContext;
}) {
  const href = props.isGuestUser ? buildLoginHref("/billing/upgrade") : "/billing/upgrade";
  const ctaLabel = props.isGuestUser ? "ログインして変化を見返す" : "変化を見返せるようにする";
  return (
    <section className={conciergePremiumCardClass}>
      <div className="space-y-2">
        <p className="text-sm font-semibold leading-6 text-amber-950">
          {props.isGuestUser
            ? "相談を保存すると、今の状態や選んだ理由をあとから見返せます。"
            : "Premiumでは、前回との違いや状態の変化をあとから見返せます。"}
        </p>
        <p className="text-xs leading-6 text-slate-600">相談内容に基づく状態整理、選んだ理由、行動の意味を記録として残せます。</p>
        <a
          href={href}
          className="inline-flex items-center rounded-[var(--kt-radius-panel)] bg-[var(--kt-color-premium-accent)] px-3 py-2 text-xs font-semibold text-[var(--kt-color-text-inverse)] hover:bg-amber-800"
          onClick={() => {
            trackCardEvent({
              event: "premium_preview_click",
              cardId: "premium_preview",
              source: "concierge_result",
              accessLevel: props.accessLevel,
              visibility: "teaser",
              ctaType: "continue_with_premium",
              ...props.analyticsContext,
              ...consultationAxisAnalytics(props.analyticsContext?.consultationAxis),
              shrineId: props.shrineId ?? undefined,
              threadId: props.tid ?? undefined,
            });
          }}
        >
          {ctaLabel}
        </a>
      </div>
    </section>
  );
}

type Props = {
  payload: ConciergeSectionsPayload;
  onAction?: (action: RendererAction) => void;
  sending?: boolean;
  threadId?: number | null;
  isEntryRoute?: boolean;
  isPremiumActive?: boolean;
  analyticsContext?: AnalyticsContext;
};


function parseExtraTokens(extra: string | undefined | null): string[] {
  return (extra || "")
    .split(/[、,\s]+/)
    .map((x) => x.trim())
    .filter(Boolean);
}

// Closed-card preset token -> Level 2 canonical Visit Preference tag
// (Structured Signal Mapping, see ConciergeFilterPanel.tsx for the main
// mapping table). "ひとり"/"階段少なめ" have no Shrine-side capability
// (Task 13 Shrine Data Capability Check: Hold) and stay natural-language-only.
const CLOSED_PRESET_VISIT_PREFERENCE_TAGS: Readonly<Record<string, readonly string[]>> = {
  静か: ["quiet"],
  駅近: ["nearby"],
};

function visitPreferencesForClosedPresets(presets: readonly string[]): string[] {
  const next = new Set<string>();
  for (const p of presets) {
    for (const tag of CLOSED_PRESET_VISIT_PREFERENCE_TAGS[p] ?? []) next.add(tag);
  }
  return Array.from(next);
}

function buildHistoryThemeDisplay(theme: string | null | undefined): { title: string; body: string } | null {
  const normalized = typeof theme === "string" ? theme.trim() : "";
  if (!normalized) return null;

  const map: Record<string, { title: string; body: string }> = {
    再出発: {
      title: "歴史的には、区切りと再出発を象徴する神社です",
      body: "過去を否定するためではなく、次へ進む前に一度流れを区切る場所として受け取りやすい候補です。",
    },
    静寂: {
      title: "歴史的には、静かに整える時間を象徴する神社です",
      body: "刺激を増やすより、外の情報から少し距離を置いて、自分の状態を見直す場所として受け取りやすい候補です。",
    },
    勝負: {
      title: "歴史的には、決断や覚悟を象徴する神社です",
      body: "結果を保証する場所ではなく、迷いを抱えながらも次に動かす方向を確認する場所として受け取りやすい候補です。",
    },
    縁: {
      title: "歴史的には、人や機会との結びつきを象徴する神社です",
      body: "関係をただ増やすのではなく、今あるつながりやこれから選びたい縁を見直す場所として受け取りやすい候補です。",
    },
    学び: {
      title: "歴史的には、積み重ねと集中を象徴する神社です",
      body: "結果だけを急ぐより、今続ける対象を絞り、努力の向け方を整える場所として受け取りやすい候補です。",
    },
    守り: {
      title: "歴史的には、暮らしの土台を守ることを象徴する神社です",
      body: "不安を消し切るためではなく、今守りたいものや生活の土台を確認する場所として受け取りやすい候補です。",
    },
    復興: {
      title: "歴史的には、回復と立て直しを象徴する神社です",
      body: "一気に元へ戻すのではなく、疲れや停滞を抱えたまま少しずつ整え直す場所として受け取りやすい候補です。",
    },
    浄化: {
      title: "歴史的には、抱えたものを手放すことを象徴する神社です",
      body: "問題を消すためではなく、抱え込みすぎた感情や情報をいったん外へ置く場所として受け取りやすい候補です。",
    },
    導き: {
      title: "歴史的には、進む方向を見直すことを象徴する神社です",
      body: "答えを与える場所ではなく、迷いの中で次に向かう方向を静かに確認する場所として受け取りやすい候補です。",
    },
    巡り: {
      title: "歴史的には、流れや循環を象徴する神社です",
      body: "停滞を責めるのではなく、止まっている流れを小さく巡らせ直す場所として受け取りやすい候補です。",
    },
  };

  return map[normalized] ?? null;
}

function scrollToConciergeInput() {
  if (typeof window === "undefined") return;

  const scroll = () => {
    const target = document.getElementById("concierge-input");
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "center" });
      if (target instanceof HTMLTextAreaElement || target instanceof HTMLInputElement) {
        target.focus({ preventScroll: true });
      }
      return;
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  window.requestAnimationFrame(scroll);
  window.setTimeout(scroll, 120);
}

export default function ConciergeSectionsRenderer({
  payload,
  onAction,
  sending = false,
  threadId = null,
  isEntryRoute = false,
  isPremiumActive: isPremiumActiveProp,
  analyticsContext,
}: Props) {
  const trackedImpressionKeysRef = useRef<Set<string>>(new Set());
  const trackedCardEventKeysRef = useRef<Set<string>>(new Set());
  const [showOtherRecommendations, setShowOtherRecommendations] = useState(false);
  const otherRecommendationsId = useId();

  const { isLoggedIn, loading: authLoading } = useAuth();
  const isGuestUser = !authLoading && !isLoggedIn;

  function resolveFirstResultClick(resultSetId: string) {
    if (typeof window === "undefined") return false;

    const key = `firstClick:${resultSetId}`;

    try {
      if (window.localStorage.getItem(key)) return false;

      window.localStorage.setItem(key, "1");
      return true;
    } catch {
      return false;
    }
  }

  useEffect(() => {
    const onOpen = () => onAction?.({ type: "add_condition" });
    window.addEventListener("concierge:open-filter", onOpen);
    return () => window.removeEventListener("concierge:open-filter", onOpen);
  }, [onAction]);

  const filterState: ConciergeFilterState | null = useMemo(() => {
    const sec = payload.sections.find((s) => s.type === "filter") as any;
    return (sec?.state ?? null) as ConciergeFilterState | null;
  }, [payload]);

  const appliedTokens = parseExtraTokens(filterState?.extraCondition);
  const appliedLabel = appliedTokens.length ? `条件: ${appliedTokens.join(" / ")}` : null;
  const normalizedModeForTracking = normalizeConciergeMode(payload?.meta?.mode);
  const tid = threadId != null ? String(threadId) : null;
  const isPremiumActive =
    typeof isPremiumActiveProp === "boolean"
      ? isPremiumActiveProp
      : Boolean((payload?.meta as any)?.billing?.is_active || (payload?.meta as any)?.isPremiumActive);

  const accessLevel = resolveAccessLevel(
    {
      plan: isPremiumActive ? "premium" : "free",
      is_active: isPremiumActive,
    },
    !authLoading && isLoggedIn,
  );

  const premiumPreviewVisibility = getVisibilityForCard("premium_preview", accessLevel);
  const savePromptVisibility = getVisibilityForCard("save_prompt", accessLevel);
  const consultationSummaryVisibility = getVisibilityForCard("consultation_summary", accessLevel);
  const shrineMeaningVisibility = getVisibilityForCard("shrine_meaning", accessLevel);
  const actionMeaningVisibility = getVisibilityForCard("action_meaning", accessLevel);

  const conciergeCardRoutes = useMemo(
    () =>
      buildConciergeCardRoutes([
        { cardId: "premium_preview", visibility: premiumPreviewVisibility },
        { cardId: "save_prompt", visibility: savePromptVisibility },
        { cardId: "consultation_summary", visibility: consultationSummaryVisibility },
        { cardId: "shrine_meaning", visibility: shrineMeaningVisibility },
        { cardId: "action_meaning", visibility: actionMeaningVisibility },
      ]),
    [
      actionMeaningVisibility,
      consultationSummaryVisibility,
      premiumPreviewVisibility,
      savePromptVisibility,
      shrineMeaningVisibility,
    ],
  );

  const resultImpressions = useMemo(() => {
    if (!payload || !Array.isArray(payload.sections)) return [];

    return payload.sections.flatMap((sec: ConciergeSection) => {
      if (sec.type !== "recommendations") return [];

      const items = ((sec as any).items ?? []).filter(
        (item: RegisteredShrineItem | PlaceShrineItem): item is RegisteredShrineItem => item.kind === "registered",
      );

      return items.map((item: RegisteredShrineItem, index: number) => ({
        shrineId: item.shrineId,
        name: item.title,
        position: index === 0 ? "hero" : "compact",
        rank: index + 1,
        mode: normalizedModeForTracking,
        historyTheme:
          typeof (item as any).history_theme === "string"
            ? (item as any).history_theme
            : typeof (item as any).historyTheme === "string"
              ? (item as any).historyTheme
              : null,
        consultationAxis: pickAnalyticsString(
          (item as any).consultation_axis,
          (item as any).consultationAxis,
          payload.meta?.consultationAxis,
        ),
        analyticsProvenance: item.analyticsProvenance,
      }));
    });
  }, [payload, normalizedModeForTracking]);

  const resultSetId = useMemo(() => {
    return buildRecommendationResultSetId(tid, resultImpressions);
  }, [resultImpressions, tid]);

  useEffect(() => {
    resultImpressions.forEach((item) => {
      const impressionKey = `${resultSetId}:concierge_result_impression:${item.shrineId}:${item.position}:${item.rank}`;
      if (trackedImpressionKeysRef.current.has(impressionKey)) return;

      trackedImpressionKeysRef.current.add(impressionKey);
      trackSearchEvent("concierge_result_impression", {
        source: "concierge_result",
        threadId: tid ?? undefined,
        resultSetId,
        shrineId: item.shrineId,
        position: item.position === "hero" ? "hero_primary" : "compact",
        recommendationRank: item.rank,
        mode: item.mode,
        historyTheme: item.historyTheme ?? analyticsContext?.historyTheme,
        ...consultationAxisAnalytics(item.consultationAxis ?? analyticsContext?.consultationAxis),
        ...(item.analyticsProvenance
          ? recommendationAnalyticsProperties(item.analyticsProvenance)
          : {}),
      });
    });
  }, [analyticsContext?.consultationAxis, analyticsContext?.historyTheme, resultImpressions, resultSetId, tid]);

  useEffect(() => {
    const heroItem = resultImpressions.find((item) => item.position === "hero");
    if (!heroItem) return;

    const routeByCardId = new Map(conciergeCardRoutes.map((route) => [route.cardId, route]));

    const consultationSummaryRoute = routeByCardId.get("consultation_summary");
    if (consultationSummaryRoute) {
      const consultationSummaryEventKey = `${resultSetId}:${consultationSummaryRoute.viewEvent}:consultation_summary`;

      if (!trackedCardEventKeysRef.current.has(consultationSummaryEventKey)) {
        trackedCardEventKeysRef.current.add(consultationSummaryEventKey);
        trackCardEvent({
          event: consultationSummaryRoute.viewEvent,
          cardId: "consultation_summary",
          source: "concierge_result",
          accessLevel,
          visibility: consultationSummaryRoute.visibility,
          mode: heroItem.mode,
          historyTheme: heroItem.historyTheme ?? analyticsContext?.historyTheme,
          ...consultationAxisAnalytics(heroItem.consultationAxis ?? analyticsContext?.consultationAxis),
          threadId: tid ?? undefined,
          resultSetId,
        });
      }
    }

    const shrineMeaningRoute = routeByCardId.get("shrine_meaning");
    if (shrineMeaningRoute) {
      const shrineMeaningEventKey = `${resultSetId}:${shrineMeaningRoute.viewEvent}:shrine_meaning:${heroItem.shrineId}`;

      if (!trackedCardEventKeysRef.current.has(shrineMeaningEventKey)) {
        trackedCardEventKeysRef.current.add(shrineMeaningEventKey);
        trackCardEvent({
          event: shrineMeaningRoute.viewEvent,
          cardId: "shrine_meaning",
          source: "concierge_result",
          accessLevel,
          visibility: shrineMeaningRoute.visibility,
          shrineId: heroItem.shrineId,
          recommendationRank: heroItem.rank,
          mode: heroItem.mode,
          historyTheme: heroItem.historyTheme ?? analyticsContext?.historyTheme,
          ...consultationAxisAnalytics(heroItem.consultationAxis ?? analyticsContext?.consultationAxis),
          threadId: tid ?? undefined,
          resultSetId,
        });
      }
    }

    const actionMeaningRoute = routeByCardId.get("action_meaning");
    if (actionMeaningRoute) {
      const actionMeaningEventKey = `${resultSetId}:${actionMeaningRoute.viewEvent}:action_meaning:${heroItem.shrineId}`;

      if (!trackedCardEventKeysRef.current.has(actionMeaningEventKey)) {
        trackedCardEventKeysRef.current.add(actionMeaningEventKey);
        trackCardEvent({
          event: actionMeaningRoute.viewEvent,
          cardId: "action_meaning",
          source: "concierge_result",
          accessLevel,
          visibility: actionMeaningRoute.visibility,
          shrineId: heroItem.shrineId,
          recommendationRank: heroItem.rank,
          mode: heroItem.mode,
          historyTheme: heroItem.historyTheme ?? analyticsContext?.historyTheme,
          ...consultationAxisAnalytics(heroItem.consultationAxis ?? analyticsContext?.consultationAxis),
          threadId: tid ?? undefined,
          resultSetId,
        });
      }
    }

    if (!isEntryRoute) {
      const savePromptEventKey = `${resultSetId}:save_prompt_view:${accessLevel}`;
      if (!trackedCardEventKeysRef.current.has(savePromptEventKey)) {
        trackedCardEventKeysRef.current.add(savePromptEventKey);
        trackCardEvent({
          event: "save_prompt_view",
          cardId: "save_prompt",
          source: "concierge_result",
          accessLevel,
          visibility: savePromptVisibility,
          ctaType: isGuestUser ? "login_to_save" : "save",
          ...analyticsContext,
          ...consultationAxisAnalytics(analyticsContext?.consultationAxis),
          threadId: tid ?? undefined,
          resultSetId,
        });
      }
    }

    const heroEventKey = `${resultSetId}:card_view:shrine_hero:${heroItem.shrineId}`;
    if (!trackedCardEventKeysRef.current.has(heroEventKey)) {
      trackedCardEventKeysRef.current.add(heroEventKey);
      trackCardEvent({
        event: "card_view",
        cardId: "shrine_hero",
        source: "concierge_result",
        accessLevel,
        visibility: "visible",
        shrineId: heroItem.shrineId,
        recommendationRank: heroItem.rank,
        mode: heroItem.mode,
        historyTheme: heroItem.historyTheme ?? analyticsContext?.historyTheme,
        ...consultationAxisAnalytics(heroItem.consultationAxis ?? analyticsContext?.consultationAxis),
        threadId: tid ?? undefined,
        resultSetId,
      });
    }

    if (showOtherRecommendations) {
      const compactItems = resultImpressions.filter((item) => item.position === "compact");

      if (compactItems.length > 0) {
        const otherShrinesEventKey = `${resultSetId}:card_view:other_shrines`;
        if (!trackedCardEventKeysRef.current.has(otherShrinesEventKey)) {
          trackedCardEventKeysRef.current.add(otherShrinesEventKey);
          trackCardEvent({
            event: "card_view",
            cardId: "other_shrines",
            source: "concierge_result",
            accessLevel,
            visibility: "visible",
            historyTheme: analyticsContext?.historyTheme,
            ...consultationAxisAnalytics(analyticsContext?.consultationAxis),
            threadId: tid ?? undefined,
            resultSetId,
          });
        }

        compactItems.forEach((item) => {
          const compactEventKey = `${resultSetId}:card_view:shrine_compact:${item.shrineId}`;
          if (trackedCardEventKeysRef.current.has(compactEventKey)) return;

          trackedCardEventKeysRef.current.add(compactEventKey);
          trackCardEvent({
            event: "card_view",
            cardId: "shrine_compact",
            source: "concierge_result",
            accessLevel,
            visibility: "visible",
            shrineId: item.shrineId,
            recommendationRank: item.rank,
            mode: item.mode,
            historyTheme: item.historyTheme ?? analyticsContext?.historyTheme,
            ...consultationAxisAnalytics(item.consultationAxis ?? analyticsContext?.consultationAxis),
            threadId: tid ?? undefined,
            resultSetId,
          });
        });
      }
    }

    if (isPremiumActive) return;

    const premiumPreviewEventKey = `${resultSetId}:card_teaser_view:premium_preview:${heroItem.shrineId}`;
    if (trackedCardEventKeysRef.current.has(premiumPreviewEventKey)) return;

    trackedCardEventKeysRef.current.add(premiumPreviewEventKey);
    trackCardEvent({
      event: "card_teaser_view",
      cardId: "premium_preview",
      source: "concierge_result",
      accessLevel,
      visibility: "teaser",
      shrineId: heroItem.shrineId,
      recommendationRank: heroItem.rank,
      mode: heroItem.mode,
      historyTheme: heroItem.historyTheme ?? analyticsContext?.historyTheme,
      ...consultationAxisAnalytics(heroItem.consultationAxis ?? analyticsContext?.consultationAxis),
      threadId: tid ?? undefined,
      resultSetId,
    });
  }, [
    accessLevel,
    analyticsContext,
    conciergeCardRoutes,
    isGuestUser,
    isPremiumActive,
    isEntryRoute,
    resultImpressions,
    resultSetId,
    savePromptVisibility,
    showOtherRecommendations,
    tid,
  ]);

  if (!payload || !Array.isArray(payload.sections) || payload.sections.length === 0) return null;

  return (
    <div className="mx-auto w-full max-w-md min-w-0 space-y-4 pb-0 lg:max-w-2xl">
      {payload.sections.map((sec: ConciergeSection, i: number) => {
        switch (sec.type) {
          case "guide":
            return null;

          case "filter": {
            const state: ConciergeFilterState = (sec as any).state;
            const title = (sec as any).title ?? "条件を追加して絞る";

            const canApplyCompatFilter =
              !!state.birthdate?.trim() || (state.selectedTagIds?.length ?? 0) > 0 || !!state.extraCondition?.trim();

            // 閉じ状態（プリセット選択 + 即絞り）
            if (!state.isOpen) {
              const presets = ["静か", "駅近", "ひとり", "階段少なめ"] as const;

              const parts = parseExtraTokens(state.extraCondition);
              const set = new Set(parts);

              const togglePreset = (p: string) => {
                const next = new Set(parts);
                const turningOn = !next.has(p);
                if (next.has(p)) next.delete(p);
                else next.add(p);
                onAction?.({ type: "filter_set_extra", extraCondition: Array.from(next).join(" ") });

                // Structured Visit Preference is union/append-only here (like
                // mergeExtra() in ConciergeFilterPanel.tsx) -- toggling a
                // preset off never removes a tag, since it may also have
                // been set via the open ConciergeFilterPanel.
                if (turningOn) {
                  const addedTags = visitPreferencesForClosedPresets([p]);
                  if (addedTags.length) {
                    const merged = new Set([...(state.visitPreferences ?? []), ...addedTags]);
                    onAction?.({
                      type: "filter_set_visit_preferences",
                      visitPreferences: Array.from(merged),
                    });
                  }
                }
              };

              const selectedPresets = presets.filter((p) => set.has(p));

              return (
                <div key={`filter-${i}-closed`}>
                  <DetailSection title="補助条件を添える">
                    <p className="mb-2 text-xs text-[var(--kt-color-text-muted)]">必要なものだけ選んでください</p>

                    <div className="mb-3 flex flex-wrap gap-2">
                      {presets.map((p) => {
                        const active = set.has(p);
                        return (
                          <button
                            key={p}
                            type="button"
                            className={[
                              "rounded-full border px-3 py-1 text-xs font-semibold transition",
                              active
                                ? "bg-[var(--kt-color-action-primary)] text-[var(--kt-color-action-primary-text)] border-[var(--kt-color-action-primary)]"
                                : "bg-[var(--kt-color-surface-default)] text-[var(--kt-color-text-secondary)] hover:bg-[var(--kt-color-background-subtle)]",
                            ].join(" ")}
                            onClick={() => togglePreset(p)}
                          >
                            {p}
                          </button>
                        );
                      })}
                    </div>

                    {selectedPresets.length > 0 && (
                      <div className={`mb-3 ${conciergeSoftCardClass} text-xs leading-6 text-slate-600`}>
                        追加済み: {selectedPresets.join(" / ")}
                      </div>
                    )}

                    {!isEntryRoute ? (
                      <button
                        type="button"
                        className="mt-2 w-full rounded-[var(--kt-radius-panel)] border px-4 py-3 text-sm font-semibold"
                        onClick={() => {
                          onAction?.({ type: "back_to_entry" });
                          scrollToConciergeInput();
                        }}
                        disabled={sending}
                      >
                        入口に戻る
                      </button>
                    ) : null}

                    <button
                      type="button"
                      className="w-full rounded-[var(--kt-radius-panel)] bg-[var(--kt-color-action-primary)] px-4 py-3 text-sm font-semibold text-[var(--kt-color-action-primary-text)] disabled:opacity-60"
                      disabled={!canApplyCompatFilter || sending}
                      onClick={() => {
                        onAction?.({ type: "filter_apply" });
                      }}
                    >
                      {sending ? "絞り込み中…" : "この内容で反映する"}
                    </button>

                    <button
                      type="button"
                      className="mt-2 w-full rounded-[var(--kt-radius-panel)] border px-4 py-3 text-sm font-semibold"
                      onClick={() => onAction?.({ type: "add_condition" })}
                    >
                      もう少し詳しく添える
                    </button>
                  </DetailSection>
                </div>
              );
            }

            // ConciergeFilterPanel already renders its own title + close
            // control as a self-contained bordered section (see
            // ConciergeFilterPanel.tsx). Wrapping it in DetailSection here
            // duplicated the same title text twice and added a second
            // nested border/padding layer -- Concierge Entry Responsive /
            // Density Polish Task 6 removed that redundancy; no signal or
            // behavior change.
            return (
              <div key={`filter-${i}-open`}>
                <ConciergeFilterPanel
                  isOpen
                  title={title}
                  onClose={() => onAction?.({ type: "filter_close" })}
                  onApply={() => {
                    onAction?.({ type: "filter_apply" });
                  }}
                  canApply={canApplyCompatFilter}
                  birthdate={state.birthdate}
                  onBirthdateChange={(v: string) => onAction?.({ type: "filter_set_birthdate", birthdate: v })}
                  element4={state.element4}
                  goriyakuTags={state.goriyakuTags}
                  suggestedTags={state.suggestedTags}
                  selectedTagIds={state.selectedTagIds}
                  onToggleTag={(tagId: number) => onAction?.({ type: "filter_toggle_tag", tagId })}
                  tagsLoading={state.tagsLoading}
                  tagsError={state.tagsError}
                  extraCondition={state.extraCondition}
                  onExtraConditionChange={(v: string) =>
                    onAction?.({ type: "filter_set_extra", extraCondition: v })
                  }
                  visitPreferences={state.visitPreferences}
                  onVisitPreferencesChange={(tags: string[]) =>
                    onAction?.({ type: "filter_set_visit_preferences", visitPreferences: tags })
                  }
                />
              </div>
            );
          }

          case "recommendations": {
            const items = (sec as any).items ?? [];

            const rs = payload?.meta?.resultState ?? null;
            const isFallback = rs?.fallback_mode === "nearby_unfiltered";
            const hasDummy = items.some((x: any) => x?.isDummy === true);

            const bannerText =
              (typeof rs?.fallback_reason_ja === "string" && rs.fallback_reason_ja) ||
              (typeof rs?.ui_disclaimer_ja === "string" && rs.ui_disclaimer_ja) ||
              (hasDummy ? "条件に合う神社が少ないため、まずは向かいやすい神社から表示しています。" : null);

            const normalizedMode = normalizeConciergeMode(payload?.meta?.mode);

            const registeredItems = items.filter(
              (x: RegisteredShrineItem | PlaceShrineItem): x is RegisteredShrineItem => x.kind === "registered",
            );

            const placeItems = items.filter(
              (x: RegisteredShrineItem | PlaceShrineItem): x is PlaceShrineItem => x.kind === "place",
            );

            const heroItem = registeredItems[0] ?? null;
            const otherRegisteredItems = registeredItems.slice(1);

            return (
              <DetailSection key={`recs-${i}`} title={(sec as any).title ?? ""}>
                <div className="mb-2 flex items-center justify-end">
                  <ModeBadge mode={payload?.meta?.mode} />
                </div>

                {typeof payload?.meta?.remaining === "number" && payload.meta.remaining > 0 && (
                  <div className="mb-2 text-xs leading-6 text-[var(--kt-color-text-muted)]">
                    あと {payload.meta.remaining}回までは無料で試せます
                  </div>
                )}

                {bannerText && (
                  <div className={`mb-3 ${conciergeNoticeCardClass} text-sm leading-6 text-amber-900`}>
                    {bannerText}
                  </div>
                )}

                {(isFallback || hasDummy) && (
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      className="rounded-[var(--kt-radius-panel)] border px-4 py-3 text-sm font-semibold"
                      onClick={() => onAction?.({ type: "open_map" })}
                    >
                      近くの神社を静かに見る
                    </button>
                    <button
                      type="button"
                      /* bg-neutral-900: Dark Surface Contract Group A候補だが、
                         --kt-color-surface-emphasis(slate-800/900)とcomputed colorが
                         一致しないため今回は適用しない(Blocked by Contract)。
                         詳細は docs/audit/design-token-stage3-dark-surface-decision.md */
                      className="rounded-[var(--kt-radius-panel)] bg-neutral-900 px-4 py-3 text-sm font-semibold text-white"
                      onClick={() => onAction?.({ type: "filter_clear" })}
                    >
                      条件を広げて見直す
                    </button>
                  </div>
                )}

                {appliedLabel && (
                  <div
                    className={`mb-2 ${conciergeSoftCardClass} flex items-center justify-between text-xs leading-6 text-slate-600`}
                  >
                    <span>{appliedLabel}</span>
                    <button
                      type="button"
                      className="rounded-[var(--kt-radius-control)] px-2 py-1 font-semibold text-[var(--kt-color-text-secondary)] hover:bg-slate-100"
                      onClick={() => onAction?.({ type: "filter_clear" })}
                    >
                      クリア
                    </button>
                  </div>
                )}

                <div className="space-y-3">
                  {heroItem
                    ? (() => {
                        const inputNeedTags = payload?.meta?.needTags ?? [];
                        const matchedNeedTags = heroItem.breakdown?.matched_need_tags ?? [];
                        const effectiveNeedTags = inputNeedTags.length > 0 ? inputNeedTags : matchedNeedTags;

                        const reasonVm = buildRecommendationReasonViewModel({
                          rec: {
                            id: heroItem.shrineId,
                            display_name: heroItem.title,
                            name: heroItem.title,
                            breakdown: heroItem.breakdown ?? null,
                            breakdown_detail: (heroItem as any).breakdown_detail ?? null,
                            reason: heroItem.description ?? null,
                            fallback_mode: payload?.meta?.resultState?.fallback_mode ?? null,
                            distance_m: (heroItem as any).distance_m ?? null,
                            popular_score: (heroItem as any).popular_score ?? null,
                            astro_elements: (heroItem as any).astro_elements ?? null,
                            astro_priority: (heroItem as any).astro_priority ?? null,
                            explanation: (heroItem as any).explanation ?? null,
                          },
                          reasonFacts: heroItem.reasonFacts ?? null,
                          index: 0,
                          mode: normalizedMode,
                          birthdate: filterState?.birthdate ?? null,
                          needTags: effectiveNeedTags,
                        });
                        const reasonDisplay = buildRecommendationReasonDisplay({
                          matchReason: reasonVm.list.primaryPhrase,
                          reason: heroItem.description,
                          directionReference: heroItem.directionReference,
                        });
                        // Reason V4構造化契約(fact/interpretation/action)を優先し、
                        // needTagsベースの独自テンプレート(reasonDisplay)は新fieldが無い場合のfallbackとしてのみ使う
                        const heroReasonV4 = buildHeroReasonV4Sections({
                          detail: (heroItem as any).reasonV4Detail ?? null,
                          recommendationReasonV4: (heroItem as any).recommendationReasonV4 ?? null,
                          reason: heroItem.description ?? null,
                        });
                        // 構造化Reason V4がある場合は重複を避ける。無い場合はBackendが指定した
                        // reason_facts Primaryをadapter経由でVisible UIへ渡す。
                        const heroSecondaryReason = heroReasonV4.hasStructured ? null : heroReasonV4.fallbackText;
                        const trustMetadata = (heroItem as any).trustMetadata ?? null;
                        const trustLabels = [
                          trustMetadata?.rank_class ?? trustMetadata?.rankClass,
                          ...(trustMetadata?.cultural_status ?? trustMetadata?.culturalStatus ?? []),
                          trustMetadata?.lineage,
                        ].filter(Boolean);

                        const historyTheme =
                          typeof (heroItem as any).history_theme === "string"
                            ? (heroItem as any).history_theme
                            : typeof (heroItem as any).historyTheme === "string"
                              ? (heroItem as any).historyTheme
                              : null;
                        const historyContext =
                          typeof (heroItem as any).history_context === "string"
                            ? (heroItem as any).history_context
                            : typeof (heroItem as any).historyContext === "string"
                              ? (heroItem as any).historyContext
                              : null;
                        const historyThemeDisplay = historyContext
                          ? {
                              title: "この神社が持つ文脈",
                              body: historyContext,
                            }
                          : buildHistoryThemeDisplay(historyTheme);

                        return (
                          <div key={`rec-${i}-hero-${heroItem.shrineId}`} className="space-y-2">
                            <ConciergeTopRecommendationHero
                              name={heroItem.title}
                              href={withDirectionRouteContext(heroItem.detailHref, heroItem.directionReference, "hero")}
                              imageUrl={heroItem.imageUrl}
                              address={null}
                              topReasonLabel={reasonVm.hero.topReasonLabel ?? null}
                              eyebrowLabel={reasonVm.hero.eyebrowLabel ?? null}
                              subtitle={reasonVm.hero.subtitle ?? null}
                              catchCopy={reasonVm.hero.catchCopy}
                              whyTop={null}
                              primaryReason={heroReasonV4.hasStructured ? null : reasonVm.list.primaryPhrase}
                              secondaryReason={heroSecondaryReason}
                              factReason={heroReasonV4.factText}
                              interpretationReason={heroReasonV4.interpretationText}
                              actionReason={heroReasonV4.actionText}
                              differenceFromOthers={null}
                              tags={matchedNeedTags.map(labelNeedDisplayTag).slice(0, 3)}
                              actionSuggestions={(heroItem as any).actionSuggestions ?? []}
                              actionSuggestionV4Preview={(heroItem as any).actionSuggestionV4Preview ?? null}
                              analyticsSource="concierge_result"
                              threadId={tid ?? null}
                              resultSetId={resultSetId}
                              shrineId={heroItem.shrineId}
                              recommendationRank={1}
                              historyTheme={historyTheme ?? analyticsContext?.historyTheme ?? null}
                              routeLabel="神社の詳細を見る"
                              onDetailClick={() =>
                                { if (heroItem.directionReference?.matched) trackWebDirection("direction_match_detail_opened", { matched: true, recommendation_rank: 1 }); trackSearchEvent("shrine_detail_transition", {
                                  source: "concierge_result",
                                  threadId: tid ?? undefined,
                                  resultSetId,
                                  position: "hero_primary",
                                  recommendationRank: 1,
                                  shrineId: heroItem.shrineId,
                                  mode: analyticsContext?.mode ?? normalizedMode,
                                  flow: analyticsContext?.flow,
                                  hasBirthdate: analyticsContext?.hasBirthdate,
                                  recommendationCount: analyticsContext?.recommendationCount,
                                  historyTheme: historyTheme ?? analyticsContext?.historyTheme,
                                  ...consultationAxisAnalytics(heroItem.consultationAxis ?? analyticsContext?.consultationAxis),
                                  firstClick: resolveFirstResultClick(resultSetId),
                                  ...(heroItem.analyticsProvenance
                                    ? recommendationAnalyticsProperties(heroItem.analyticsProvenance)
                                    : {}),
                                }); }
                              }
                            />
                            <DirectionReferenceCard reference={reasonDisplay.directionReference} recommendationKey={heroItem.shrineId} rank={1} />

                            {trustMetadata ? (
                              <section className={conciergeSoftCardClass}>
                                <div className="space-y-2">
                                  <div className="flex flex-wrap gap-1">
                                    {trustLabels.slice(0, 4).map((label: string) => (
                                      <span
                                        key={label}
                                        className="rounded-[var(--kt-radius-pill)] bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-600"
                                      >
                                        {label}
                                      </span>
                                    ))}
                                  </div>
                                  {trustMetadata.origin_summary || trustMetadata.originSummary ? (
                                    <p className="text-xs leading-6 text-slate-600">
                                      {trustMetadata.origin_summary ?? trustMetadata.originSummary}
                                    </p>
                                  ) : null}
                                </div>
                              </section>
                            ) : null}

                            {shrineMeaningVisibility !== "hidden" ? (
                              <section className={conciergeSoftCardClass}>
                                <div className="space-y-2">
                                  <p className="text-xs font-semibold tracking-[0.12em] text-[var(--kt-color-text-muted)]">
                                    相談から見た意味
                                  </p>
                                  <p className="text-sm leading-7 text-[var(--kt-color-text-secondary)]">{reasonVm.detail.shrineMeaning}</p>
                                </div>
                              </section>
                            ) : null}

                            {historyThemeDisplay ? (
                              <section className={conciergeSoftCardClass}>
                                <div className="space-y-2">
                                  <p className="text-xs font-semibold tracking-[0.12em] text-[var(--kt-color-text-muted)]">
                                    この神社が持つ文脈
                                  </p>

                                  <p className="text-sm leading-7 text-[var(--kt-color-text-secondary)]">{historyThemeDisplay.body}</p>
                                </div>
                              </section>
                            ) : null}

                            {actionMeaningVisibility !== "hidden" ? (
                              <section className={conciergeSoftCardClass}>
                                <div className="space-y-2">
                                  <p className="text-xs font-semibold tracking-[0.12em] text-[var(--kt-color-text-muted)]">
                                    今の自分への問い
                                  </p>
                                  <p className="text-sm leading-7 text-[var(--kt-color-text-secondary)]">
                                    {actionMeaningVisibility === "teaser"
                                      ? "この結果を保存すると、今の状態や選んだ理由をあとから見返せます。"
                                      : (reasonVm.detail.actionMeaning ?? reasonVm.detail.shrineMeaning)}
                                  </p>
                                </div>
                              </section>
                            ) : null}

                            {consultationSummaryVisibility !== "hidden" && reasonVm.detail.consultationSummary ? (
                              <ConciergeConsultationSummary
                                summary={reasonVm.detail.consultationSummary}
                                modeLabel={normalizedMode === "compat" ? "相性ベース" : "悩みベース"}
                              />
                            ) : null}

                            <ShrineSaveButton
                              shrineId={heroItem.shrineId}
                              ctx="concierge"
                              tid={tid}
                              nextPath={heroItem.detailHref}
                              variant="subtle"
                            />

                            {premiumPreviewVisibility !== "hidden" ? (
                              <ConciergePremiumEntryCard
                                shrineId={heroItem.shrineId}
                                tid={tid}
                                isGuestUser={isGuestUser}
                                accessLevel={accessLevel}
                                analyticsContext={analyticsContext}
                              />
                            ) : null}
                          </div>
                        );
                      })()
                    : null}

                  {otherRegisteredItems.length > 0 ? (
                    <div className="pt-8">
                      <button
                        type="button"
                        className="w-full rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] px-4 py-3 text-xs font-semibold text-[var(--kt-color-text-muted)] transition hover:bg-[var(--kt-color-background-subtle)] hover:text-[var(--kt-color-text-secondary)]"
                        aria-expanded={showOtherRecommendations}
                        aria-controls={otherRecommendationsId}
                        onClick={() => setShowOtherRecommendations((prev) => !prev)}
                      >
                        {showOtherRecommendations ? "ほかの神社を閉じる" : "迷った時だけ、ほかの神社を見る"}
                      </button>

                      {showOtherRecommendations ? (
                        <div id={otherRecommendationsId}>
                          <div className="mb-2 mt-3 text-xs font-semibold tracking-[0.16em] text-[var(--kt-color-text-muted)]">
                            ほかの神社
                          </div>
                          <p className="mb-3 text-xs leading-5 text-[var(--kt-color-text-muted)]">迷った時の参考です。</p>

                          <div className="space-y-3">
                            {otherRegisteredItems.map((item: RegisteredShrineItem, compactIdx: number) => {
                              const compactReasonVm = buildRecommendationReasonViewModel({
                                rec: {
                                  id: item.shrineId,
                                  display_name: item.title,
                                  name: item.title,
                                  breakdown: item.breakdown ?? null,
                                  breakdown_detail: (item as any).breakdown_detail ?? null,
                                  reason: item.description ?? null,
                                  fallback_mode: payload?.meta?.resultState?.fallback_mode ?? null,
                                  distance_m: (item as any).distance_m ?? null,
                                  popular_score: (item as any).popular_score ?? null,
                                  astro_elements: (item as any).astro_elements ?? null,
                                  astro_priority: (item as any).astro_priority ?? null,
                                  explanation: (item as any).explanation ?? null,
                                },
                                reasonFacts: item.reasonFacts ?? null,
                                index: compactIdx + 1,
                                mode: normalizedMode,
                                birthdate: filterState?.birthdate ?? null,
                                needTags: item.breakdown?.matched_need_tags ?? [],
                              });
                              const compactReasonDisplay = buildRecommendationReasonDisplay({
                                matchReason: compactReasonVm.list.primaryPhrase,
                                reason: item.description,
                                directionReference: item.directionReference,
                              });

                              return (
                                <div key={`rec-${i}-compact-${item.shrineId}`} className="space-y-2">
                                  <ShrineCardCompact
                                    name={item.title}
                                    href={withDirectionRouteContext(item.detailHref, item.directionReference, "other")}
                                    imageUrl={item.imageUrl}
                                    address={item.address ?? null}
                                    summary={compactReasonDisplay.reason}
                                    primaryReason={compactReasonDisplay.matchReason}
                                    tags={[]}
                                    distanceM={(item as any).distance_m ?? null}
                                    onDetailClick={() =>
                                      { if (item.directionReference?.matched) trackWebDirection("direction_match_detail_opened", { matched: true, recommendation_rank: compactIdx + 2 }); trackSearchEvent("shrine_detail_transition", {
                                        source: "concierge_result",
                                        threadId: tid ?? undefined,
                                        resultSetId,
                                        position: "compact",
                                        recommendationRank: compactIdx + 2,
                                        shrineId: item.shrineId,
                                        mode: analyticsContext?.mode ?? normalizedMode,
                                        flow: analyticsContext?.flow,
                                        hasBirthdate: analyticsContext?.hasBirthdate,
                                        recommendationCount: analyticsContext?.recommendationCount,
                                        historyTheme:
                                          typeof (item as any).history_theme === "string"
                                            ? (item as any).history_theme
                                            : typeof (item as any).historyTheme === "string"
                                              ? (item as any).historyTheme
                                              : analyticsContext?.historyTheme,
                                        ...consultationAxisAnalytics(
                                          (item as any).consultationAxis ?? analyticsContext?.consultationAxis,
                                        ),
                                        firstClick: resolveFirstResultClick(resultSetId),
                                        ...(item.analyticsProvenance
                                          ? recommendationAnalyticsProperties(item.analyticsProvenance)
                                          : {}),
                                      }); }
                                    }
                                  />
                                  <DirectionReferenceCard reference={compactReasonDisplay.directionReference} recommendationKey={item.shrineId} rank={compactIdx + 2} />
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}
                    </div>
                  ) : null}

                  {placeItems.length > 0 ? (
                    <div className="space-y-3 pt-4">
                      {placeItems.map((item: PlaceShrineItem, placeIdx: number) => (
                        <div key={`rec-${i}-${placeIdx}-place-${item.placeId}`} className="space-y-2">
                          <PlaceShrineCard
                            placeId={item.placeId}
                            title={item.title}
                            address={item.address}
                            description={item.description}
                            imageUrl={item.imageUrl}
                            detailHref={item.detailHref}
                            detailLabel={item.detailLabel}
                          />
                        </div>
                      ))}
                    </div>
                  ) : null}

                  {!isEntryRoute && savePromptVisibility !== "hidden" ? (
                    <div className="pt-4">
                      <button
                        type="button"
                        className="w-full rounded-[var(--kt-radius-panel)] border px-4 py-3 text-sm font-semibold text-[var(--kt-color-text-secondary)] hover:bg-[var(--kt-color-background-subtle)]"
                        onClick={() => {
                          trackCardEvent({
                            event: "save_prompt_click",
                            cardId: "save_prompt",
                            source: "concierge_result",
                            accessLevel,
                            visibility: savePromptVisibility,
                            ctaType: isGuestUser ? "login_to_save" : "save",
                            ...analyticsContext,
                            ...consultationAxisAnalytics(analyticsContext?.consultationAxis),
                            threadId: tid ?? undefined,
                            resultSetId,
                          });

                          onAction?.({ type: "save_concierge_thread" });
                        }}
                        disabled={sending}
                      >
                        {isGuestUser ? "ログインしてあとで見返す" : "あとで見返すために保存"}
                      </button>
                    </div>
                  ) : null}
                </div>
              </DetailSection>
            );
          }

          case "astro":
            return (
              <AstroCard
                key={`astro-${i}`}
                sunSign={(sec as any).sunSign}
                element={(sec as any).element}
                reason={(sec as any).reason}
              />
            );

          default:
            return null;
        }
      })}
      {/* 下部固定バーを前提にした余白は持たせない。結果セクションはここで閉じる。 */}
    </div>
  );
}
