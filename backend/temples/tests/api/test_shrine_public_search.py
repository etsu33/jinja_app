import pytest
from rest_framework.test import APIClient

from temples.models import Shrine

pytestmark = pytest.mark.django_db


def test_public_search_does_not_include_pending_submission_like_data():
    Shrine.objects.create(
        name_jp="公開神社A",
        address="東京都千代田区1-1",
        kind="shrine",
    )
    Shrine.objects.create(
        name_jp="未公開候補っぽい神社",
        address="東京都渋谷区2-2",
        kind="shrine",
    )

    client = APIClient()
    res = client.get("/api/shrines/?q=公開神社A")

    assert res.status_code == 200
    data = res.json()

    names = [row["name_jp"] for row in data.get("results", data)]
    assert "公開神社A" in names
