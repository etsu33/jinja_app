"use client";

import { useEffect, useMemo } from "react";
import DetailSection from "@/components/shrine/DetailSection";
import ShrineCard from "@/components/shrine/ShrineCard";
import PlaceShrineCard from "@/components/shrine/PlaceShrineCard";
import ConciergeFilterPanel from "@/features/concierge/components/ConciergeFilterPanel";
import ModeBadge from "@/features/concierge/components/ModeBadge";

import type {
  ConciergeSectionsPayload,
  ConciergeSection,
  ConciergeFilterState,
  RegisteredShrineItem,
  PlaceShrineItem,
  RendererAction,
} from "@/features/concierge/sections/types";

function AstroCard(props: { sunSign?: string; element?: string; reason?: string }) {
  const { sunSign, element, reason } = props;
  return (
    <DetailSection title="占星術による選定">
      <div className="rounded-lg border border-primary/20 bg-primary/5 px-5 py-4">
        <div className="text-sm font-medium text-foreground/80">
          {sunSign || "不明"} / {element || "不明"}
        </div>
        <div className="mt-2 text-sm leading-relaxed text-muted-foreground">{reason || "（理由なし）"}</div>
      </div>
    </DetailSection>
  );
}

type Props = {
  payload: ConciergeSectionsPayload;
  onAction?: (action: RendererAction) => void;
  sending?: boolean;
};

function parseExtraTokens(extra: string | undefined | null): string[] {
  return (extra || "")
    .split(/[、,\s]+/)
    .map((x) => x.trim())
    .filter(Boolean);
}

export default function ConciergeSectionsRenderer({ payload, onAction, sending = false }: Props) {
  // ✅ hooks は必ず同じ順序
  useEffect(() => {
    const onOpen = () => onAction?.({ type: "add_condition" });
    window.addEventListener("concierge:open-filter", onOpen);
    return () => window.removeEventListener("concierge:open-filter", onOpen);
  }, [onAction]);


  // ✅ filter state は map の外で1回だけ取る
  const filterState: ConciergeFilterState | null = useMemo(() => {
    const sec = payload.sections.find((s) => s.type === "filter") as any;
    return (sec?.state ?? null) as ConciergeFilterState | null;
  }, [payload]);

  const appliedTokens = parseExtraTokens(filterState?.extraCondition);
  const appliedLabel = appliedTokens.length ? `${appliedTokens.join(" / ")} で絞り込みました` : null;

  if (!payload || !Array.isArray(payload.sections) || payload.sections.length === 0) return null;

  return (
    <div className="mx-auto w-full max-w-md min-w-0 space-y-4">
      {payload.sections.map((sec: ConciergeSection, i: number) => {
        switch (sec.type) {
          case "guide":
            return null;

          case "filter": {
            const state: ConciergeFilterState = (sec as any).state;
            const title = (sec as any).title ?? "条件を追加して絞る";

            // 閉じ状態（プリセット選択 + 即絞り）- 静かなUI
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
              const hasAny = selectedPresets.length > 0;

              return (
                <DetailSection key={`filter-${i}`} title="さらに条件を追加">
                  <p className="mb-4 text-sm text-muted-foreground">
                    お気持ちに合わせて絞り込めます
                  </p>

                  <div className="mb-4 flex flex-wrap gap-2">
                    {presets.map((p) => {
                      const active = set.has(p);
                      return (
                        <button
                          key={p}
                          type="button"
                          className={[
                            "rounded-full border px-4 py-2 text-xs font-medium transition-all duration-200",
                            active
                              ? "border-primary/50 bg-primary/10 text-foreground"
                              : "border-border/50 bg-card text-muted-foreground hover:border-primary/30 hover:bg-primary/5",
                          ].join(" ")}
                          onClick={() => togglePreset(p)}
                        >
                          {p}
                        </button>
                      );
                    })}
                  </div>

                  {selectedPresets.length > 0 && (
                    <div className="mb-4 rounded-lg border border-border/30 bg-secondary/50 px-4 py-3 text-sm text-foreground/70">
                      {selectedPresets.join(" / ")} で探します
                    </div>
                  )}

                  <button
                    type="button"
                    className="w-full rounded-full border border-primary/40 bg-primary/10 px-4 py-3 text-sm font-medium text-foreground/90 transition-all duration-200 hover:bg-primary/15 disabled:opacity-50"
                    disabled={!hasAny || sending}
                    onClick={() => onAction?.({ type: "filter_apply" })}
                  >
                    {sending ? "探しています..." : "この条件で探す"}
                  </button>

                  <button
                    type="button"
                    className="mt-3 w-full rounded-full border border-border/40 bg-card px-4 py-3 text-sm font-medium text-muted-foreground transition-all duration-200 hover:bg-secondary hover:text-foreground"
                    onClick={() => onAction?.({ type: "add_condition" })}
                  >
                    詳しく設定する
                  </button>
                </DetailSection>
              );
            }

            // 開いた状態（既存のフィルタパネル）
            return (
              <DetailSection key={`filter-${i}`} title={title}>
                <ConciergeFilterPanel
                  isOpen
                  title={title}
                  onClose={() => onAction?.({ type: "filter_close" })}
                  onApply={() => onAction?.({ type: "filter_apply" })}
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
                  onExtraConditionChange={(v: string) => onAction?.({ type: "filter_set_extra", extraCondition: v })}
                />
              </DetailSection>
            );
          }

          

          case "recommendations": {
            const items = (sec as any).items as (RegisteredShrineItem | PlaceShrineItem)[];
            const heroItem = items[0]; // 最初の1件をヒーローとして扱う
            const otherItems = items.slice(1);

            return (
              <div key={`recs-${i}`} className="space-y-8">
                {/* 相談サマリー - 静かな導入 */}
                <div className="text-center">
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    あなたの今の気持ちに寄り添う場所を
                    <br />
                    お探ししました
                  </p>
                </div>

                {appliedLabel && (
                  <div className="flex items-center justify-center gap-3 rounded-lg border border-border/30 bg-secondary/30 px-4 py-3">
                    <span className="text-sm text-foreground/70">{appliedLabel}</span>
                    <button
                      type="button"
                      className="text-xs font-medium text-muted-foreground hover:text-foreground"
                      onClick={() => onAction?.({ type: "filter_clear" })}
                    >
                      クリア
                    </button>
                  </div>
                )}

                {/* ヒーロー神社 - 1件を主役に */}
                {heroItem && (
                  <div className="space-y-4">
                    <div className="text-center">
                      <p className="text-xs font-medium uppercase tracking-[0.15em] text-foreground/50">
                        おすすめの場所
                      </p>
                    </div>

                    {heroItem.kind === "registered" ? (
                      <ShrineCard
                        shrineId={heroItem.shrineId}
                        title={heroItem.title}
                        address={heroItem.address}
                        description={heroItem.description}
                        imageUrl={heroItem.imageUrl}
                        breakdown={heroItem.breakdown ?? null}
                        detailHref={heroItem.detailHref}
                        hideLeftMark
                        hideBadges
                      />
                    ) : (
                      <PlaceShrineCard
                        placeId={heroItem.placeId}
                        title={heroItem.title}
                        address={heroItem.address}
                        description={heroItem.description}
                        imageUrl={heroItem.imageUrl}
                        detailHref={heroItem.detailHref}
                        detailLabel={heroItem.detailLabel}
                      />
                    )}
                  </div>
                )}

                {/* 他の候補 - 控えめに */}
                {otherItems.length > 0 && (
                  <div className="space-y-4">
                    <div className="mx-auto h-px w-12 bg-border/40" />
                    <p className="text-center text-xs text-muted-foreground/70">
                      ほかにも気になる場所があれば
                    </p>

                    <div className="space-y-4">
                      {otherItems.map((item, idx) => {
                        if (item.kind === "registered") {
                          return (
                            <ShrineCard
                              key={`rec-${i}-${idx + 1}`}
                              shrineId={item.shrineId}
                              title={item.title}
                              address={item.address}
                              description={item.description}
                              imageUrl={item.imageUrl}
                              breakdown={item.breakdown ?? null}
                              detailHref={item.detailHref}
                              hideLeftMark
                              hideBadges
                            />
                          );
                        }

                        return (
                          <PlaceShrineCard
                            key={`rec-${i}-${idx + 1}`}
                            placeId={item.placeId}
                            title={item.title}
                            address={item.address}
                            description={item.description}
                            imageUrl={item.imageUrl}
                            detailHref={item.detailHref}
                            detailLabel={item.detailLabel}
                          />
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
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
    </div>
  );
}
