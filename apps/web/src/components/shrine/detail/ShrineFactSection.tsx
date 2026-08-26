// apps/web/src/components/shrine/detail/ShrineFactSection.tsx
import type { DetailFactDeity, DetailFactHistoryItem, DetailFactSection } from "@/components/shrine/detail/types";
import type { ShrineKnowledgeSource } from "@/lib/api/types";
import { groupShrineHistoryFacts } from "@/lib/shrine/buildShrineFactSection";

type Props = {
  section: DetailFactSection;
};

// disputed Factに付与する状態ラベル。文言はここ1箇所でのみ定義する（PR-C4B2）。
// verification_statusの内部名（"disputed"等）はユーザーへ露出しない。
// Source同士が明示的に矛盾していることは現行Modelから判定できないため、
// 「矛盾しています」「誤り」等の断定語は使わず、中立的な表現に留める。
const DISPUTED_FACT_LABEL = "異なる見解を含む情報";

function DisputedBadge() {
  return (
    <span className="inline-flex items-center rounded-[var(--kt-radius-pill)] border border-[var(--kt-color-border-default)] px-1.5 py-0.5 text-[10px] font-medium leading-none text-[var(--kt-color-text-muted)]">
      {DISPUTED_FACT_LABEL}
    </span>
  );
}

function DeityList({ deities }: { deities: DetailFactDeity[] }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-[var(--kt-color-text-primary)]">御祭神</h3>
      <ul className="mt-2 flex flex-wrap gap-2">
        {deities.map((deity, index) => (
          <li
            key={`${deity.display_name}:${index}`}
            className="inline-flex items-center gap-1.5 rounded-[var(--kt-radius-pill)] bg-[var(--kt-color-background-subtle)] px-3 py-1 text-sm text-[var(--kt-color-text-secondary)]"
          >
            {deity.display_name}
            {deity.displayState === "disputed" ? <DisputedBadge /> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

// Section末尾へ集約表示するSource一覧。dedupe基準はurl（非空の場合）、urlを持たないSourceは
// id基準でdedupeする。異なるSource（url/idが異なる）は失わない — 同一urlのみを1件へまとめる。
function collectSectionSources(histories: DetailFactHistoryItem[]): ShrineKnowledgeSource[] {
  const seen = new Set<string>();
  const collected: ShrineKnowledgeSource[] = [];

  for (const history of histories) {
    for (const source of history.sources ?? []) {
      const dedupeKey = source.url ? `url:${source.url}` : `id:${source.id}`;
      if (seen.has(dedupeKey)) continue;
      seen.add(dedupeKey);
      collected.push(source);
    }
  }

  return collected;
}

function SourceList({ sources }: { sources: ShrineKnowledgeSource[] }) {
  if (sources.length === 0) return null;

  return (
    <div className="mt-3 border-t border-[var(--kt-color-border-default)] pt-3">
      <h4 className="text-[11px] font-semibold tracking-[0.04em] text-[var(--kt-color-text-muted)]">出典</h4>
      <ul className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1">
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
    </div>
  );
}

// 1 Fact = 1 card。Presentation Grouping（groupShrineHistoryFacts）はこのcardの内容・identity・
// sourcesを一切変更せず、どのgroupの下に置くかだけを決める。showTypeLabelは、groupの見出しが
// 既にhistory_type_labelを示している場合（グルーピング済みFact）にラベルの二重表示を避けるため
// falseにする。disputedなFact（groupingされない、既存の個別表示のまま）ではtrueのままにする。
function HistoryCard({ history, showTypeLabel }: { history: DetailFactHistoryItem; showTypeLabel: boolean }) {
  return (
    <div className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] p-3">
      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
        {showTypeLabel ? (
          <span className="text-[11px] font-semibold tracking-[0.04em] text-[var(--kt-color-text-muted)]">
            {history.history_type_label}
          </span>
        ) : null}
        {history.title ? (
          <h4 className="text-sm font-semibold text-[var(--kt-color-text-primary)]">{history.title}</h4>
        ) : null}
        {history.period_text ? (
          <span className="text-xs text-[var(--kt-color-text-muted)]">{history.period_text}</span>
        ) : null}
        {history.displayState === "disputed" ? <DisputedBadge /> : null}
      </div>
      {history.content ? (
        <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-[var(--kt-color-text-secondary)]">
          {history.content}
        </p>
      ) : null}
    </div>
  );
}

function historyCardKey(history: DetailFactHistoryItem, index: number): string {
  return history.id != null ? String(history.id) : `${history.title}:${index}`;
}

// Presentation Grouping（docs/knowledge/shrine-knowledge-contract.md「Presentation Groupingの契約」）:
// 既存canonical history_typeが完全一致するFact群を、Fact本文・identity・sourcesを一切変えずに
// 共通見出しの下へ表示する。disputedなFactはグルーピングせず、既存の個別表示のまま残す。
function HistoryList({ histories }: { histories: DetailFactHistoryItem[] }) {
  const { groups, disputed } = groupShrineHistoryFacts(histories);

  return (
    <div>
      <h3 className="text-sm font-semibold text-[var(--kt-color-text-primary)]">由緒・歴史</h3>
      <div className="mt-3 space-y-4">
        {groups.map((group) => (
          <div key={group.historyType}>
            <h4 className="text-[11px] font-semibold tracking-[0.04em] text-[var(--kt-color-text-muted)]">
              {group.label}
            </h4>
            <div className="mt-2 space-y-3">
              {group.items.map((history, index) => (
                <HistoryCard key={historyCardKey(history, index)} history={history} showTypeLabel={false} />
              ))}
            </div>
          </div>
        ))}
        {disputed.length > 0 ? (
          <div className="space-y-3">
            {disputed.map((history, index) => (
              <HistoryCard key={historyCardKey(history, index)} history={history} showTypeLabel />
            ))}
          </div>
        ) : null}
      </div>
      <SourceList sources={collectSectionSources(histories)} />
    </div>
  );
}

export default function ShrineFactSection({ section }: Props) {
  const hasDeities = section.deities.length > 0;
  const hasHistories = section.histories.length > 0;

  if (!hasDeities && !hasHistories) return null;

  return (
    <section className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4">
      <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">{section.heading}</h2>

      <div className="mt-4 space-y-4">
        {hasDeities ? <DeityList deities={section.deities} /> : null}
        {hasHistories ? <HistoryList histories={section.histories} /> : null}
      </div>
    </section>
  );
}
