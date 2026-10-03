"""Generate the A-5b §10.1 reproducibility projection (read-only).

Usage:
    python manage.py a5b_reproducibility_projection [--commit REV] [--output PATH]

Reads git-tracked records at one commit and writes the canonical projection
bytes (A-5b contract §10.1 H) to stdout, or to ``--output``. The SHA-256 and the
resolved input commit are written to stderr. An unresolved projection
(§10.1 I) exits with status 2 and writes nothing.

This command does not designate a run1 / run2 and records nothing. No DB access.
"""

from __future__ import annotations

import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from temples.services.a5b_reproducibility_projection import (
    GitCommitReader,
    ProjectionUnresolved,
    build_projection,
    projection_sha256,
    serialize_projection,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


class Command(BaseCommand):
    help = "Generate the A-5b §10.1 canonical reproducibility projection (read-only)."
    requires_system_checks: list[str] = []
    requires_migrations_checks = False

    def add_arguments(self, parser):
        parser.add_argument("--commit", default="HEAD", help="input commit (default: HEAD)")
        parser.add_argument(
            "--output", help="write the canonical bytes to this path instead of stdout"
        )

    def handle(self, *args, **options):
        try:
            reader = GitCommitReader(options["commit"], REPO_ROOT)
            data = serialize_projection(build_projection(reader))
        except ProjectionUnresolved as exc:
            self.stderr.write(f"UNRESOLVED: {exc}")
            raise CommandError("A-5b reproducibility projection UNRESOLVED", returncode=2) from exc

        if options["output"]:
            Path(options["output"]).write_bytes(data)
        else:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
        self.stderr.write(f"input_commit={reader.commit}")
        self.stderr.write(f"sha256={projection_sha256(data)}")
