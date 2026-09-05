

"use client";

import type { FormEvent } from "react";

import type { GoriyakuTag } from "@/lib/api/tags";

type DetailSearchAccordionProps = {
  inputValue: string;
  onInputValueChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  goriyakuTags: readonly GoriyakuTag[];
  tagsLoading: boolean;
  tagsError: string | null;
  activeTag: string;
  activeGoriyakuTag: GoriyakuTag | null;
  onSelectTag: (tagName: string) => void;
};

export function DetailSearchAccordion({
  inputValue,
  onInputValueChange,
  onSubmit,
  goriyakuTags,
  tagsLoading,
  tagsError,
  activeTag,
  activeGoriyakuTag,
  onSelectTag,
}: DetailSearchAccordionProps) {
  return (
    <details className="rounded-3xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] p-4">
      <summary className="cursor-pointer text-sm font-medium text-[var(--kt-color-text-primary)]">詳しく探す</summary>

      <div className="mt-4 space-y-4">
        <form onSubmit={onSubmit} className="flex flex-col gap-2 sm:flex-row sm:items-end">
          <input
            type="search"
            value={inputValue}
            onChange={(event) => onInputValueChange(event.currentTarget.value)}
            placeholder="神社名や願いごとを、そっと入力"
            className="w-full rounded-3xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] px-3 py-2 text-sm text-[var(--kt-color-text-primary)] placeholder:text-[var(--kt-color-text-muted)]"
          />
          <button
            type="submit"
            className="rounded-full border border-emerald-200/50 bg-emerald-50/40 px-3 py-2 text-xs font-medium text-emerald-700 hover:bg-emerald-100/30"
          >
            ひらく
          </button>
        </form>

        <div className="space-y-2">
          <p className="text-[11px] font-medium tracking-[0.2em] text-[var(--kt-color-text-muted)]">願いに近いもの</p>

          {tagsLoading ? (
            <p className="text-xs text-[var(--kt-color-text-muted)] opacity-70">ご利益タグを読み込み中…</p>
          ) : tagsError ? (
            <p className="text-xs text-rose-600">{tagsError}</p>
          ) : goriyakuTags.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {goriyakuTags.slice(0, 8).map((tag) => {
                const isActive = tag.name === activeTag;

                return (
                  <button
                    key={tag.id}
                    type="button"
                    aria-pressed={isActive}
                    onClick={() => onSelectTag(tag.name)}
                    className={[
                      "rounded-full border px-2.5 py-1 text-xs font-medium transition",
                      isActive
                        ? "border-emerald-200/70 bg-emerald-50/70 text-emerald-700"
                        : "border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] text-[var(--kt-color-text-secondary)] hover:bg-[var(--kt-color-background-subtle)] opacity-65",
                    ].join(" ")}
                  >
                    {tag.name}
                  </button>
                );
              })}
              {activeGoriyakuTag ? (
                <p className="text-xs text-emerald-700 opacity-70">
                  {activeGoriyakuTag.name}で表示中です。もう一度押すと解除できます。
                </p>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </details>
  );
}
