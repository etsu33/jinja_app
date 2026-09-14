"""Local storage 上で、DB row 削除に合わせて実ファイルが消えることの統合test。

Storage は default_storage（Local）をそのまま使い、MEDIA_ROOT を tmp へ逃がす。
R2 へは接続しない。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import override_settings

from temples.models import Goshuin, GoshuinImage, Shrine
from tests.factories import UserFactory
from users.models import UserProfile

# 1x1 PNG。ImageField の検証を通る最小データ。
PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def _png(name="a.png"):
    return SimpleUploadedFile(name, PNG_1PX, content_type="image/png")


def _abs(media_root, field_file) -> Path:
    return Path(media_root) / field_file.name


@pytest.fixture
def media_root(tmp_path):
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        yield tmp_path


def _shrine():
    return Shrine.objects.create(
        name_jp="テスト神社",
        address="東京都千代田区1-1",
        latitude=35.6812,
        longitude=139.7671,
    )


# --- UserProfile.icon -------------------------------------------------------


@pytest.mark.django_db
def test_profile_delete_removes_the_icon_file(media_root, django_capture_on_commit_callbacks):
    user = UserFactory()
    profile = UserProfile.objects.get(user=user)
    profile.icon = _png("icon.png")
    profile.save()
    path = _abs(media_root, profile.icon)
    assert path.exists()

    with django_capture_on_commit_callbacks(execute=True):
        profile.delete()

    assert not path.exists()


@pytest.mark.django_db
def test_replacing_the_icon_removes_the_old_file_and_keeps_the_new_one(
    media_root, django_capture_on_commit_callbacks
):
    user = UserFactory()
    profile = UserProfile.objects.get(user=user)
    profile.icon = _png("old.png")
    profile.save()
    old_path = _abs(media_root, profile.icon)
    assert old_path.exists()

    with django_capture_on_commit_callbacks(execute=True):
        profile.icon = _png("new.png")
        profile.save()

    new_path = _abs(media_root, profile.icon)
    assert not old_path.exists()
    assert new_path.exists()
    assert old_path != new_path


@pytest.mark.django_db
def test_icon_file_survives_a_rolled_back_profile_delete(media_root):
    user = UserFactory()
    profile = UserProfile.objects.get(user=user)
    profile.icon = _png("icon.png")
    profile.save()
    path = _abs(media_root, profile.icon)

    with pytest.raises(RuntimeError):
        with transaction.atomic():
            profile.delete()
            raise RuntimeError("rollback")

    # DB が巻き戻った以上、ファイルも残っていなければ復旧できない
    assert path.exists()
    assert UserProfile.objects.filter(user=user).exists()


# --- GoshuinImage.image -----------------------------------------------------


@pytest.mark.django_db
def test_goshuin_image_delete_removes_the_image_file(
    media_root, django_capture_on_commit_callbacks
):
    user = UserFactory()
    goshuin = Goshuin.objects.create(user=user, shrine=_shrine())
    image = GoshuinImage.objects.create(goshuin=goshuin, image=_png("g.png"))
    path = _abs(media_root, image.image)
    assert path.exists()

    with django_capture_on_commit_callbacks(execute=True):
        image.delete()

    assert not path.exists()


@pytest.mark.django_db
def test_goshuin_delete_cascade_removes_child_image_files(
    media_root, django_capture_on_commit_callbacks
):
    """CASCADE 経由でも post_delete が飛び、実ファイルが消えること。

    receiver が登録されていないと Django は fast-delete 経路を選び、
    post_delete が飛ばずにファイルだけ残る。
    """
    user = UserFactory()
    goshuin = Goshuin.objects.create(user=user, shrine=_shrine())
    first = GoshuinImage.objects.create(goshuin=goshuin, image=_png("g1.png"), order=0)
    second = GoshuinImage.objects.create(goshuin=goshuin, image=_png("g2.png"), order=1)
    paths = [_abs(media_root, first.image), _abs(media_root, second.image)]
    assert all(p.exists() for p in paths)

    with django_capture_on_commit_callbacks(execute=True):
        goshuin.delete()

    assert GoshuinImage.objects.count() == 0
    assert not any(p.exists() for p in paths)


@pytest.mark.django_db
def test_goshuin_image_file_survives_a_rolled_back_delete(media_root):
    user = UserFactory()
    goshuin = Goshuin.objects.create(user=user, shrine=_shrine())
    image = GoshuinImage.objects.create(goshuin=goshuin, image=_png("g.png"))
    path = _abs(media_root, image.image)

    with pytest.raises(RuntimeError):
        with transaction.atomic():
            goshuin.delete()
            raise RuntimeError("rollback")

    assert path.exists()
    assert GoshuinImage.objects.filter(pk=image.pk).exists()


@pytest.mark.django_db
def test_files_are_not_deleted_before_commit(media_root):
    """commit 前の時点ではファイルが残っていること。"""
    user = UserFactory()
    goshuin = Goshuin.objects.create(user=user, shrine=_shrine())
    image = GoshuinImage.objects.create(goshuin=goshuin, image=_png("g.png"))
    path = _abs(media_root, image.image)

    with transaction.atomic():
        image.delete()
        assert path.exists()  # まだ commit していない
