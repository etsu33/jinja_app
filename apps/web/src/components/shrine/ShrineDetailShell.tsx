// apps/web/src/components/shrine/ShrineDetailShell.tsx
import type { ReactNode } from "react";
import Link from "next/link";
import type { Close } from "@/lib/navigation/shrineClose";
import ShrineCloseLink from "@/components/shrine/ShrineCloseLink";
import { LABELS } from "@/lib/ui/labels";
import DetailSection from "@/components/shrine/DetailSection";
import GoogleMapRouteLink from "@/components/shrine/GoogleMapRouteLink";
import type { DirectionRouteContext } from "@/lib/analytics/directionRouteContext";
import type { RecommendationAnalyticsProvenance } from "../../../../../packages/shared/recommendationAnalyticsProvenance";

type SaveAction = {
  shrineId: number;
  nextPath: string;
  node: ReactNode; // 例: <ShrineSaveButton ... />
};

type Props = {
  title: string;
  subtitle?: string | null;
  close: Close;
  shrineId?: number | string | null;

  // CTA
  addGoshuinHref?: string | null;
  googleDirHref?: string | null;
  googleDirLabel?: string; // 任意で上書き可
  googleDirFallbackText?: string;

  saveAction?: SaveAction | null;

  children?: ReactNode;

  // ✅ concierge 等で「操作」を消すためのスイッチ
  hideActions?: boolean;

  ctx?: string | null;
  tid?: string | number | null;
  historyTheme?: string | null;
  directionRouteContext?: DirectionRouteContext | null;
  analyticsProvenance?: RecommendationAnalyticsProvenance;
  recommendationInstanceId?: string | null;
};

export default function ShrineDetailShell({
  title,
  subtitle = null,
  close,
  addGoshuinHref = null,
  googleDirHref = null,
  googleDirLabel = LABELS.googleDirections,
  googleDirFallbackText: _googleDirFallbackText,
  saveAction = null,
  children,
  hideActions = false,

  shrineId = null,
  ctx = null,
  tid = null,
  historyTheme = null,
  directionRouteContext = null,
  analyticsProvenance,
  recommendationInstanceId = null,
}: Props) {
  const shouldShowActions = !hideActions && Boolean(googleDirHref || saveAction?.node || addGoshuinHref);

  return (
    <main className="mx-auto min-h-[calc(100vh-64px)] max-w-md space-y-4 p-4 lg:max-w-2xl">
      {/* ✅ Close をヘッダー左固定 */}
      <header className="flex items-center justify-between">
        <div className="shrink-0">
          <ShrineCloseLink close={close} />
        </div>

        <div className="min-w-0 flex-1 px-2 text-center">
          <div className="truncate text-sm font-semibold text-[var(--kt-color-text-primary)]">{title}</div>
          {subtitle ? <div className="truncate text-[11px] text-[var(--kt-color-text-muted)]">{subtitle}</div> : null}
        </div>

        {/* 右側はレイアウト固定のため空 */}
        <div className="w-[64px]" />
      </header>

      {/* ✅ 操作は「何かできる」時だけ表示 + concierge では強制非表示 */}
      {shouldShowActions ? (
        <DetailSection title="操作">
          <div className="grid gap-2">
            {/* primary: 経路案内 */}
            {googleDirHref ? (
              <GoogleMapRouteLink
                href={googleDirHref}
                label={googleDirLabel}
                shrineId={shrineId}
                ctx={ctx}
                tid={tid}
                historyTheme={historyTheme}
                directionRouteContext={directionRouteContext}
                analyticsProvenance={analyticsProvenance}
                recommendationInstanceId={recommendationInstanceId}
                className="inline-flex min-h-[44px] w-full items-center justify-center rounded-[var(--kt-radius-panel)] bg-slate-900 px-4 py-3 text-sm font-semibold text-[var(--kt-color-text-inverse)] hover:bg-slate-800"
              />
            ) : null}

            {/* secondary: 保存 */}
            {saveAction?.node ? <div>{saveAction.node}</div> : null}

            {/* tertiary: 御朱印追加 */}
            {addGoshuinHref ? (
              <Link
                href={addGoshuinHref}
                className="inline-flex min-h-[44px] w-full items-center justify-center rounded-[var(--kt-radius-panel)] border bg-[var(--kt-color-surface-default)] px-4 py-3 text-sm font-semibold text-[var(--kt-color-text-primary)] hover:bg-[var(--kt-color-background-subtle)]"
              >
                {LABELS.addGoshuin}
              </Link>
            ) : null}
          </div>
        </DetailSection>
      ) : null}

      {children}
    </main>
  );
}
