"""Account Deletion と Storage cleanup（PR #2829）の接続。

#2829 の contract test は複製しない。Account 削除経路から
post_delete receiver + transaction.on_commit が発火することだけを確認する。
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from temples.models import Goshuin, GoshuinImage, Shrine
from tests.factories import UserFactory
from users.models import UserProfile
from users.services.account_deletion import AccountDataDeletionFailed, delete_user_account

pytestmark = pytest.mark.django_db

PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def _png(name="a.png"):
    return SimpleUploadedFile(name, PNG_1PX, content_type="image/png")


@pytest.fixture
def media_root(tmp_path):
    with override_settings(MEDIA_ROOT=str(tmp_path), STRIPE_SECRET_KEY="sk_test_dummy"):
        yield tmp_path


def _seed_files(user, media_root):
    profile = UserProfile.objects.get(user=user)
    profile.icon = _png("icon.png")
    profile.save()

    shrine = Shrine.objects.create(
        name_jp="テスト神社", address="東京都1-1", latitude=35.6, longitude=139.7
    )
    goshuin = Goshuin.objects.create(user=user, shrine=shrine)
    image = GoshuinImage.objects.create(goshuin=goshuin, image=_png("g.png"))

    icon_path = Path(media_root) / profile.icon.name
    image_path = Path(media_root) / image.image.name
    assert icon_path.exists() and image_path.exists()
    return icon_path, image_path


def test_account_deletion_removes_profile_icon_and_goshuin_images(
    media_root, django_capture_on_commit_callbacks
):
    user = UserFactory()
    icon_path, image_path = _seed_files(user, media_root)

    with django_capture_on_commit_callbacks(execute=True):
        delete_user_account(user=user)

    assert not icon_path.exists()
    assert not image_path.exists()


def test_storage_files_survive_when_the_deletion_transaction_fails(
    media_root, django_capture_on_commit_callbacks
):
    """DB が巻き戻ったら実ファイルも消えないこと。"""
    user = UserFactory()
    icon_path, image_path = _seed_files(user, media_root)

    with django_capture_on_commit_callbacks(execute=True):
        with patch.object(type(user), "delete", side_effect=RuntimeError("db boom")):
            with pytest.raises(AccountDataDeletionFailed):
                delete_user_account(user=user)

    assert icon_path.exists()
    assert image_path.exists()
    assert UserProfile.objects.filter(user=user).exists()
