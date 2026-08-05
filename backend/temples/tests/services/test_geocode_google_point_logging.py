# backend/temples/tests/services/test_geocode_google_point_logging.py
#
# geocode_google_point() previously used bare print() calls that logged the
# raw user-entered area/address text, and on exceptions logged str(e) —
# which for requests connection/timeout errors embeds the full request URL
# including the Google Maps API key and address query param (verified
# empirically against the real requests library). This guards against that
# class of leak recurring.
from __future__ import annotations

import logging

import pytest
import requests

from temples.geocoding.client import geocode_google_point

FAKE_API_KEY = "FAKE_GOOGLE_MAPS_KEY_FOR_TEST"
SENSITIVE_AREA = "東京都渋谷区_SENSITIVE_ADDRESS_MARKER"


def _logged_text(caplog: pytest.LogCaptureFixture) -> str:
    return "\n".join(record.getMessage() for record in caplog.records)


def test_geocode_google_point_does_not_log_area_or_key_on_connection_error(
    monkeypatch, requests_mock, caplog
):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", FAKE_API_KEY)

    # requests_mock's ConnectionError path reproduces the same exception shape
    # (URL with query string embedded in str(e)) as a real network failure.
    requests_mock.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        exc=requests.exceptions.ConnectionError(
            f"Max retries exceeded with url: /maps/api/geocode/json?key={FAKE_API_KEY}&address={SENSITIVE_AREA}"
        ),
    )

    with caplog.at_level(logging.INFO, logger="temples.geocoding.client"):
        result = geocode_google_point(SENSITIVE_AREA)

    assert result is None
    logged = _logged_text(caplog)
    assert FAKE_API_KEY not in logged
    assert SENSITIVE_AREA not in logged


def test_geocode_google_point_does_not_log_area_on_skip(monkeypatch, caplog):
    # _google_maps_api_key() also falls back to django.conf.settings, which is
    # resolved once at process start, so clearing env vars alone can't force
    # the "no key" branch reliably here — patch the resolver directly instead.
    monkeypatch.setattr("temples.geocoding.client._google_maps_api_key", lambda: None)

    with caplog.at_level(logging.INFO, logger="temples.geocoding.client"):
        result = geocode_google_point(SENSITIVE_AREA)

    assert result is None
    logged = _logged_text(caplog)
    assert SENSITIVE_AREA not in logged


def test_geocode_google_point_does_not_log_area_on_response(monkeypatch, requests_mock, caplog):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", FAKE_API_KEY)

    requests_mock.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        json={"status": "OK", "results": [{"geometry": {"location": {"lat": 35.0, "lng": 139.0}}}]},
        status_code=200,
    )

    with caplog.at_level(logging.INFO, logger="temples.geocoding.client"):
        result = geocode_google_point(SENSITIVE_AREA)

    assert result == (35.0, 139.0)
    logged = _logged_text(caplog)
    assert SENSITIVE_AREA not in logged
    assert FAKE_API_KEY not in logged
