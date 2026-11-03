"""Explicit, environment-driven bootstrap for a superuser.

Do not execute automatically at startup. Configure credentials via a secret manager,
and rotate any credentials previously committed to repository history.
"""

import os

from django.contrib.auth import get_user_model


def create_user_once():
    if os.environ.get("KAMIMUSUBI_BOOTSTRAP_SUPERUSER") != "1":
        raise RuntimeError("explicit_bootstrap_authorization_required")

    username = os.environ.get("KAMIMUSUBI_BOOTSTRAP_USERNAME", "").strip()
    email = os.environ.get("KAMIMUSUBI_BOOTSTRAP_EMAIL", "").strip()
    password = os.environ.get("KAMIMUSUBI_BOOTSTRAP_PASSWORD", "")
    if not username or not email or not password:
        raise RuntimeError("bootstrap_credentials_missing")

    User = get_user_model()
    if User.objects.filter(username=username).exists():
        raise RuntimeError("bootstrap_user_already_exists")

    User.objects.create_superuser(username=username, email=email, password=password)
    print("bootstrap_user_created")


if __name__ == "__main__":
    create_user_once()
