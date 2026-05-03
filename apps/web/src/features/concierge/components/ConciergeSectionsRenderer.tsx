"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import DetailSection from "@/components/shrine/DetailSection";
import PlaceShrineCard from "@/components/shrine/PlaceShrineCard";
import ShrineSaveButton from "@/components/shrine/ShrineSaveButton";
import ConciergeFilterPanel from "@/features/concierge/components/ConciergeFilterPanel";
import ModeBadge from "@/features/concierge/components/ModeBadge";
import { buildRecommendationReasonViewModel } from "@/lib/concierge/buildRecommendationReasonViewModel";
import ConciergeTopRecommendationHero from "@/features/concierge/components/ConciergeTopRecommendationHero";
import ConciergeConsultationSummary from "@/features/concierge/components/ConciergeConsultationSummary";
import ShrineCardCompact from "@/components/shrines/ShrineCardCompact";
import { track } from "@/lib/analytics/track";
import { buildGoogleMapsDirUrl } from "@/lib/maps/googleMaps";

import type {
  ConciergeSectionsPayload,
  ConciergeSection,
  ConciergeFilterState,
  RegisteredShrineItem,
  PlaceShrineItem,
  RendererAction,
} from "@/features/concierge/sections/types";

type MetaMode = NonNullable<ConciergeSectionsPayload["meta"]>["mode"];

const conciergeSoftCardClass = "rounded-2xl border border-slate-200 bg-slate-50 shadow-sm p-4";
const conciergeNoticeCardClass = "rounded-2xl border border-amber-200 bg-amber-50 shadow-sm p-4";

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

function AstroCard(props: { sunSign?: string; element?: string; reason?: string }) {
  const { sunSign, element, reason } = props;
  return (
    <DetailSection title="占星術による選定">
      <div className={conciergeNoticeCardClass}>
        <div className="text-sm font-semibold text-slate-900">
          {sunSign || "不明"} / {element || "不明"}
        </div>
        <div className="mt-2 text-sm leading-7 text-slate-700">{reason || "（理由なし）"}</div>
      </div>
    </DetailSection>
  );
}

type Props = {
  payload: ConciergeSectionsPayload;
  onAction?: (action: RendererAction) => void;
  sending?: boolean;
  threadId?: number | null;
  isEntryRoute?: boolean;
};

function parseExtraTokens(extra: string | undefined | null): string[] {
  return (extra || "")
    .split(/[、,\s]+/)
    .map((x) => x.trim())
    .filter(Boolean);
}

export default function ConciergeSectionsRenderer({
  payload,
  onAction,
  sending = false,
  threadId = null,
  isEntryRoute = false,
}: Props) {
  const trackedImpressionKeysRef = useRef<Set<string>>(new Set());
  const [showOtherRecommendations, setShowOtherRecommendations] = useState(false);

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
      }));
    });
  }, [payload, normalizedModeForTracking]);

  const resultSetId = useMemo(() => {
    const signature = resultImpressions.map((item) => `${item.rank}:${item.position}:${item.shrineId}`).join("|");
    return `${tid ?? "unknown"}:${signature || "empty"}`;
  }, [resultImpressions, tid]);

  useEffect(() => {
    resultImpressions.forEach((item) => {
      const impressionKey = `${resultSetId}:concierge_result_impression:${item.shrineId}:${item.position}:${item.rank}`;
      if (trackedImpressionKeysRef.current.has(impressionKey)) return;

      trackedImpressionKeysRef.current.add(impressionKey);
      track("concierge_result_impression", {
        shrineId: item.shrineId,
        name: item.name,
        position: item.position,
        rank: item.rank,
        ctx: "concierge",
        tid,
        resultSetId,
        mode: item.mode,
      });
    });
  }, [resultImpressions, resultSetId, tid]);

  if (!payload || !Array.isArray(payload.sections) || payload.sections.length === 0) return null;

  return (
    <div className="mx-auto w-full max-w-md min-w-0 space-y-4 pb-0">
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
                if (next.has(p)) next.delete(p);
                else next.add(p);
                onAction?.({ type: "filter_set_extra", extraCondition: Array.from(next).join(" ") });
              };

              const selectedPresets = presets.filter((p) => set.has(p));

              return (
                <div key={`filter-${i}-closed`}>
                  <DetailSection title="条件で絞る">
                    <p className="mb-2 text-xs text-slate-500">まずは条件を追加</p>

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
                                ? "bg-emerald-600 text-white border-emerald-600"
                                : "bg-white text-slate-700 hover:bg-slate-50",
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

                    {!isEntryRoute && (
                      <button
                        type="button"
                        className="mt-2 w-full rounded-xl border px-4 py-3 text-sm font-semibold"
                        onClick={() => onAction?.({ type: "back_to_entry" })}
                        disabled={sending}
                      >
                        入口に戻る
                      </button>
                    )}

                    <button
                      type="button"
                      className="w-full rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
                      disabled={!canApplyCompatFilter || sending}
                      onClick={() => {
                        onAction?.({ type: "filter_apply" });
                      }}
                    >
                      {sending ? "絞り込み中…" : "この条件で絞り込む"}
                    </button>

                    <button
                      type="button"
                      className="mt-2 w-full rounded-xl border px-4 py-3 text-sm font-semibold"
                      onClick={() => onAction?.({ type: "add_condition" })}
                    >
                      詳細条件を設定する
                    </button>
                  </DetailSection>
                </div>
              );
            }

            return (
              <div key={`filter-${i}-open`}>
                <DetailSection title={title}>
                  <div>
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
                    />
                  </div>
                </DetailSection>
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
              (hasDummy ? "条件に合う候補が少ないため、まずは選びやすい候補から表示しています。" : null);

            const topRegisteredItem = items.find(
              (x: RegisteredShrineItem | PlaceShrineItem) => x.kind === "registered",
            ) as RegisteredShrineItem | undefined;

            const normalizedMode = normalizeConciergeMode(payload?.meta?.mode);

            const topReasonVm =
              topRegisteredItem && topRegisteredItem.kind === "registered"
                ? buildRecommendationReasonViewModel({
                    rec: {
                      display_name: topRegisteredItem.title,
                      name: topRegisteredItem.title,
                      breakdown: topRegisteredItem.breakdown ?? null,
                      reason: topRegisteredItem.description ?? null,
                      fallback_mode: payload?.meta?.resultState?.fallback_mode ?? null,
                      distance_m: (topRegisteredItem as any).distance_m ?? null,
                      popular_score: (topRegisteredItem as any).popular_score ?? null,
                      astro_elements: (topRegisteredItem as any).astro_elements ?? null,
                      astro_priority: (topRegisteredItem as any).astro_priority ?? null,
                      explanation: (topRegisteredItem as any).explanation ?? null,
                      reason_facts: (topRegisteredItem as any).reasonFacts ?? null,
                    },
                    index: 0,
                    mode: normalizedMode,
                    birthdate: filterState?.birthdate ?? null,
                    needTags: topRegisteredItem.breakdown?.matched_need_tags ?? [],
                  })
                : null;

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

                {topReasonVm?.detail.consultationSummary ? (
                  <div className="mb-4">
                    <ConciergeConsultationSummary
                      summary={topReasonVm.detail.consultationSummary}
                      modeLabel={normalizedMode === "compat" ? "相性をもとに見ています" : "相談内容をもとに見ています"}
                      appliedLabel={appliedLabel}
                    />
                  </div>
                ) : null}

                {typeof payload?.meta?.remaining === "number" && payload.meta.remaining > 0 && (
                  <div className="mb-2 text-xs leading-6 text-slate-500">
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
                      className="rounded-xl border px-4 py-3 text-sm font-semibold"
                      onClick={() => onAction?.({ type: "open_map" })}
                    >
                      近くの候補を優先して探す
                    </button>
                    <button
                      type="button"
                      className="rounded-xl bg-neutral-900 px-4 py-3 text-sm font-semibold text-white"
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
                      className="rounded-md px-2 py-1 font-semibold text-slate-700 hover:bg-slate-100"
                      onClick={() => onAction?.({ type: "filter_clear" })}
                    >
                      クリア
                    </button>
                  </div>
                )}

                <div className="space-y-3">
                  {heroItem
                    ? (() => {
                        const reasonVm = buildRecommendationReasonViewModel({
                          rec: {
                            display_name: heroItem.title,
                            name: heroItem.title,
                            breakdown: heroItem.breakdown ?? null,
                            reason: heroItem.description ?? null,
                            fallback_mode: payload?.meta?.resultState?.fallback_mode ?? null,
                            distance_m: (heroItem as any).distance_m ?? null,
                            popular_score: (heroItem as any).popular_score ?? null,
                            astro_elements: (heroItem as any).astro_elements ?? null,
                            astro_priority: (heroItem as any).astro_priority ?? null,
                            explanation: (heroItem as any).explanation ?? null,
                            reason_facts: (heroItem as any).reasonFacts ?? null,
                          },
                          index: 0,
                          mode: normalizedMode,
                          birthdate: filterState?.birthdate ?? null,
                          needTags: heroItem.breakdown?.matched_need_tags ?? [],
                        });

                        return (
                          <div key={`rec-${i}-hero-${heroItem.shrineId}`} className="space-y-2">
                            <ConciergeTopRecommendationHero
                              name={heroItem.title}
                              href={heroItem.detailHref}
                              imageUrl={heroItem.imageUrl}
                              address={null}
                              topReasonLabel={reasonVm.hero.topReasonLabel ?? null}
                              catchCopy={reasonVm.hero.catchCopy}
                              whyTop={null}
                              primaryReason={reasonVm.why.primaryReason}
                              secondaryReason={null}
                              differenceFromOthers={null}
                              tags={(heroItem.breakdown?.matched_need_tags ?? []).slice(0, 3)}
                              routeLabel="まずはここに行く"
                              secondaryActionSlot={
                                <ShrineSaveButton
                                  shrineId={heroItem.shrineId}
                                  ctx="concierge"
                                  tid={tid}
                                  nextPath={heroItem.detailHref}
                                  variant="subtle"
                                />
                              }
                              onRouteClick={() => {
                                track("concierge_result_click", {
                                  action: "route",
                                  position: "hero_primary",
                                  rank: 1,
                                  shrineId: heroItem.shrineId,
                                  firstClick: resolveFirstResultClick(resultSetId),
                                });

                                onAction?.({
                                  type: "open_map",
                                  shrineId: heroItem.shrineId,
                                  rank: 1,
                                  routeHref: buildGoogleMapsDirUrl({
                                    address: (heroItem as any).address ?? null,
                                    fallbackName: heroItem.title,
                                  }),
                                });
                              }}
                              onDetailClick={() =>
                                track("concierge_result_click", {
                                  action: "detail",
                                  position: "hero_secondary",
                                  rank: 1,
                                  shrineId: heroItem.shrineId,
                                  firstClick: resolveFirstResultClick(resultSetId),
                                })
                              }
                            />
                          </div>
                        );
                      })()
                    : null}

                  {otherRegisteredItems.length > 0 ? (
                    <div className="pt-8">
                      {!showOtherRecommendations ? (
                        <button
                          type="button"
                          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs font-semibold text-slate-500 transition hover:bg-slate-50 hover:text-slate-700"
                          onClick={() => setShowOtherRecommendations(true)}
                        >
                          迷った時だけ、ほかの候補を見る
                        </button>
                      ) : (
                        <div>
                          <div className="mb-2 text-xs font-semibold tracking-[0.16em] text-slate-500">ほかの候補</div>
                          <p className="mb-3 text-xs leading-5 text-slate-500">迷った時の参考です。</p>

                          <div className="space-y-3">
                            {otherRegisteredItems.map((item: RegisteredShrineItem, compactIdx: number) => {
                              return (
                                <div key={`rec-${i}-compact-${item.shrineId}`} className="space-y-2">
                                  <ShrineCardCompact
                                    name={item.title}
                                    href={item.detailHref}
                                    imageUrl={item.imageUrl}
                                    address={null}
                                    summary={null}
                                    primaryReason={null}
                                    tags={[]}
                                    distanceM={(item as any).distance_m ?? null}
                                    onDetailClick={() =>
                                      track("concierge_result_click", {
                                        action: "detail",
                                        position: "compact",
                                        rank: compactIdx + 2,
                                        shrineId: item.shrineId,
                                        firstClick: resolveFirstResultClick(resultSetId),
                                      })
                                    }
                                  />
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
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

                  {!isEntryRoute ? (
                    <div className="pt-4">
                      <button
                        type="button"
                        className="w-full rounded-xl border px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                        onClick={() => onAction?.({ type: "save_concierge_thread" })}
                        disabled={sending}
                      >
                        この相談を保存する
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
