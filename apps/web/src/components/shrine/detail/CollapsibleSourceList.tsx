// apps/web/src/components/shrine/detail/CollapsibleSourceList.tsx
import type { ShrineKnowledgeSource } from "@/lib/api/types";

// 見どころ・由緒・歴史の出典は各ブロック（カード）に「出典（N件）」の1行で出し、押すとそのブロックの出典が開く（折りたたみ）。
// 根拠を読んだ事実のすぐ横で開けるようにしつつ、画面の情報量を抑える。
// 決定：ドライブ「KAMI MUSUBI 文章と見どころの選定・表現ルール v1.0（案）」6章⑤（見どころ 2026-11-26、由緒・歴史 2026-11-27 えつこさん）。
export default function CollapsibleSourceList({ sources }: { sources: ShrineKnowledgeSource[] }) {
  if (sources.length === 0) return null;

  return (
    <details className="group mt-3 border-t border-[var(--kt-color-border-default)] pt-1">
      <summary className="flex min-h-[44px] cursor-pointer list-none items-center gap-1 text-[11px] font-semibold tracking-[0.04em] text-[var(--kt-color-text-muted)] [&::-webkit-details-marker]:hidden">
        <span aria-hidden="true" className="inline-block transition-transform group-open:rotate-90">
          ›
        </span>
        出典（{sources.length}件）
      </summary>
      <ul className="mb-1 flex flex-wrap gap-x-3 gap-y-1">
        {sources.map((source, index) => {
          const label = source.title || source.publisher || "出典";
          return (
            <li key={`${source.id}:${index}`}>
              {source.url ? (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="text-xs text-[var(--kt-color-text-muted)] underline underline-offset-2"
                >
                  {label}
                </a>
              ) : (
                <span className="text-xs text-[var(--kt-color-text-muted)]">{label}</span>
              )}
            </li>
          );
        })}
      </ul>
    </details>
  );
}
