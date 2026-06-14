

import type { Meta, StoryObj } from "@storybook/react";

import { ExploreLayout } from "./ExploreLayout";

const mockGoriyakuTags = [
  { id: 1, name: "縁結び", slug: "enmusubi" },
  { id: 2, name: "金運・商売繁盛", slug: "kinun" },
  { id: 3, name: "厄除け", slug: "yakuyoke" },
];

const meta = {
  title: "Explore/ExploreLayout",
  component: ExploreLayout,
  argTypes: {
    onInputValueChange: { action: "inputValueChange" },
    onSearchSubmit: { action: "searchSubmit" },
    onSelectTag: { action: "selectTag" },
    onViewModeChange: { action: "viewModeChange" },
  },
  args: {
    activeTag: "",
    inputValue: "",
    goriyakuTags: mockGoriyakuTags,
    tagsLoading: false,
    tagsError: null,
    activeGoriyakuTag: null,
    viewMode: "list",
    showNearbyList: false,
    children: (
      <div className="grid gap-3">
        <div className="rounded-3xl border border-stone-200/30 bg-white/70 p-4 text-sm text-stone-700">
          浅草神社
        </div>
        <div className="rounded-3xl border border-stone-200/30 bg-white/70 p-4 text-sm text-stone-700">
          神田明神
        </div>
        <div className="rounded-3xl border border-stone-200/30 bg-white/70 p-4 text-sm text-stone-700">
          東京大神宮
        </div>
      </div>
    ),
  },
} satisfies Meta<typeof ExploreLayout>;

export default meta;
type Story = StoryObj<typeof meta>;

export const DefaultList: Story = {};

export const MapMode: Story = {
  args: {
    viewMode: "map",
    children: (
      <div className="rounded-3xl border border-stone-200/30 bg-stone-50/60 p-8 text-center text-sm text-stone-500">
        地図表示エリア
      </div>
    ),
  },
};

export const ActiveTag: Story = {
  args: {
    activeTag: "静か",
    experienceFeedback: <p className="text-xs text-emerald-700 opacity-70">静かで表示中です。</p>,
  },
};

export const EmptyResult: Story = {
  args: {
    children: (
      <div className="rounded-3xl border border-stone-200/30 bg-stone-50/50 p-5 text-sm text-stone-700">
        条件に合う神社はまだ見つかりません。
      </div>
    ),
  },
};
