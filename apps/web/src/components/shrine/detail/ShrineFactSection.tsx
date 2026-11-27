// apps/web/src/components/shrine/detail/ShrineFactSection.tsx
import type { DetailFactDeity, DetailFactHistoryItem, DetailFactSection } from "@/components/shrine/detail/types";
import type { ShrineKnowledgeSource } from "@/lib/api/types";
import CollapsibleSourceList from "@/components/shrine/detail/CollapsibleSourceList";
import ShrineHighlightAnchorLink from "@/components/shrine/detail/ShrineHighlightAnchorLink";
import { groupShrineHistoryFacts } from "@/lib/shrine/buildShrineFactSection";
import { shrineHighlightAnchorId, shrineHistoryAnchorId } from "@/lib/shrine/buildShrineHighlightSection";

type Props = {
  section: DetailFactSection;
  // 見どころへのリンクの計測に使う（Highlights PR-5）。無くても表示は変わらない。
  shrineId?: number | null;
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

// 1枚の歴史カードに出す出典。同じカードの中で同じURL（URLが無ければ同じid）が重なったときだけ1件にまとめる。
// カードをまたいだまとめはしない — どの出典がどの事実の根拠かを、その事実のカードで読めるようにするため
// （ドライブ「文章と見どころの選定・表現ルール v1.0（案）」6章⑤、2026-11-27 えつこさん決定）。
function cardSources(history: DetailFactHistoryItem): ShrineKnowledgeSource[] {
  const seen = new Set<string>();
  const collected: ShrineKnowledgeSource[] = [];

  for (const source of history.sources ?? []) {
    const dedupeKey = source.url ? `url:${source.url}` : `id:${source.id}`;
    if (seen.has(dedupeKey)) continue;
    seen.add(dedupeKey);
    collected.push(source);
  }

  return collected;
}

// 1 Fact = 1 card。Presentation Grouping（groupShrineHistoryFacts）はこのcardの内容・identity・
// sourcesを一切変更せず、どのgroupの下に置くかだけを決める。showTypeLabelは、groupの見出しが
// 既にhistory_type_labelを示している場合（グルーピング済みFact）にラベルの二重表示を避けるため
// falseにする。disputedなFact（groupingされない、既存の個別表示のまま）ではtrueのままにする。
function HistoryCard({
  history,
  showTypeLabel,
  shrineId,
}: {
  history: DetailFactHistoryItem;
  showTypeLabel: boolean;
  shrineId: number | null;
}) {
  const highlightLinks = history.highlightLinks ?? [];
  return (
    <div
      id={history.id != null ? shrineHistoryAnchorId(history.id) : undefined}
      className="scroll-mt-24 rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] p-3"
    >
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
      {/* Highlights PR-5: この話を境内のどこで確かめられるか。見どころの節へ移る。 */}
      {highlightLinks.length > 0 ? (
        <div className="mt-2 flex flex-wrap items-baseline gap-x-2 gap-y-1">
          <span className="text-xs font-semibold text-[var(--kt-color-text-muted)]">現地で見られる場所：</span>
          {highlightLinks.map((link) => (
            <ShrineHighlightAnchorLink
              key={link.id}
              targetId={shrineHighlightAnchorId(link.id)}
              shrineId={shrineId}
              highlightId={link.id}
              direction="history_to_highlight"
              className="text-xs text-[var(--kt-color-action-primary)] underline underline-offset-2"
            >
              {link.name}
            </ShrineHighlightAnchorLink>
          ))}
        </div>
      ) : null}
      <CollapsibleSourceList sources={cardSources(history)} />
    </div>
  );
}

function historyCardKey(history: DetailFactHistoryItem, index: number): string {
  return history.id != null ? String(history.id) : `${history.title}:${index}`;
}

// Presentation Grouping（docs/knowledge/shrine-knowledge-contract.md「Presentation Groupingの契約」）:
// 既存canonical history_typeが完全一致するFact群を、Fact本文・identity・sourcesを一切変えずに
// 共通見出しの下へ表示する。disputedなFactはグルーピングせず、既存の個別表示のまま残す。
function HistoryList({ histories, shrineId }: { histories: DetailFactHistoryItem[]; shrineId: number | null }) {
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
                <HistoryCard
                  key={historyCardKey(history, index)}
                  history={history}
                  showTypeLabel={false}
                  shrineId={shrineId}
                />
              ))}
            </div>
          </div>
        ))}
        {disputed.length > 0 ? (
          <div className="space-y-3">
            {disputed.map((history, index) => (
              <HistoryCard key={historyCardKey(history, index)} history={history} showTypeLabel shrineId={shrineId} />
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function ShrineFactSection({ section, shrineId = null }: Props) {
  const hasDeities = section.deities.length > 0;
  const hasHistories = section.histories.length > 0;

  if (!hasDeities && !hasHistories) return null;

  return (
    <section className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4">
      <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">{section.heading}</h2>

      <div className="mt-4 space-y-4">
        {hasDeities ? <DeityList deities={section.deities} /> : null}
        {hasHistories ? <HistoryList histories={section.histories} shrineId={shrineId} /> : null}
      </div>
    </section>
  );
}
