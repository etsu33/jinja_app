import json
from io import StringIO

import pytest
from django.core.management.base import CommandError
from django.core.management import call_command

from temples.management.commands import bootstrap_production_data as bootstrap_module
from temples.models import ProductionDataBootstrapRun, Shrine


@pytest.mark.django_db
def test_bootstrap_production_data_runs_unfinished_step_once(monkeypatch, tmp_path):
    source = tmp_path / "shrines.json"
    source.write_text(
        json.dumps(
            [
                {
                    "name_jp": "Bootstrap Test Shrine",
                    "address": "東京都千代田区",
                    "goriyaku": "開運",
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("USE_GIS", "0")
    monkeypatch.setattr(
        bootstrap_module,
        "BOOTSTRAP_STEPS",
        (
            bootstrap_module.BootstrapStep(
                step="test_import_shrines_seed",
                version="test-v1",
                command="import_shrines_seed",
                args=("--source", str(source)),
            ),
        ),
    )

    call_command("bootstrap_production_data", "--skip-debug-counts", stdout=StringIO())
    call_command("bootstrap_production_data", "--skip-debug-counts", stdout=StringIO())

    run = ProductionDataBootstrapRun.objects.get(
        step="test_import_shrines_seed",
        version="test-v1",
    )
    assert run.status == ProductionDataBootstrapRun.Status.SUCCESS
    assert run.attempts == 1
    assert Shrine.objects.filter(name_jp="Bootstrap Test Shrine").count() == 1


@pytest.mark.django_db
def test_bootstrap_production_data_records_failed_step_without_success(monkeypatch, tmp_path):
    missing_source = tmp_path / "missing.json"
    monkeypatch.setattr(
        bootstrap_module,
        "BOOTSTRAP_STEPS",
        (
            bootstrap_module.BootstrapStep(
                step="test_import_shrines_seed_failure",
                version="test-v1",
                command="import_shrines_seed",
                args=("--source", str(missing_source)),
            ),
        ),
    )

    with pytest.raises(CommandError):
        call_command("bootstrap_production_data", "--skip-debug-counts", stdout=StringIO())

    run = ProductionDataBootstrapRun.objects.get(
        step="test_import_shrines_seed_failure",
        version="test-v1",
    )
    assert run.status == ProductionDataBootstrapRun.Status.FAILED
    assert run.attempts == 1
    assert "source file not found" in run.last_error
    assert not ProductionDataBootstrapRun.objects.filter(
        step="test_import_shrines_seed_failure",
        version="test-v1",
        status=ProductionDataBootstrapRun.Status.SUCCESS,
    ).exists()
