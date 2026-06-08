from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from temples.models import Favorite, Shrine, ShrineInteractionLog


class DebugBehaviorFunnelAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        self.user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="password",
        )
        self.shrine = Shrine.objects.create(
            name_jp="テスト神社",
            address="東京都千代田区",
            latitude=35.681236,
            longitude=139.767125,
        )
        self.url = reverse("temples:debug-behavior-funnel")

    def test_admin_can_get_behavior_funnel_metrics(self):
        ShrineInteractionLog.objects.create(
            user=self.user,
            shrine=self.shrine,
            action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
        )
        ShrineInteractionLog.objects.create(
            user=self.user,
            shrine=self.shrine,
            action_type=ShrineInteractionLog.ActionType.ROUTE_OPEN,
        )
        Favorite.objects.create(
            user=self.user,
            shrine=self.shrine,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)

        assert response.status_code == 200
        assert response.data["detail_view_count"] == 1
        assert response.data["route_open_count"] == 1
        assert response.data["save_count"] == 1
        assert response.data["visit_count"] == 0
        assert response.data["reflection_count"] == 0
        assert response.data["save_to_visit_cvr"] == 0.0
        assert response.data["visit_to_reflection_cvr"] == 0.0

    def test_non_admin_cannot_get_behavior_funnel_metrics(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        assert response.status_code == 403

    def test_returns_404_when_shrine_does_not_exist(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.url, {"shrine_id": 999999})

        assert response.status_code == 404
        assert response.data["detail"] == "Shrine not found."

    def test_returns_400_when_datetime_is_invalid(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.url, {"from": "not-a-date"})

        assert response.status_code == 400
        assert "Invalid datetime" in response.data["detail"]
