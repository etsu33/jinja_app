"""Regression checks: bootstrap must be opt-in and never retain fixed credentials."""

import os
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.django_db
def test_initial_user_missing_explicit_authorization_fails():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(CommandError, match="explicit_bootstrap_authorization_required"):
            call_command("create_initial_user")


@pytest.mark.django_db
def test_initial_user_missing_credentials_fails():
    with patch.dict(os.environ, {"KAMIMUSUBI_BOOTSTRAP_INITIAL_USER": "1"}, clear=True):
        with pytest.raises(CommandError, match="bootstrap_credentials_missing"):
            call_command("create_initial_user")


@pytest.mark.django_db
def test_initial_user_create_once_and_never_update(django_user_model):
    env = {
        "KAMIMUSUBI_BOOTSTRAP_INITIAL_USER": "1",
        "KAMIMUSUBI_BOOTSTRAP_USERNAME": "bootstrap_fixture_user",
        "KAMIMUSUBI_BOOTSTRAP_EMAIL": "bootstrap@example.invalid",
        "KAMIMUSUBI_BOOTSTRAP_PASSWORD": "only-a-test-credential-not-for-production",
    }
    with patch.dict(os.environ, env, clear=True):
        call_command("create_initial_user")
        user = django_user_model.objects.get(username=env["KAMIMUSUBI_BOOTSTRAP_USERNAME"])
        assert user.check_password(env["KAMIMUSUBI_BOOTSTRAP_PASSWORD"])
        assert not user.is_superuser
        with pytest.raises(CommandError, match="bootstrap_user_already_exists"):
            call_command("create_initial_user")
        assert django_user_model.objects.get(pk=user.pk).check_password(
            env["KAMIMUSUBI_BOOTSTRAP_PASSWORD"]
        )
