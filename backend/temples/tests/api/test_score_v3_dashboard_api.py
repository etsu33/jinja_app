from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from temples.models_concierge_analytics import ConciergeRecommendationLog


class ScoreV3DashboardAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username="admin_v3",
            email="admin_v3@example.com",
            password="password",
        )
        self.user = User.objects.create_user(
            username="user_v3",
            email="user_v3@example.com",
            password="password",
        )
        self.url = reverse("temples:score-v3-dashboard")

    def test_admin_gets_200(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_non_admin_gets_403(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        assert response.status_code == 403

    def test_anonymous_gets_401(self):
        response = self.client.get(self.url)
        assert response.status_code in (401, 403)

    def test_no_data_returns_200_with_zeros(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        assert response.status_code == 200
        data = response.data
        assert "score_v3" in data
        assert "funnel" in data
        assert "decision" in data
        assert data["score_v3"]["top1_changed_rate_avg"] == 0.0
        assert data["funnel"]["route_open_rate"] == 0.0
        assert data["decision"]["active_candidate"] is False
        assert data["decision"]["rollback_required"] is False

    def test_decision_key_present(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        assert response.status_code == 200
        decision = response.data["decision"]
        assert "active_candidate" in decision
        assert "rollback_required" in decision
        assert "reasons" in decision

    def test_score_v3_and_funnel_keys_present(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        sv3 = response.data["score_v3"]
        assert "top1_changed_rate_avg" in sv3
        assert "activation_candidate_rate" in sv3
        assert "avg_delta" in sv3
        assert "max_abs_delta_max" in sv3
        funnel = response.data["funnel"]
        assert "route_open_rate" in funnel
        assert "save_rate" in funnel
        assert "visit_done_rate" in funnel
        assert "reflection_saved_rate" in funnel
        assert "detail_view_count" in funnel
        assert "route_open_count" in funnel
        assert "save_count" in funnel
        assert "visit_count" in funnel
        assert "reflection_count" in funnel
        assert "save_to_visit_cvr" in funnel
        assert "visit_to_reflection_cvr" in funnel

    def test_with_observation_data_aggregated(self):
        ConciergeRecommendationLog.objects.create(
            query="test",
            result_state={
                "_score_v3_debug": {
                    "score_v3_ab_observation": {
                        "top1_changed_rate": 0.05,
                        "activation_candidate": True,
                        "avg_delta": 0.1,
                        "max_abs_delta": 0.3,
                    }
                }
            },
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        assert response.status_code == 200
        sv3 = response.data["score_v3"]
        assert sv3["top1_changed_rate_avg"] == 0.05
        assert sv3["activation_candidate_rate"] == 1.0
        assert sv3["max_abs_delta_max"] == 0.3

    def test_active_candidate_true_when_criteria_met(self):
        ConciergeRecommendationLog.objects.create(
            query="test",
            result_state={
                "_score_v3_debug": {
                    "score_v3_ab_observation": {
                        "top1_changed_rate": 0.05,
                        "activation_candidate": True,
                        "avg_delta": 0.01,
                        "max_abs_delta": 0.2,
                    }
                }
            },
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        assert response.data["decision"]["active_candidate"] is True
        assert response.data["decision"]["rollback_required"] is False

    def test_rollback_required_true_when_criteria_met(self):
        ConciergeRecommendationLog.objects.create(
            query="test",
            result_state={
                "_score_v3_debug": {
                    "score_v3_ab_observation": {
                        "top1_changed_rate": 0.25,
                        "activation_candidate": False,
                        "avg_delta": 0.5,
                        "max_abs_delta": 1.5,
                    }
                }
            },
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        assert response.data["decision"]["rollback_required"] is True
        assert response.data["decision"]["active_candidate"] is False

    def test_invalid_datetime_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"from": "not-a-date"})
        assert response.status_code == 400
        assert "Invalid datetime" in response.data["detail"]
