"use client";

// Compass MVP client (docs/product/compass-product-contract.md,
// docs/product/compass-mvp-runtime-contract.md, Phase 5 brief).
//
// No free-text consultation input here (Phase 5 brief Section 4) -- that
// belongs to Concierge. This screen collects only: purpose (chip select),
// origin (reused OriginSelector), birthdate (date input), then calls the
// Compass BFF and renders one of the backend's 5 fail-safe states plus
// this component's own pre-submit states (birthdate/origin missing).
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import DetailSection from "@/components/shrine/DetailSection";
import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import type { UserOrigin } from "../../../../../packages/shared/userOrigin";
import { toOriginPayload } from "../../../../../packages/shared/userOrigin";
import CompassDirectionVisual from "./components/CompassDirectionVisual";
import CompassOriginSummary from "./components/CompassOriginSummary";
import CompassPurposeSelector from "./components/CompassPurposeSelector";
import CompassRecommendationsSection from "./components/CompassRecommendationsSection";
import type {
  CompassDirectionRuntime,
  CompassPurpose,
  CompassRecommendationsResponse,
  CompassUiState,
} from "./types";

// Compass lifecycle analytics (PR-A,
// docs/audit/compass-analytics-contract-readiness.md §6-10). Only the
// backend orchestrator's own state strings are used -- never renamed for
// analytics convenience -- plus the frontend-only "backend_error" bucket
// already used by this component's own uiState for network failures and
// non-400 error responses.
type CompassResultState =
  | "invalid_purpose"
  | "direction_filter_unavailable"
  | "no_common_direction"
  | "direction_zero_candidates"
  | "evidence_zero_candidates"
  | "recommendation_success"
  | "backend_error";

function formatTargetMonth(date: Date): string {
  return `${date.getFullYear()}年${date.getMonth() + 1}月`;
}

// Product Contract Section 2.2-7 / Runtime Contract Section 5-1 (#2508
// Option C, audited in docs/audit/compass-monthly-fallback-ui-analytics-boundary.md
// Section 9): a Monthly Fallback direction must never be presented as if it
// were annual/monthly agreement. The backend's direction_context.note is a
// fixed constant identical for both calculationMethod values (Signal-to-
// Explanation Rule violation for the fallback case), so this copy is
// derived here from calculationMethod instead of rendering note directly.
function getDirectionNote(calculationMethod: CompassDirectionRuntime["calculationMethod"]): string {
  if (calculationMethod === "monthly_kyusei_v1") {
    return "年盤と月盤で重なる方位がないため、今月の月盤を参考にした方位です。日盤は使用していません。";
  }
  return "年盤と月盤の両方で重なる、今月の参考方位です。日盤は使用していません。";
}

export default function CompassClient() {
  const [now] = useState(() => new Date());
  const [purpose, setPurpose] = useState<CompassPurpose | null>(null);
  const [birthdate, setBirthdate] = useState("");
  const [origin, setOrigin] = useState<UserOrigin | null>(null);
  const [deviceError, setDeviceError] = useState<string | null>(null);
  const [attempted, setAttempted] = useState(false);
  const [uiState, setUiState] = useState<CompassUiState>("initial");
  const [result, setResult] = useState<CompassRecommendationsResponse | null>(null);

  const searchParams = useSearchParams();
  const entryTrackedRef = useRef(false);

  useEffect(() => {
    if (entryTrackedRef.current) return;
    entryTrackedRef.current = true;

    trackSearchEvent("compass_entry", {
      referrer_source: searchParams.get("ref") === "home" ? "home" : "direct",
    });
    // Fires once for the actual Compass entry only -- entryTrackedRef guards
    // against React re-render/StrictMode double-invocation the same way
    // ShrineDetailViewTracker.tsx does for shrine_detail_view.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const trackCompassResult = (
    resultState: CompassResultState,
    recommendationCount: number | null = null,
    recommendationInstanceId: string | null = null,
  ) => {
    trackSearchEvent("compass_result", {
      result_state: resultState,
      purpose,
      origin_mode: origin?.source ?? null,
      has_birthdate: true,
      recommendation_count: recommendationCount,
      recommendationInstanceId,
    });
  };

  const useDevice = () => {
    setDeviceError(null);
    if (!("geolocation" in navigator)) {
      setDeviceError("この端末では現在地を取得できません。駅名・住所から指定してください。");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setOrigin({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          source: "device",
          accuracy: "precise",
        });
      },
      () => {
        setDeviceError("現在地を取得できませんでした。駅名・住所から指定してください。");
      },
    );
  };

  const missingBirthdate = attempted && !birthdate.trim();
  const missingOrigin = attempted && !origin;
  const missingPurpose = attempted && !purpose;

  const handleSubmit = async () => {
    setAttempted(true);
    if (!purpose || !birthdate.trim() || !origin) {
      return;
    }

    setUiState("loading");
    setResult(null);

    try {
      const res = await fetch("/api/compass/recommendations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          purpose,
          birthdate: birthdate.trim(),
          origin: toOriginPayload(origin),
        }),
      });

      if (!res.ok && res.status !== 400) {
        setUiState("backend_error");
        trackCompassResult("backend_error");
        return;
      }

      const body = (await res.json()) as CompassRecommendationsResponse;
      setResult(body);
      setUiState(body.state);
      trackCompassResult(
        body.state,
        body.state === "recommendation_success" ? (body.recommendations?.length ?? 0) : null,
        body.recommendation_instance_id,
      );
    } catch {
      setUiState("backend_error");
      trackCompassResult("backend_error");
    }
  };

  const isLoading = uiState === "loading";
  const directionContext = result?.direction_context ?? null;

  return (
    <div className="mx-auto w-full max-w-2xl space-y-6 px-4 py-8">
      {/* DetailSection titles render as h2 (shared component, matches
          Concierge/Shrine Detail's existing outline); this page-level h1
          is sr-only so the visual heading stays exactly as designed while
          giving the document a correct heading hierarchy for screen readers
          (Phase 6 QA finding, docs/audit/compass-full-experience-qa.md). */}
      <h1 className="sr-only">今月の参拝コンパス</h1>
      <DetailSection title="今月の参拝コンパス" variant="primary" right={formatTargetMonth(now)}>
        <p className="text-sm leading-6 text-[var(--kt-color-text-secondary)]">
          今月の流れと目的から、向かう方向と参拝候補を見つけます。
        </p>
      </DetailSection>

      <DetailSection title="目的と出発地点" variant="secondary">
        <div className="space-y-5">
          <div className="space-y-1.5">
            <CompassPurposeSelector value={purpose} onChange={setPurpose} />
            {missingPurpose ? (
              <p role="alert" className="text-sm text-[var(--kt-color-status-error)]">
                目的を選択してください。
              </p>
            ) : null}
          </div>

          <CompassOriginSummary
            origin={origin}
            onChange={setOrigin}
            onUseDevice={useDevice}
            deviceError={deviceError}
          />
          {missingOrigin ? (
            <p role="alert" className="text-sm text-[var(--kt-color-status-error)]">
              出発地点を選択してください。
            </p>
          ) : null}

          <div className="space-y-1.5">
            <label htmlFor="compass-birthdate" className="text-sm font-medium text-[var(--kt-color-text-secondary)]">
              生年月日（方位計算に使用）
            </label>
            <input
              id="compass-birthdate"
              type="date"
              value={birthdate}
              onChange={(event) => setBirthdate(event.target.value)}
              className="min-h-11 w-full rounded-[var(--kt-radius-control)] border border-[var(--kt-color-border-default)] px-3 py-2 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600"
            />
            {missingBirthdate ? (
              <p role="alert" className="text-sm text-[var(--kt-color-status-error)]">
                生年月日を入力してください。
              </p>
            ) : null}
          </div>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={isLoading}
            className="min-h-11 w-full rounded-[var(--kt-radius-pill)] bg-[var(--kt-color-action-primary)] px-4 py-2.5 text-sm font-semibold text-[var(--kt-color-action-primary-text)] transition hover:bg-[var(--kt-color-action-primary-hover)] disabled:bg-[var(--kt-color-action-disabled)] disabled:text-[var(--kt-color-text-muted)]"
          >
            {isLoading ? "確認しています…" : "今月の方向を確認する"}
          </button>
        </div>
      </DetailSection>

      {directionContext ? (
        <DetailSection title="今月、意識したい方向" variant="secondary">
          <div className="space-y-3">
            <CompassDirectionVisual referenceDirections={directionContext.referenceDirections} />
            <p className="text-center text-xs text-[var(--kt-color-text-muted)]">
              {getDirectionNote(directionContext.calculationMethod)}（参考情報です）
            </p>
          </div>
        </DetailSection>
      ) : null}

      {uiState === "direction_filter_unavailable" ? (
        <DetailSection title="方向の参考情報を計算できませんでした" variant="tertiary">
          <p className="text-sm leading-6 text-[var(--kt-color-text-secondary)]">
            生年月日または出発地点をご確認のうえ、もう一度お試しください。
          </p>
        </DetailSection>
      ) : null}

      {uiState === "no_common_direction" ? (
        <DetailSection title="今月は方位の参考情報がありません" variant="tertiary">
          <p className="text-sm leading-6 text-[var(--kt-color-text-secondary)]">
            生年月日・出発地点はどちらも問題ありません。年盤と月盤の共通方位も、今月の月盤単独の参考方位も、今月はいずれもありませんでした。
          </p>
        </DetailSection>
      ) : null}

      {uiState === "direction_zero_candidates" ? (
        <DetailSection title="この方向の参拝候補が見つかりませんでした" variant="tertiary">
          <p className="text-sm leading-6 text-[var(--kt-color-text-secondary)]">
            出発地点を変えると、見つかることがあります。
          </p>
        </DetailSection>
      ) : null}

      {uiState === "evidence_zero_candidates" ? (
        <DetailSection title="参拝候補の情報を確認できませんでした" variant="tertiary">
          <p className="text-sm leading-6 text-[var(--kt-color-text-secondary)]">
            しばらくしてから、もう一度お試しください。
          </p>
        </DetailSection>
      ) : null}

      {uiState === "backend_error" ? (
        <DetailSection title="只今、確認できませんでした" variant="tertiary">
          <p className="text-sm leading-6 text-[var(--kt-color-text-secondary)]">
            時間をおいて、もう一度お試しください。
          </p>
        </DetailSection>
      ) : null}

      {uiState === "recommendation_success" && result ? (
        <CompassRecommendationsSection
          recommendations={result.recommendations}
          recommendationInstanceId={result.recommendation_instance_id}
        />
      ) : null}
    </div>
  );
}
