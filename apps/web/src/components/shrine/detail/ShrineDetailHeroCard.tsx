import Image from "next/image";

type Props = {
  title: string;
  imageUrl?: string | null;
};

/**
 * 一覧Heroは「候補を開かせる」ためのカード。
 * 詳細Heroは「意味宣言のあとに視覚補助を置く」ための軽い補助カード。
 * 同じ神社表示でも役割が違うため、詳細側では責務を絞った専用表示にする。
 */
export default function ShrineDetailHeroCard({ title, imageUrl = null }: Props) {
  const resolvedImageUrl = typeof imageUrl === "string" && imageUrl.trim().length > 0 ? imageUrl : null;

  return (
    <section className="pt-1">
      <article className="overflow-hidden rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] shadow-[var(--kt-shadow-medium)]">
        {/* Media slot is a visual aid only. With no image (Shrine API carries no
            image field; heroImageUrl falls back to a public goshuin photo, else
            null) we render nothing here rather than an empty fixed-height
            bg-slate-100 box — which reads as a bright empty panel in dark mode. */}
        {resolvedImageUrl ? (
          <div className="relative h-32 w-full bg-slate-100">
            <Image
              src={resolvedImageUrl}
              alt={title}
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, 448px"
            />
          </div>
        ) : null}

        <div className="p-4">
          <p className="text-sm font-semibold text-[var(--kt-color-text-primary)]">{title}</p>
        </div>
      </article>
    </section>
  );
}
