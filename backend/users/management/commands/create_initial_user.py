"""Explicit initial-user creation without credentials embedded in source control."""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "明示的に設定された認証情報から初期ユーザーを作成する（既存ユーザーは変更しない）"

    def handle(self, *args, **options):
        if os.environ.get("KAMIMUSUBI_BOOTSTRAP_INITIAL_USER") != "1":
            raise CommandError("explicit_bootstrap_authorization_required")

        username = os.environ.get("KAMIMUSUBI_BOOTSTRAP_USERNAME", "").strip()
        email = os.environ.get("KAMIMUSUBI_BOOTSTRAP_EMAIL", "").strip()
        password = os.environ.get("KAMIMUSUBI_BOOTSTRAP_PASSWORD", "")
        if not username or not email or not password:
            raise CommandError("bootstrap_credentials_missing")

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise CommandError("bootstrap_user_already_exists")

        User.objects.create_user(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS("initial_user_created"))
