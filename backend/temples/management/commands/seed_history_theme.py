from __future__ import annotations

from django.core.management.base import BaseCommand

from temples.models import Shrine


HISTORY_THEME_SEED: dict[int, str] = {
    17: "勝負",
    14: "勝負",
    15: "勝負",
    10: "勝負",
    58: "勝負",
    59: "勝負",
    49: "勝負",
    94: "勝負",
    90: "勝負",
    88: "勝負",
    4: "縁",
    44: "縁",
    40: "縁",
    89: "縁",
    31: "縁",
    55: "縁",
    48: "縁",
    36: "縁",
    34: "縁",
    72: "縁",
    6: "学び",
    64: "学び",
    47: "学び",
    92: "学び",
    85: "学び",
    74: "学び",
    77: "学び",
    26: "守り",
    12: "守り",
    65: "守り",
    11: "守り",
    57: "守り",
    78: "守り",
    29: "守り",
    35: "守り",
    3: "再出発",
    1: "再出発",
    30: "再出発",
    100: "再出発",
    50: "再出発",
    33: "再出発",
    23: "再出発",
    83: "復興",
    96: "復興",
    99: "復興",
    87: "復興",
    51: "復興",
    71: "静寂",
    27: "静寂",
    28: "静寂",
    91: "静寂",
    2: "勝負",
    5: "守り",
    7: "守り",
    8: "勝負",
    9: "守り",
    13: "守り",
    16: "縁",
    18: "再出発",
    19: "守り",
    20: "勝負",
    24: "守り",
    25: "守り",
    32: "守り",
    37: "学び",
    38: "縁",
    39: "勝負",
    41: "縁",
    42: "縁",
    43: "勝負",
    45: "縁",
    46: "勝負",
    52: "縁",
    53: "勝負",
    54: "縁",
    56: "復興",
    60: "縁",
    61: "学び",
    62: "守り",
    63: "勝負",
    66: "守り",
    67: "勝負",
    68: "勝負",
    69: "勝負",
    70: "縁",
    73: "勝負",
    75: "守り",
    76: "勝負",
    79: "縁",
    80: "縁",
    81: "守り",
    82: "勝負",
    84: "縁",
    86: "守り",
    93: "縁",
    95: "守り",
    97: "守り",
    98: "勝負",
}


class Command(BaseCommand):
    help = "Seed Shrine.history_theme for representative shrines."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show planned updates without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        updated = 0
        missing: list[int] = []

        for shrine_id, history_theme in HISTORY_THEME_SEED.items():
            shrine = Shrine.objects.filter(id=shrine_id).only("id", "name_jp", "history_theme").first()
            if shrine is None:
                missing.append(shrine_id)
                continue

            current = shrine.history_theme or ""
            if current == history_theme:
                self.stdout.write(f"SKIP {shrine_id}: {shrine.name_jp} already {history_theme}")
                continue

            self.stdout.write(f"SET {shrine_id}: {shrine.name_jp} {current!r} -> {history_theme!r}")
            if not dry_run:
                shrine.history_theme = history_theme
                shrine.save(update_fields=["history_theme"])
            updated += 1

        if missing:
            self.stdout.write(self.style.WARNING(f"Missing shrine ids: {missing}"))

        mode = "dry-run" if dry_run else "updated"
        self.stdout.write(self.style.SUCCESS(f"history_theme seed {mode}: {updated}"))
        self.stdout.write(self.style.SUCCESS(f"history_theme seed total: {len(HISTORY_THEME_SEED)}"))
