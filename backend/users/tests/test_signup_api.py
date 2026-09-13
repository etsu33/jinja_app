# backend/users/tests/test_signup_api.py
"""Signup API（POST /api/users/signup/）の validation 契約。

Backend を validation の正本とするため、Frontend の入力チェックとは独立に
username / email / password の必須条件をここで固定する。
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from tests.utils import api_client_as

SIGNUP_URL_NAME = "users_api:signup"

User = get_user_model()


def _post(payload):
    return api_client_as().post(reverse(SIGNUP_URL_NAME), payload, format="json")


@pytest.mark.django_db
def test_signup_succeeds_with_username_email_password():
    res = _post({"username": "tarou", "email": "tarou@example.com", "password": "password123"})

    assert res.status_code == 201
    body = res.json()
    assert body["username"] == "tarou"
    assert "id" in body

    user = User.objects.get(username="tarou")
    assert user.email == "tarou@example.com"
    assert user.check_password("password123")


@pytest.mark.django_db
def test_signup_rejects_missing_email():
    res = _post({"username": "tarou", "password": "password123"})

    assert res.status_code == 400
    assert "email" in res.json()
    assert not User.objects.filter(username="tarou").exists()


@pytest.mark.django_db
def test_signup_rejects_blank_email():
    res = _post({"username": "tarou", "email": "", "password": "password123"})

    assert res.status_code == 400
    assert "email" in res.json()
    assert not User.objects.filter(username="tarou").exists()


@pytest.mark.django_db
def test_signup_rejects_null_email():
    res = _post({"username": "tarou", "email": None, "password": "password123"})

    assert res.status_code == 400
    assert "email" in res.json()
    assert not User.objects.filter(username="tarou").exists()


@pytest.mark.django_db
def test_signup_rejects_invalid_email_format():
    res = _post({"username": "tarou", "email": "not-an-email", "password": "password123"})

    assert res.status_code == 400
    assert "email" in res.json()
    assert not User.objects.filter(username="tarou").exists()


@pytest.mark.django_db
def test_signup_rejects_missing_username():
    res = _post({"email": "tarou@example.com", "password": "password123"})

    assert res.status_code == 400
    assert "username" in res.json()
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_signup_rejects_blank_username():
    res = _post({"username": "", "email": "tarou@example.com", "password": "password123"})

    assert res.status_code == 400
    assert "username" in res.json()
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_signup_rejects_password_shorter_than_8():
    res = _post({"username": "tarou", "email": "tarou@example.com", "password": "short12"})

    assert res.status_code == 400
    assert "password" in res.json()
    assert not User.objects.filter(username="tarou").exists()


@pytest.mark.django_db
def test_signup_rejects_missing_password():
    res = _post({"username": "tarou", "email": "tarou@example.com"})

    assert res.status_code == 400
    assert "password" in res.json()
    assert not User.objects.filter(username="tarou").exists()


@pytest.mark.django_db
def test_signup_rejects_duplicate_username():
    User.objects.create_user(username="tarou", email="tarou@example.com", password="password123")

    res = _post({"username": "tarou", "email": "other@example.com", "password": "password123"})

    assert res.status_code == 400
    assert "username" in res.json()
    assert User.objects.filter(username="tarou").count() == 1


@pytest.mark.django_db
def test_signup_does_not_return_password():
    res = _post({"username": "tarou", "email": "tarou@example.com", "password": "password123"})

    assert res.status_code == 201
    assert "password" not in res.json()
