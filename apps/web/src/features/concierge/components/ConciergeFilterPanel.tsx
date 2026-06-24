"use client";

import { useState } from "react";

import type { GoriyakuTag, Element4 } from "@/features/concierge/sections/types";

type Props = {
  isOpen: boolean;
  title?: string;

  onClose: () => void;
  onApply: () => void;

  birthdate: string;
  onBirthdateChange: (v: string) => void;

  element4: Element4 | null;

  goriyakuTags: readonly GoriyakuTag[];
  suggestedTags: readonly GoriyakuTag[];
  selectedTagIds: readonly number[];
  onToggleTag: (tagId: number) => void;

  tagsLoading: boolean;
  tagsError: string | null;

  extraCondition: string;
  onExtraConditionChange: (v: string) => void;

  canApply?: boolean;
};

const QUICK_PRESET_GROUPS: readonly {
  title: string;
  description: string;
  items: readonly { label: string; value: string }[];
}[] = [
  {
    title: "体験スタイル",
    description: "どう過ごしたいかを、候補の並び方の参考にします。",
    items: [
      { label: "静かな時間を過ごしたい", value: "静かな雰囲気で、気持ちを落ち着けて整理できる場所がいい" },
      { label: "気分を切り替えたい", value: "気持ちを切り替えて、前向きになれる場所がいい" },
      { label: "自然を感じたい", value: "自然を感じながら、ゆっくり参拝できる場所がいい" },
      { label: "歴史や文化に触れたい", value: "歴史や文化を感じながら、意味を受け取れる場所がいい" },
    ],
  },
  {
    title: "実用条件",
    description: "無理なく行けるか、安心して過ごせるかの補助条件です。",
    items: [
      { label: "近場がいい", value: "できるだけ近い場所を優先して" },
      { label: "アクセスしやすい場所がいい", value: "駅から行きやすく、移動の負担が少ない場所がいい" },
      { label: "有名な神社が安心", value: "有名で定番感があり、安心して参拝しやすい場所がいい" },
      { label: "人混みを避けたい", value: "混雑しにくい、落ち着いた場所がいい" },
    ],
  },
  {
    title: "神社好き向け",
    description: "神社そのものの楽しみ方を、補助条件として加えます。",
    items: [
      { label: "由緒を知りたい", value: "由緒や背景を感じながら参拝できる場所がいい" },
      { label: "御朱印を楽しみたい", value: "御朱印も楽しみながら参拝できる場所がいい" },
      { label: "神話に触れたい", value: "神話や祀られている神様の文脈に触れられる場所がいい" },
      { label: "境内をゆっくり歩きたい", value: "境内をゆっくり歩きながら、落ち着いて過ごせる場所がいい" },
    ],
  },
];

const INITIAL_VISIBLE_GORIYAKU_COUNT = 4;

function mergeExtra(prev: string, add: string) {
  const p = (prev || "").trim();
  const a = (add || "").trim();
  if (!a) return p;
  if (!p) return a;
  if (p.includes(a)) return p;
  return `${p}\n${a}`;
}

export default function ConciergeFilterPanel({
  isOpen,
  title = "希望を補足する",
  onClose,
  onApply,
  birthdate,
  onBirthdateChange,
  element4,
  goriyakuTags,
  suggestedTags,
  selectedTagIds,
  onToggleTag,
  tagsLoading,
  tagsError,
  extraCondition,
  onExtraConditionChange,
  canApply = false,
}: Props) {
  const [showAllGoriyakuTags, setShowAllGoriyakuTags] = useState(false);

  if (!isOpen) return null;

  const selected = new Set(selectedTagIds);
  const visibleGoriyakuTags = showAllGoriyakuTags
    ? goriyakuTags
    : goriyakuTags.slice(0, INITIAL_VISIBLE_GORIYAKU_COUNT);
  const hiddenGoriyakuCount = Math.max(goriyakuTags.length - INITIAL_VISIBLE_GORIYAKU_COUNT, 0);

  return (
    <section className="mx-auto w-full max-w-md min-w-0 space-y-2 rounded-xl border border-slate-200 bg-slate-50/60 p-2 sm:max-h-none">
      <div className="flex items-center justify-between">
        <div className="text-[10px] font-semibold text-slate-600">{title}</div>
        <button type="button" className="text-[11px] font-semibold text-slate-600 hover:underline" onClick={onClose}>
          閉じる
        </button>
      </div>

      <div className="grid gap-0.5 rounded-xl border border-slate-200 bg-white p-2">
        <div className="space-y-0.5">
          <div className="text-[10px] font-semibold text-slate-500">誕生日（任意）</div>
          <div className="text-[10px] text-slate-400">相性候補を見るための任意の補助情報です</div>
          <input
            type="date"
            value={birthdate}
            onChange={(e) => onBirthdateChange(e.target.value)}
            className="w-full rounded-xl border px-3 py-1.5 text-sm"
          />
        </div>

        {element4 ? (
          <div className="text-[11px] text-slate-500">
            誕生日から見た補助傾向: <span className="font-semibold text-slate-700">{element4}</span>
          </div>
        ) : null}

        <div className="space-y-2">
          <div>
            <div className="text-[10px] font-semibold text-slate-600">参拝スタイル</div>
            <p className="mt-0.5 text-[10px] leading-4 text-slate-400">
              相談テーマを主軸にしたまま、過ごし方や行きやすさを補助条件として加えます。
            </p>
          </div>

          {QUICK_PRESET_GROUPS.map((group) => (
            <div key={group.title} className="space-y-1 rounded-lg border border-slate-100 bg-slate-50/60 p-2">
              <div>
                <div className="text-[10px] font-semibold text-slate-600">{group.title}</div>
                <p className="mt-0.5 text-[10px] leading-4 text-slate-400">{group.description}</p>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {group.items.map((p) => (
                  <button
                    key={p.label}
                    type="button"
                    className="rounded-full border bg-white px-3 py-1 text-xs font-semibold hover:bg-slate-50"
                    onClick={() => onExtraConditionChange(mergeExtra(extraCondition, p.value))}
                    title={p.value}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {element4 && suggestedTags.length > 0 ? (
          <div className="space-y-0.5">
            <div className="text-[10px] font-semibold text-slate-500">相性から見た候補</div>
            <p className="text-[10px] leading-4 text-slate-400">
              誕生日情報をもとにした補助候補です。相談テーマとの一致を優先します。
            </p>
            <div className="flex flex-wrap gap-1.5">
              {suggestedTags.map((t) => {
                const on = selected.has(t.id);
                return (
                  <button
                    key={t.id}
                    type="button"
                    className={`rounded-full border px-3 py-1 text-xs font-semibold ${
                      on ? "border-emerald-600 bg-emerald-50" : "bg-white"
                    }`}
                    onClick={() => onToggleTag(t.id)}
                  >
                    {t.name}
                  </button>
                );
              })}
            </div>
          </div>
        ) : null}
      </div>

      {tagsLoading || tagsError || visibleGoriyakuTags.length > 0 || hiddenGoriyakuCount > 0 ? (
        <div className="space-y-1 rounded-xl border border-slate-200 bg-white p-2">
          <div>
            <div className="text-[10px] font-semibold text-slate-600">ご利益・願いに近いもの</div>
            <p className="mt-0.5 text-[10px] leading-4 text-slate-400">
              相談テーマを主軸にしつつ、願いたいことに近いものを補助条件として使います。
            </p>
          </div>
          {tagsError ? <div className="text-xs text-red-600">{tagsError}</div> : null}
          {tagsLoading ? <div className="text-xs text-slate-500">読み込み中…</div> : null}

          {visibleGoriyakuTags.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {visibleGoriyakuTags.map((t) => {
                const on = selected.has(t.id);
                return (
                  <button
                    key={t.id}
                    type="button"
                    className={`rounded-full border px-3 py-1 text-xs font-semibold ${
                      on ? "border-emerald-600 bg-emerald-50" : "bg-white"
                    }`}
                    onClick={() => onToggleTag(t.id)}
                  >
                    {t.name}
                  </button>
                );
              })}
            </div>
          ) : null}

          {hiddenGoriyakuCount > 0 ? (
            <button
              type="button"
              className="text-left text-[11px] font-semibold text-slate-500 hover:text-slate-700 hover:underline"
              onClick={() => setShowAllGoriyakuTags((prev) => !prev)}
            >
              {showAllGoriyakuTags ? "折りたたむ" : `他${hiddenGoriyakuCount}件を表示`}
            </button>
          ) : null}
        </div>
      ) : null}

      <div className="flex justify-end gap-2 border-t border-slate-200 bg-slate-50/95 pt-1.5 pb-0.5">
        <button type="button" className="rounded-xl border px-3 py-1.5 text-sm font-semibold" onClick={onClose}>
          キャンセル
        </button>

        <button
          type="button"
          onClick={() => {
            console.log("FILTER_PANEL_APPLY_CLICK", { canApply });
            onApply();
          }}
          disabled={false}
          style={{ pointerEvents: "auto" }}
          className={[
            "relative z-20 rounded-xl px-3 py-1.5 text-sm font-semibold transition",
            canApply
              ? "bg-emerald-600 text-white hover:bg-emerald-700"
              : "bg-slate-200 text-slate-400 cursor-not-allowed",
          ].join(" ")}
        >
          この内容に反映する
        </button>
      </div>
    </section>
  );
}
