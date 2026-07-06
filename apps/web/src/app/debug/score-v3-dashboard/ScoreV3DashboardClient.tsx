"use client";

import { useEffect, useState } from "react";
import { fetchScoreV3Dashboard } from "@/features/scoreV3Dashboard/fetchDashboard";
import type { ScoreV3DashboardResponse } from "@/features/scoreV3Dashboard/types";

type State =
  | { phase: "idle" }
  | { phase: "loading" }
  | { phase: "error"; status: number; message: string }
  | { phase: "ok"; data: ScoreV3DashboardResponse };

function pct(v: number) {
  return `${(v * 100).toFixed(1)}%`;
}

function Metric({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="flex items-center justify-between text-sm py-1 border-b last:border-b-0">
      <span className="text-slate-600">{label}</span>
      <span className="font-mono font-semibold tabular-nums">
        {value}
        {note && <span className="ml-1 text-xs text-slate-400 font-normal">{note}</span>}
      </span>
    </div>
  );
}

function count(v: number) {
  return v.toLocaleString("ja-JP");
}

function DecisionBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center justify-between text-sm py-1">
      <span className="text-slate-600">{label}</span>
      <span
        className={`rounded-full px-3 py-0.5 text-xs font-bold ${
          ok ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"
        }`}
      >
        {ok ? "YES" : "NO"}
      </span>
    </div>
  );
}

export default function ScoreV3DashboardClient() {
  const [state, setState] = useState<State>({ phase: "idle" });

  async function load() {
    setState({ phase: "loading" });
    const result = await fetchScoreV3Dashboard();
    if (result.ok) {
      setState({ phase: "ok", data: result.data });
    } else {
      setState({ phase: "error", status: result.status, message: result.message });
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="mx-auto max-w-2xl space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Score v3 Dashboard</h1>
        <button
          type="button"
          onClick={load}
          disabled={state.phase === "loading"}
          className="rounded-full border bg-white px-3 py-1.5 text-xs font-semibold hover:bg-slate-50 disabled:opacity-40"
        >
          {state.phase === "loading" ? "読み込み中…" : "更新"}
        </button>
      </div>

      {state.phase === "idle" || state.phase === "loading" ? (
        <div className="rounded-2xl border bg-white p-4 text-sm text-slate-500">読み込み中…</div>
      ) : state.phase === "error" ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 space-y-1">
          <div className="font-semibold text-rose-700">
            {state.status === 401 ? "401 Unauthorized" : state.status === 403 ? "403 Forbidden" : "エラー"}
          </div>
          <div className="text-sm text-rose-600">{state.message}</div>
        </div>
      ) : (
        <>
          {/* decision */}
          <div className="rounded-2xl border bg-white p-4 space-y-1">
            <div className="text-sm font-semibold mb-2">判定</div>
            <DecisionBadge ok={state.data.decision.active_candidate} label="active_candidate" />
            <DecisionBadge ok={!state.data.decision.rollback_required} label="rollback_required (falseが正常)" />
            {state.data.decision.reasons.length > 0 && (
              <div className="mt-2 space-y-1">
                {state.data.decision.reasons.map((r, i) => (
                  <div key={i} className="rounded-lg bg-amber-50 px-3 py-1.5 text-xs text-amber-700">
                    {r}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* score_v3 */}
          <div className="rounded-2xl border bg-white p-4 space-y-0">
            <div className="text-sm font-semibold mb-2">Score v3 観測値</div>
            <Metric
              label="top1_changed_rate_avg"
              value={pct(state.data.score_v3.top1_changed_rate_avg)}
              note="(目安: ≤10%)"
            />
            <Metric
              label="activation_candidate_rate"
              value={pct(state.data.score_v3.activation_candidate_rate)}
              note="(目安: ≥80%)"
            />
            <Metric label="avg_delta" value={state.data.score_v3.avg_delta.toFixed(4)} />
            <Metric
              label="max_abs_delta_max"
              value={state.data.score_v3.max_abs_delta_max.toFixed(4)}
              note="(目安: <0.50)"
            />
          </div>

          {/* funnel */}
          <div className="rounded-2xl border bg-white p-4 space-y-0">
            <div className="text-sm font-semibold mb-2">Behavior Funnel</div>
            <Metric label="detail_view_count" value={count(state.data.funnel.detail_view_count)} />
            <Metric label="route_open_count" value={count(state.data.funnel.route_open_count)} />
            <Metric label="save_count" value={count(state.data.funnel.save_count)} />
            <Metric label="visit_count" value={count(state.data.funnel.visit_count)} />
            <Metric label="reflection_count" value={count(state.data.funnel.reflection_count)} />
            <Metric label="route_open_rate" value={pct(state.data.funnel.route_open_rate)} />
            <Metric label="save_rate" value={pct(state.data.funnel.save_rate)} />
            <Metric label="visit_done_rate" value={pct(state.data.funnel.visit_done_rate)} />
            <Metric label="reflection_saved_rate" value={pct(state.data.funnel.reflection_saved_rate)} />
          </div>
        </>
      )}

      <div className="rounded-2xl border bg-white p-4">
        <p className="text-xs text-slate-500">admin / superuser 専用。非 staff は 403 が返ります。</p>
      </div>
    </main>
  );
}
