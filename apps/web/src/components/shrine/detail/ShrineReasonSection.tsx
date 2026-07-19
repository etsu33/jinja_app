import type { DetailReasonSection } from "@/components/shrine/detail/types";

/**
 * ① 推薦判断
 * - 主理由
 * - 補助理由
 * - 1位理由
 *
 * rule:
 * - ラベルの羅列ではなく、説明文として読める形で表示する
 * - group.title を見出しとして使い、group.items は本文として縦に表示する
 * - 推薦判断の説明を行い、状態整理や行動意味は混ぜない
 */
export default function ShrineReasonSection({ section }: { section: DetailReasonSection }) {
  return (
    <section className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4">
      <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">{section.heading}</h2>

      <div className="mt-3 space-y-4">
        {section.groups.map((group) => (
          <div key={group.title} className="space-y-2">
            <h3 className="text-sm font-medium text-[var(--kt-color-text-secondary)]">{group.title}</h3>
            <div className="space-y-2">
              {group.items.map((item) => (
                <p
                  key={`${group.title}:${item}`}
                  className="text-sm leading-7 text-[var(--kt-color-text-secondary)]"
                >
                  {item}
                </p>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
