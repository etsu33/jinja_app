"""Source backfill for shrine ids 10 (鶴岡八幡宮) and 22 (給田六所神社).

P4 — `docs/audit/source-backfill-id10-id22-reproducibility.md`.

Both shrines carry Knowledge Facts backed only by non-primary Sources
(`tourism_official` + `secondary_editorial` for id 10; `secondary_editorial`
+ `local_history` for id 22). This migration adds **one government /
cultural-property `ShrineKnowledgeSource` per shrine**, first-hand reviewed
this session, and relates it to the **existing** `ShrineHistory` Fact(s) it
directly corroborates. It is a provenance upgrade only:

- **no new Fact** is created (`ShrineDeity` / `ShrineHistory` untouched);
- **no Fact field** (`verification_status` / `confidence` / `verified_at` /
  content) is changed;
- **no `Shrine.goriyaku` / `goriyaku_tags` / `GoriyakuTag` / Need-mapping**
  change;
- scope is **exactly shrine ids 10 and 22**.

Deterministic + idempotent + reversible, mirroring 0090 / 0091 / 0094 / 0095.

**Local/Production reproducibility:** the local dev DB (`jinja_db`) and
Production assign **different `ShrineHistory` pks** to the same seed Facts
(e.g. 鶴岡八幡宮's "由比若宮の勧請" founding history is pk 19 locally, pk 13
in Production). So the target Facts are matched by their **environment-stable
identity** — `shrine_id` (pk 10 / 22, stable) + `history_type` + `title`
(seed-defined) — **never by `ShrineHistory` pk**. The same artifact then
relates the reviewed Source to the same semantic Fact in every environment.

- shrine matched by pk **and** guarded by expected `name_jp` + `place_ref_id
  IS NULL` (the original catalog row, not the map-resolve duplicate — see
  0091); a mismatch makes that shrine a no-op;
- each target `ShrineHistory` matched by `shrine_id` + `history_type` +
  `title`; no match ⇒ that relation is skipped;
- the `ShrineKnowledgeSource` is looked up by exact `url` + `source_type`
  first (re-run reuses it — no duplicate Source row);
- `.add()` on the M2M is a no-op when the relation already exists (idempotent).

**Reverse safety — row ownership AND relation ownership**
(`docs/audit/source-backfill-id10-id22-reproducibility.md` §20 / §21).

Reverse must restore the exact PRE-forward semantic state, which means it has
to tell apart two independent kinds of ownership:

1. **Source-row ownership.** Forward stamps `MIGRATION_TAG` into
   `ShrineKnowledgeSource.note` **only on a row it `create()`s itself**. A
   pre-existing Source that forward merely *reuses* by `url` + `source_type`
   never gets that tag, and reverse never deletes such a row.

2. **Relation ownership.** A row-level tag cannot say *which* individual
   `history ↔ Source` links forward added — a reused Source may already cite
   some target histories (curated by hand) while forward adds the link to the
   others. So forward records the links it actually creates in a single
   delimited, append-only line in `note`:

       <original note><SEP>[temples.0096:added-histories] <type>::<title> | ...

   `SEP` is `"\n\n"`. The line lists **only** links this migration's forward
   pass newly created (target links that were absent beforehand). Reverse
   reads that line, removes exactly those links (matched against this entry's
   static `histories` spec — never trusting the free-text token), then
   restores `note` to the exact byte-for-byte prefix before
   `SEP + prefix`. A pre-existing link that forward left untouched is never
   recorded and never removed. If forward added no new link (every target link
   already existed) it writes no line and does not touch `note` at all.

This mirrors 0095's "reverse only undoes the exact state forward wrote" — at
the level of the individual relation.

Concretely (PRE = state before forward):

- **A. reused Source + target link already present** → forward adds nothing,
  writes no marker line; reverse is a no-op → the pre-existing link and row
  (and its curated `note`) are preserved untouched.
- **B. reused Source + target link absent** → forward adds the link and
  records it; reverse removes that link, strips its own `note` line back to
  the original, and keeps the row.
- **C. Source absent** → forward `create()`s it (tagged) and adds the links;
  reverse removes the links and deletes the row iff nothing else cites it.
- **D. mixed** — reused Source, history A already linked, history B not →
  forward records only B; reverse removes only B, keeps A, keeps the row.

`SELECT` on `Shrine` excludes `location` (`.only(...)`, the 0091/0094 legacy
`text`-column guard).
"""

from django.db import migrations
from django.db.models import F

SHRINE_LOOKUP_FIELDS = ("id", "name_jp", "place_ref_id", "updated_at")

VERIFIED_AT = "2026-08-29T00:00:00+00:00"

# Sentinel written to `ShrineKnowledgeSource.note` **only** on rows this
# migration's forward pass creates. Reverse deletes a Source row only if its
# `note` contains this exact marker (row ownership).
MIGRATION_TAG = "[temples.0096:auto-created]"
MIGRATION_NOTE = (
    MIGRATION_TAG
    + " P4 provenance backfill — created by data migration temples.0096; "
    "reverse of temples.0096 removes this row and the relations it added."
)

# Prefix of the single append-only line that records which `history ↔ Source`
# links forward newly created (relation ownership). Never written when forward
# added no new link. `ADDED_HISTORIES_SEP` always precedes it so reverse can
# restore the exact original `note` prefix.
ADDED_HISTORIES_PREFIX = "[temples.0096:added-histories]"
ADDED_HISTORIES_SEP = "\n\n"
_HISTORY_TOKEN_SEP = " | "
_TYPE_TITLE_SEP = "::"

# One reviewed Source per shrine + the existing histories it corroborates.
BACKFILL = [
    {
        "shrine_id": 10,
        "shrine_name": "鶴岡八幡宮",
        "source": {
            "source_type": "cultural_property",
            "title": "鶴岡八幡宮境内（史跡）｜文化遺産オンライン（文化庁）",
            "publisher": "文化庁",
            "url": "https://online.bunka.go.jp/heritages/detail/160978",
            "language": "ja",
            "confidence": "high",
        },
        # 源頼義の若宮勧請 / 治承4年(1180) 源頼朝の現在地遷座 — both stated on the record.
        # (history_type, title) — pk deliberately NOT used (differs Local vs Prod).
        "histories": [
            ("founding", "由比若宮の勧請"),
            ("historical_event", "現在地への遷座"),
        ],
    },
    {
        "shrine_id": 22,
        "shrine_name": "給田六所神社",
        "source": {
            "source_type": "government",
            "title": "給田六所神社（給田六所神社例大祭）｜地域伝統行事・民俗芸能等 情報発信サイト（文化庁）",
            "publisher": "文化庁",
            "url": "https://www.dentou-hasshin.bunka.go.jp/search/158.html",
            "language": "ja",
            "confidence": "high",
        },
        # 「武蔵国 大國魂神社の御分霊を招請して建立された氏神様」 — supports the founding history.
        "histories": [
            ("founding", "武蔵総社六所宮よりの分霊勧請"),
        ],
    },
]


def _target_shrine(Shrine, pk, expected_name):
    shrine = (
        Shrine.objects.only(*SHRINE_LOOKUP_FIELDS)
        .filter(pk=pk, name_jp=expected_name, place_ref_id__isnull=True)
        .order_by(F("place_ref_id").asc(nulls_first=True), "id")
        .first()
    )
    return shrine


def _find_source(ShrineKnowledgeSource, spec):
    return ShrineKnowledgeSource.objects.filter(
        url=spec["url"], source_type=spec["source_type"]
    ).first()


def _get_or_create_source(ShrineKnowledgeSource, spec):
    """Return ``(source, created_by_this_migration)``.

    A pre-existing row is reused **as-is** (``created`` is ``False``); its
    ``note`` is preserved verbatim except for the append-only
    relation-ownership line, which reverse strips back off. A newly created row
    carries ``MIGRATION_NOTE`` so reverse can tell it apart for row deletion.
    """
    src = _find_source(ShrineKnowledgeSource, spec)
    if src is not None:
        return src, False
    src = ShrineKnowledgeSource.objects.create(
        source_type=spec["source_type"],
        title=spec["title"],
        publisher=spec.get("publisher", ""),
        url=spec["url"],
        language=spec.get("language", ""),
        verification_status="source_confirmed",
        confidence=spec.get("confidence", ""),
        verified_at=VERIFIED_AT,
        note=MIGRATION_NOTE,
    )
    return src, True


def _matching_histories(ShrineHistory, shrine_id, specs):
    """Match by environment-stable identity only (shrine_id + type + title).

    `ShrineHistory` pk differs between the local dev DB and Production for the
    same seed Fact, so pk is never used here.
    """
    out = []
    for htype, title in specs:
        for h in ShrineHistory.objects.filter(
            shrine_id=shrine_id, history_type=htype, title=title
        ):
            out.append(h)
    return out


def _history_token(htype, title):
    return f"{htype}{_TYPE_TITLE_SEP}{title}"


def _parse_added_histories(note):
    """Return the set of ``type::title`` tokens recorded by forward, or ``None``
    if no relation-ownership line is present."""
    for line in (note or "").splitlines():
        stripped = line.strip()
        if stripped.startswith(ADDED_HISTORIES_PREFIX):
            rest = stripped[len(ADDED_HISTORIES_PREFIX):].strip()
            return {
                tok.strip()
                for tok in rest.split(_HISTORY_TOKEN_SEP.strip())
                if tok.strip()
            }
    return None


def _note_prefix_before_marker(note):
    """The exact original ``note`` text — everything before
    ``ADDED_HISTORIES_SEP + ADDED_HISTORIES_PREFIX``. Byte-for-byte reversible."""
    needle = ADDED_HISTORIES_SEP + ADDED_HISTORIES_PREFIX
    return (note or "").split(needle, 1)[0]


def _with_added_histories_line(base_note, tokens):
    return (
        base_note
        + ADDED_HISTORIES_SEP
        + ADDED_HISTORIES_PREFIX
        + " "
        + _HISTORY_TOKEN_SEP.join(tokens)
    )


def apply_source_backfill(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    ShrineHistory = apps.get_model("temples", "ShrineHistory")
    ShrineKnowledgeSource = apps.get_model("temples", "ShrineKnowledgeSource")

    for entry in BACKFILL:
        shrine = _target_shrine(Shrine, entry["shrine_id"], entry["shrine_name"])
        if shrine is None:
            continue
        histories = _matching_histories(ShrineHistory, shrine.id, entry["histories"])
        if not histories:
            continue

        src, _created = _get_or_create_source(ShrineKnowledgeSource, entry["source"])

        already_recorded = _parse_added_histories(src.note)

        # Links this forward pass newly creates (absent beforehand). Computed
        # BEFORE any `.add()`, and only when no prior forward pass has already
        # recorded its set — so re-running forward never rewrites or loses the
        # true PRE-forward relation ownership.
        newly_linked = []
        if already_recorded is None:
            for h in histories:
                if not h.sources.filter(pk=src.pk).exists():
                    newly_linked.append(h)

        for h in histories:
            h.sources.add(src)  # no-op if already related

        if already_recorded is None and newly_linked:
            tokens = [_history_token(h.history_type, h.title) for h in newly_linked]
            base_note = _note_prefix_before_marker(src.note)
            src.note = _with_added_histories_line(base_note, tokens)
            src.save(update_fields=["note"])


def revert_source_backfill(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    ShrineHistory = apps.get_model("temples", "ShrineHistory")
    ShrineKnowledgeSource = apps.get_model("temples", "ShrineKnowledgeSource")

    for entry in BACKFILL:
        shrine = _target_shrine(Shrine, entry["shrine_id"], entry["shrine_name"])
        if shrine is None:
            continue
        src = _find_source(ShrineKnowledgeSource, entry["source"])
        if src is None:
            continue

        recorded_tokens = _parse_added_histories(src.note)
        row_created_here = MIGRATION_TAG in (src.note or "")

        # Which target links did forward create? Only those it recorded, matched
        # against this entry's static spec (never trusting the free-text token).
        # Fallback: a forward-created row with no recorded line (should not
        # occur — a created row always has >=1 new link) owns every target
        # link. A reused row with no recorded line added nothing → no-op.
        if recorded_tokens is not None:
            owned_specs = [
                (htype, title)
                for (htype, title) in entry["histories"]
                if _history_token(htype, title) in recorded_tokens
            ]
        elif row_created_here:
            owned_specs = list(entry["histories"])
        else:
            owned_specs = []

        for h in _matching_histories(ShrineHistory, shrine.id, owned_specs):
            h.sources.remove(src)

        if row_created_here:
            # A row forward created: drop it unless something else now cites it.
            if not src.deities.exists() and not src.histories.exists():
                src.delete()
                continue

        if recorded_tokens is not None:
            # Reused (or surviving created) row: restore `note` to the exact
            # pre-forward text.
            restored = _note_prefix_before_marker(src.note)
            if restored != (src.note or ""):
                src.note = restored
                src.save(update_fields=["note"])


class Migration(migrations.Migration):

    dependencies = [
        ("temples", "0095_batch17_recommendation_evidence_activation"),
    ]

    operations = [
        migrations.RunPython(apply_source_backfill, revert_source_backfill),
    ]
