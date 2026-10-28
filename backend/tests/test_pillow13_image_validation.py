"""Pillow 13 upgrade: image validation regression tests.

Covers the two Pillow-backed checks on goshuin uploads, with synthetic in-memory images only:
- DRF / Django ImageField（Image.open + verify inside Django forms.ImageField）;
- temples.api.serializers.validators.validate_image_file（content type, size, Image.open + verify, format allowlist）.
"""

from __future__ import annotations

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import serializers
from rest_framework.test import APIClient
from temples.api.serializers.my_goshuin import (
    ALLOWED_GOSHUIN_IMAGE_CT,
    ALLOWED_GOSHUIN_IMAGE_FORMATS,
    MAX_GOSHUIN_IMAGE_BYTES,
)
from temples.api.serializers.validators import validate_image_file
from temples.models import GoshuinImage, Shrine

URL = "/api/my/goshuins/"


def _image_bytes(fmt: str, mode: str = "RGB", size=(24, 16)) -> bytes:
    buf = io.BytesIO()
    img = Image.new(
        mode, size, color=0 if mode in ("L", "P", "1") else (10, 20, 30, 255)[: len(mode)]
    )
    img.save(buf, format=fmt)
    return buf.getvalue()


def _upload(data: bytes, name: str, content_type: str) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, data, content_type=content_type)


def _validate(f):
    validate_image_file(
        f,
        allowed_ct=ALLOWED_GOSHUIN_IMAGE_CT,
        allowed_formats=ALLOWED_GOSHUIN_IMAGE_FORMATS,
        max_bytes=MAX_GOSHUIN_IMAGE_BYTES,
    )


# --- validate_image_file ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fmt,mode,ct,name",
    [
        ("JPEG", "RGB", "image/jpeg", "a.jpg"),
        ("JPEG", "L", "image/jpeg", "a.jpeg"),
        ("PNG", "RGB", "image/png", "a.png"),
        ("PNG", "RGBA", "image/png", "a.png"),
        ("PNG", "P", "image/png", "a.png"),
        ("WEBP", "RGB", "image/webp", "a.webp"),
        ("WEBP", "RGBA", "image/webp", "a.webp"),
    ],
)
def test_supported_formats_pass_and_rewind(fmt, mode, ct, name):
    f = _upload(_image_bytes(fmt, mode), name, ct)

    _validate(f)

    assert f.tell() == 0  # verify() reads the file; the validator rewinds it for storage


@pytest.mark.parametrize(
    "fmt,ct",
    [("GIF", "image/png"), ("BMP", "image/png"), ("TIFF", "image/png"), ("GIF", "image/jpeg")],
)
def test_valid_images_in_disallowed_formats_are_rejected(fmt, ct):
    with pytest.raises(serializers.ValidationError):
        _validate(_upload(_image_bytes(fmt), "x.png", ct))


@pytest.mark.parametrize(
    "data",
    [
        b"not an image at all",
        b"\x89PNG\r\n\x1a\n" + b"\x00" * 16,  # PNG signature, no valid chunks
        _image_bytes("PNG")[:40],  # truncated PNG
        _image_bytes("JPEG")[:20],  # truncated JPEG header
        b"",
    ],
)
def test_corrupt_or_forged_files_are_rejected(data):
    with pytest.raises(serializers.ValidationError):
        _validate(_upload(data, "x.png", "image/png"))


def test_disallowed_content_type_is_rejected_even_for_a_valid_png():
    with pytest.raises(serializers.ValidationError):
        _validate(_upload(_image_bytes("PNG"), "x.png", "image/gif"))


def test_size_limit_is_enforced_before_decoding():
    data = _image_bytes("PNG")
    with pytest.raises(serializers.ValidationError):
        validate_image_file(
            _upload(data, "x.png", "image/png"),
            allowed_ct=ALLOWED_GOSHUIN_IMAGE_CT,
            allowed_formats=ALLOWED_GOSHUIN_IMAGE_FORMATS,
            max_bytes=len(data) - 1,
        )


def test_upload_limit_is_unchanged():
    assert MAX_GOSHUIN_IMAGE_BYTES == 10 * 1024 * 1024
    assert ALLOWED_GOSHUIN_IMAGE_FORMATS == {"JPEG", "PNG", "WEBP"}
    assert ALLOWED_GOSHUIN_IMAGE_CT == {"image/jpeg", "image/png", "image/webp"}


# --- API（ImageField + validate_image_file） ------------------------------------------------------------------


@pytest.fixture
def authed(django_user_model):
    user = django_user_model.objects.create_user(username="pillow13", password="unused-pillow13")
    client = APIClient()
    client.force_authenticate(user=user)
    shrine = Shrine.objects.create(
        name_jp="テスト神社", address="東京都", latitude=35.0, longitude=139.0
    )
    return client, shrine


def _post(client, shrine, f):
    return client.post(
        URL,
        data={"shrine": shrine.id, "title": "t", "is_public": False, "image": f},
        format="multipart",
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fmt,ct,name",
    [
        ("JPEG", "image/jpeg", "a.jpg"),
        ("PNG", "image/png", "a.png"),
        ("WEBP", "image/webp", "a.webp"),
    ],
)
def test_api_accepts_supported_formats(authed, fmt, ct, name):
    client, shrine = authed

    res = _post(client, shrine, _upload(_image_bytes(fmt), name, ct))

    assert res.status_code == 201, res.content
    assert GoshuinImage.objects.filter(goshuin_id=res.json()["id"]).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data,ct,name",
    [
        (_image_bytes("GIF"), "image/png", "a.png"),
        (_image_bytes("BMP"), "image/png", "a.png"),
        (b"plain text pretending to be a png", "image/png", "a.png"),
        (_image_bytes("PNG")[:40], "image/png", "a.png"),
    ],
)
def test_api_rejects_disallowed_or_broken_images_with_400(authed, data, ct, name):
    client, shrine = authed

    res = _post(client, shrine, _upload(data, name, ct))

    assert res.status_code == 400
    assert "image" in res.json()
    assert GoshuinImage.objects.count() == 0


@pytest.mark.django_db
def test_api_rejects_a_decompression_bomb_with_400(authed, monkeypatch):
    """Pillow raises DecompressionBombError above 2 × MAX_IMAGE_PIXELS; it must surface as 400, not 500."""
    client, shrine = authed
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 100)  # a 24 × 16 image is > 2 × 100 pixels

    res = _post(client, shrine, _upload(_image_bytes("PNG"), "a.png", "image/png"))

    assert res.status_code == 400
    assert GoshuinImage.objects.count() == 0
