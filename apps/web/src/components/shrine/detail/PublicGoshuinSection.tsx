import Link from "next/link";
import Image from "next/image";
import DetailSection from "@/components/shrine/DetailSection";

export type PublicGoshuinItem = {
  id: number;
  title?: string | null;
  created_at?: string;
  image_url?: string | null;
};

export default function PublicGoshuinSection({
  items,
  addGoshuinHref,
  sendingLabel,
  limit,
  seeAllHref,
  seeAllLabel = "すべて見る",
}: {
  items: PublicGoshuinItem[];
  addGoshuinHref?: string | null;
  sendingLabel?: string;
  limit?: number;
  seeAllHref?: string | null;
  seeAllLabel?: string;
}) {
  const list = Array.isArray(items) ? items : [];
  const n = typeof limit === "number" && Number.isFinite(limit) && limit > 0 ? Math.trunc(limit) : list.length;

  const shown = list.slice(0, n);
  const hasMore = list.length > shown.length;
  const moreCount = hasMore ? list.length - shown.length : 0;

  const isEmpty = shown.length === 0;

  return (
    <DetailSection
      title="この神社の御朱印"
      right={
        !isEmpty ? (
          <div className="relative z-50 flex flex-wrap items-center justify-end gap-2">
            {hasMore && seeAllHref ? (
              <Link href={seeAllHref} className="text-xs font-semibold text-[var(--kt-color-text-secondary)] hover:underline">
                {seeAllLabel}
                {moreCount > 0 ? <span className="ml-1 text-[var(--kt-color-text-muted)]">（他{moreCount}件）</span> : null}
              </Link>
            ) : null}

            {addGoshuinHref ? (
              <Link
                href={addGoshuinHref}
                className="relative z-50 rounded-lg bg-[var(--kt-color-action-primary)] px-3 py-1.5 text-xs font-semibold text-[var(--kt-color-action-primary-text)]"
              >
                この神社に御朱印を残す
              </Link>
            ) : null}
          </div>
        ) : null
      }
    >
      <p className="text-xs text-[var(--kt-color-text-muted)]">お気に入りの御朱印を、この神社に残せます。</p>

      {sendingLabel ? <p className="mt-2 text-xs text-[var(--kt-color-text-muted)]">{sendingLabel}</p> : null}

      {isEmpty ? (
        <div className="mt-3 rounded-[var(--kt-radius-panel)] border bg-emerald-50 p-5 text-center">
          <p className="text-sm font-semibold text-[var(--kt-color-text-secondary)]">この神社、まだ誰も御朱印を残していません</p>
          <p className="mt-1 text-xs text-[var(--kt-color-text-muted)]">あなたが最初の御朱印を残せます。</p>

          {addGoshuinHref ? (
            <Link
              href={addGoshuinHref}
              className="mt-4 inline-flex items-center justify-center rounded-lg bg-[var(--kt-color-action-primary)] px-5 py-2.5 text-sm font-semibold text-[var(--kt-color-action-primary-text)]"
            >
              この神社に御朱印を残す
            </Link>
          ) : null}
        </div>
      ) : (
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {shown.map((g, idx) => {
            const isLead = idx === 0;

            return (
              <div
                key={g.id}
                className={[
                  "overflow-hidden rounded-[var(--kt-radius-panel)] border bg-[var(--kt-color-surface-default)]",
                  isLead ? "col-span-2 border-[var(--kt-color-border-default)] shadow-[var(--kt-shadow-medium)]" : "border-slate-200/80",
                ].join(" ")}
              >
                <div
                  className={[
                    isLead ? "aspect-[4/3]" : "aspect-[4/5]",
                    "flex items-center justify-center bg-slate-100 text-xs text-slate-400",
                  ].join(" ")}
                >
                  {g.image_url ? (
                    <Image
                      src={g.image_url}
                      alt={g.title ?? "goshuin"}
                      width={600}
                      height={750}
                      className="h-full w-full object-cover"
                      unoptimized
                    />
                  ) : (
                    <span>画像未登録</span>
                  )}
                </div>

                <div className={isLead ? "p-3" : "p-2"}>
                  <p
                    className={
                      isLead
                        ? "truncate text-sm font-semibold text-slate-800"
                        : "truncate text-xs text-[var(--kt-color-text-secondary)]"
                    }
                  >
                    {(g.title ?? "").trim() || "（タイトルなし）"}
                  </p>
                  {g.created_at ? (
                    <p
                      className={
                        isLead
                          ? "mt-1 truncate text-xs text-[var(--kt-color-text-muted)]"
                          : "truncate text-[11px] text-[var(--kt-color-text-muted)]"
                      }
                    >
                      {g.created_at}
                    </p>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </DetailSection>
  );
}
