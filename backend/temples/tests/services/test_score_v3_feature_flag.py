"""Score v3 Feature Flag のユニットテスト。

SCORE_V3_MODE 環境変数による shadow / active / fallback の挙動を確認する。
実装変更なし・DB不要。
"""
from __future__ import annotations

import importlib
import os

import pytest

# ---------------------------------------------------------------------------
# Helper: reload して os.environ の変更を反映させる
# ---------------------------------------------------------------------------

def _reload_mode(monkeypatch, value: str | None):
    """SCORE_V3_MODE を monkeypatch して ranking モジュールを reload する。"""
    if value is None:
        monkeypatch.delenv("SCORE_V3_MODE", raising=False)
    else:
        monkeypatch.setenv("SCORE_V3_MODE", value)

    import temples.services.concierge_chat_ranking as mod
    importlib.reload(mod)
    return mod


# ---------------------------------------------------------------------------
# resolve_score_v3_mode_detail
# ---------------------------------------------------------------------------

class TestResolveScoreV3ModeDetail:
    def test_active_env(self, monkeypatch):
        monkeypatch.setenv("SCORE_V3_MODE", "active")
        from temples.services.concierge_chat_ranking import resolve_score_v3_mode_detail
        result = resolve_score_v3_mode_detail()
        assert result == {"mode": "active", "source": "env"}

    def test_shadow_env(self, monkeypatch):
        monkeypatch.setenv("SCORE_V3_MODE", "shadow")
        from temples.services.concierge_chat_ranking import resolve_score_v3_mode_detail
        result = resolve_score_v3_mode_detail()
        assert result == {"mode": "shadow", "source": "env"}

    def test_unset_defaults_to_shadow(self, monkeypatch):
        monkeypatch.delenv("SCORE_V3_MODE", raising=False)
        from temples.services.concierge_chat_ranking import resolve_score_v3_mode_detail
        result = resolve_score_v3_mode_detail()
        assert result == {"mode": "shadow", "source": "default"}

    def test_invalid_env_fallback(self, monkeypatch):
        monkeypatch.setenv("SCORE_V3_MODE", "invalid_value")
        from temples.services.concierge_chat_ranking import resolve_score_v3_mode_detail
        result = resolve_score_v3_mode_detail()
        assert result == {"mode": "shadow", "source": "invalid_env"}

    def test_empty_string_defaults_to_shadow(self, monkeypatch):
        monkeypatch.setenv("SCORE_V3_MODE", "")
        from temples.services.concierge_chat_ranking import resolve_score_v3_mode_detail
        result = resolve_score_v3_mode_detail()
        assert result == {"mode": "shadow", "source": "default"}

    def test_uppercase_active_is_normalised(self, monkeypatch):
        monkeypatch.setenv("SCORE_V3_MODE", "ACTIVE")
        from temples.services.concierge_chat_ranking import resolve_score_v3_mode_detail
        result = resolve_score_v3_mode_detail()
        assert result == {"mode": "active", "source": "env"}

    def test_resolve_score_v3_mode_returns_string(self, monkeypatch):
        monkeypatch.setenv("SCORE_V3_MODE", "active")
        from temples.services.concierge_chat_ranking import resolve_score_v3_mode
        assert resolve_score_v3_mode() == "active"

        monkeypatch.delenv("SCORE_V3_MODE", raising=False)
        assert resolve_score_v3_mode() == "shadow"


# ---------------------------------------------------------------------------
# resolve_score_sort_key
# ---------------------------------------------------------------------------

class TestResolveScoreSortKey:
    def _rec(self, score_total: float, score_v3: float) -> dict:
        return {
            "_score_total": score_total,
            "breakdown": {"score_v3": score_v3},
        }

    def test_shadow_returns_score_total(self):
        from temples.services.concierge_chat_ranking import resolve_score_sort_key
        rec = self._rec(score_total=1.5, score_v3=0.9)
        assert resolve_score_sort_key(rec, score_v3_mode="shadow") == pytest.approx(1.5)

    def test_active_returns_score_v3(self):
        from temples.services.concierge_chat_ranking import resolve_score_sort_key
        rec = self._rec(score_total=1.5, score_v3=0.9)
        assert resolve_score_sort_key(rec, score_v3_mode="active") == pytest.approx(0.9)

    def test_shadow_missing_score_v3_still_works(self):
        from temples.services.concierge_chat_ranking import resolve_score_sort_key
        rec = {"_score_total": 2.0, "breakdown": {}}
        assert resolve_score_sort_key(rec, score_v3_mode="shadow") == pytest.approx(2.0)

    def test_active_missing_score_v3_returns_zero(self):
        from temples.services.concierge_chat_ranking import resolve_score_sort_key
        rec = {"_score_total": 2.0, "breakdown": {}}
        assert resolve_score_sort_key(rec, score_v3_mode="active") == pytest.approx(0.0)

    def test_shadow_and_active_agree_when_equal(self):
        from temples.services.concierge_chat_ranking import resolve_score_sort_key
        rec = self._rec(score_total=1.0, score_v3=1.0)
        assert resolve_score_sort_key(rec, score_v3_mode="shadow") == resolve_score_sort_key(
            rec, score_v3_mode="active"
        )

    def test_sort_order_differs_between_modes(self):
        """active モードでは sort_key が score_v3 になることで順位が変わりうる。"""
        from temples.services.concierge_chat_ranking import resolve_score_sort_key

        rec_a = {"_score_total": 2.0, "breakdown": {"score_v3": 0.5}}
        rec_b = {"_score_total": 1.0, "breakdown": {"score_v3": 1.5}}

        # shadow: rec_a が上（score_total 2.0 > 1.0）
        shadow_keys = [
            resolve_score_sort_key(r, score_v3_mode="shadow") for r in [rec_a, rec_b]
        ]
        assert shadow_keys[0] > shadow_keys[1]

        # active: rec_b が上（score_v3 1.5 > 0.5）
        active_keys = [
            resolve_score_sort_key(r, score_v3_mode="active") for r in [rec_a, rec_b]
        ]
        assert active_keys[0] < active_keys[1]


# ---------------------------------------------------------------------------
# summarize_score_v3_ab_observations
# ---------------------------------------------------------------------------

class TestSummarizeScoreV3AbObservations:
    def _obs(self, top1_changed_rate=0.0, avg_delta=0.0, max_abs_delta=0.0, activation_candidate=True):
        return {
            "mode": "shadow",
            "top1_changed_rate": top1_changed_rate,
            "avg_delta": avg_delta,
            "max_abs_delta": max_abs_delta,
            "activation_candidate": activation_candidate,
        }

    def test_empty_returns_zeros(self):
        from temples.services.concierge_observability import summarize_score_v3_ab_observations
        result = summarize_score_v3_ab_observations([])
        assert result == {
            "count": 0,
            "top1_changed_rate_avg": 0.0,
            "activation_candidate_rate": 0.0,
            "avg_delta": 0.0,
            "max_abs_delta_avg": 0.0,
            "max_abs_delta_max": 0.0,
        }

    def test_single_observation(self):
        from temples.services.concierge_observability import summarize_score_v3_ab_observations
        obs = [self._obs(top1_changed_rate=0.0, avg_delta=-0.12, max_abs_delta=0.25, activation_candidate=True)]
        result = summarize_score_v3_ab_observations(obs)
        assert result["count"] == 1
        assert result["top1_changed_rate_avg"] == pytest.approx(0.0)
        assert result["activation_candidate_rate"] == pytest.approx(1.0)
        assert result["avg_delta"] == pytest.approx(-0.12)
        assert result["max_abs_delta_avg"] == pytest.approx(0.25)
        assert result["max_abs_delta_max"] == pytest.approx(0.25)

    def test_multiple_observations_averages(self):
        from temples.services.concierge_observability import summarize_score_v3_ab_observations
        obs = [
            self._obs(top1_changed_rate=0.0, avg_delta=-0.1, max_abs_delta=0.2, activation_candidate=True),
            self._obs(top1_changed_rate=1.0, avg_delta=-0.2, max_abs_delta=0.4, activation_candidate=False),
            self._obs(top1_changed_rate=0.0, avg_delta=0.0, max_abs_delta=0.1, activation_candidate=True),
        ]
        result = summarize_score_v3_ab_observations(obs)
        assert result["count"] == 3
        assert result["top1_changed_rate_avg"] == pytest.approx(1.0 / 3, rel=1e-5)
        assert result["activation_candidate_rate"] == pytest.approx(2.0 / 3, rel=1e-5)
        assert result["avg_delta"] == pytest.approx((-0.1 - 0.2 + 0.0) / 3, rel=1e-5)
        assert result["max_abs_delta_avg"] == pytest.approx((0.2 + 0.4 + 0.1) / 3, rel=1e-5)
        assert result["max_abs_delta_max"] == pytest.approx(0.4)

    def test_none_and_missing_fields_tolerated(self):
        from temples.services.concierge_observability import summarize_score_v3_ab_observations
        result = summarize_score_v3_ab_observations([{}, {"top1_changed_rate": None}])
        assert result["count"] == 2
        assert result["top1_changed_rate_avg"] == pytest.approx(0.0)

    def test_returns_required_keys(self):
        from temples.services.concierge_observability import summarize_score_v3_ab_observations
        result = summarize_score_v3_ab_observations([self._obs()])
        assert set(result.keys()) == {
            "count",
            "top1_changed_rate_avg",
            "activation_candidate_rate",
            "avg_delta",
            "max_abs_delta_avg",
            "max_abs_delta_max",
        }
