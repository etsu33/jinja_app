"use client";

import type { FormEvent, ReactNode } from "react";

import type { GoriyakuTag } from "@/lib/api/tags";

import { DetailSearchAccordion } from "./DetailSearchAccordion";
import { ExperienceFilterSection } from "./ExperienceFilterSection";
import { NearbySection } from "./NearbySection";
import { type ExploreViewMode, ViewModeTabs } from "./ViewModeTabs";

type ExploreLayoutProps = {
  activeTag: string;
  inputValue: string;
  onInputValueChange: (value: string) => void;
  onSearchSubmit: (event: FormEvent<HTMLFormElement>) => void;
  goriyakuTags: readonly GoriyakuTag[];
  tagsLoading: boolean;
  tagsError: string | null;
  activeGoriyakuTag: GoriyakuTag | null;
  onSelectTag: (tagName: string) => void;
  viewMode: ExploreViewMode;
  onViewModeChange: (viewMode: ExploreViewMode) => void;
  showNearbyList?: boolean;
  experienceFeedback?: ReactNode;
  children: ReactNode;
};

export function ExploreLayout({
  activeTag,
  inputValue,
  onInputValueChange,
  onSearchSubmit,
  goriyakuTags,
  tagsLoading,
  tagsError,
  activeGoriyakuTag,
  onSelectTag,
  viewMode,
  onViewModeChange,
  showNearbyList = false,
  experienceFeedback,
  children,
}: ExploreLayoutProps) {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <p className="text-[11px] font-medium tracking-[0.2em] text-stone-500">EXPLORE</p>
        <h1 className="text-xl font-medium text-stone-900">神社をたどる</h1>
      </header>

      <ExperienceFilterSection activeTag={activeTag} onSelectTag={onSelectTag} />

      {experienceFeedback ? <div>{experienceFeedback}</div> : null}

      <DetailSearchAccordion
        inputValue={inputValue}
        onInputValueChange={onInputValueChange}
        onSubmit={onSearchSubmit}
        goriyakuTags={goriyakuTags}
        tagsLoading={tagsLoading}
        tagsError={tagsError}
        activeTag={activeTag}
        activeGoriyakuTag={activeGoriyakuTag}
        onSelectTag={onSelectTag}
      />

      <NearbySection showNearbyList={showNearbyList} />

      <div className="flex justify-end">
        <ViewModeTabs value={viewMode} onChange={onViewModeChange} />
      </div>

      <section className="space-y-4">{children}</section>
    </div>
  );
}
