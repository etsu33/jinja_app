"""Remove unsupported Recommendation Evidence M2M tags from shrine ids 21 / 22.

P5-DATA — `docs/audit/p5-id21-id22-tag-reconciliation.md`, following the merged
P5 preflight (`docs/audit/p5-id21-id22-current-state-evidence.md`) and the
FINAL Mother Ship decisions P5-1..P5-5.

These `goriyaku_tags` relations were **hand-set** by migration 0091 as a LEGACY
"reason fill" for two zero/weak-Knowledge local shrines — from a hard-coded name
list, **not** parse-derived, **not** backed by any reviewed Source. Under the
current Recommendation Evidence Review Contract their eligibility is `UNKNOWN`
(no reviewed Source states the benefit). This migration removes them so that
current Recommendation Evidence reflects current reviewed evidence.

**This is NOT a factual/metaphysical denial of shrine tradition.** It only means
KAMI MUSUBI's current reviewed evidence is insufficient to use these labels as
Recommendation Evidence. A future reviewed Source discovery may re-activate them
in a separate task.

Removed:

- id 21 長太稲荷神社: `商売繁盛`, `五穀豊穣`  (Decision P5-1)   + `地域安泰` if present (Decision P5-3)
- id 22 給田六所神社: `家内安全`              (Decision P5-2)   + `地域安泰` if present (Decision P5-3)

Explicitly **NOT** changed (Decision P5-4): `Shrine.goriyaku` raw prose,
`Shrine.history_theme`. Also unchanged: every `ShrineDeity` / `ShrineHistory` /
`ShrineKnowledgeSource` row and field, the `GoriyakuTag` master taxonomy,
`NEED_TO_GORIYAKU_IDS`, and all Recommendation / ranking / scoring code.

**Local/Production reproducibility.** The local dev DB (`jinja_db`) carries a
drifted 46-row `GoriyakuTag` table while Production has the clean 39-row master,
so PKs differ per label (`商売繁盛` = 4 in Production, 17 locally). Tags are
therefore matched by **exact canonical name**, never by PK. `地域安泰` is a
legacy label **absent from the Production master** — matching it by name makes
its cleanup a safe no-op in Production and an actual removal in the drifted
local DB, converging both environments.

Scope: **exactly shrine ids 21 and 22**, catalog rows only (`place_ref_id IS
NULL`); the `place_ref`-set duplicate shadow rows (103 / 101) are never touched.
Deterministic, reversible (0090 / 0091 / 0094 / 0095 pattern). No
`get_or_create`; a missing tag name is simply skipped in both directions.

**Reverse safety — fail-closed precondition guard, not persisted ownership.**
Follow-up Mother Ship decisions: `0097_REVERSE_CONTRACT=STRICT_EXACT` /
`OWNERSHIP_STORAGE=NOT_REQUIRED` / `FORWARD_POLICY=PRECONDITION_GUARDED_FAIL_CLOSED`
/ `SCHEMA_CHANGE=REJECTED`.

Unlike migration 0096 (which persists per-relation ownership into
`ShrineKnowledgeSource.note`, because its forward pass may *reuse* an
independently pre-existing row), 0097's forward pass never creates or reuses
anything ambiguous — it only removes a small, statically-known set of
`Shrine <-> GoriyakuTag` relations. Neither `Shrine` nor `GoriyakuTag` has a
field safe to use as ownership-marker storage without corrupting real,
displayed/scored content (`Shrine.goriyaku` is the documented display
fallback once `goriyaku_tags` is emptied — Decision P5-4 forbids touching
it) or without a schema change (an explicit `through` model, or a dedicated
ledger table) — both rejected as disproportionate to this migration's
narrow, one-off reconciliation scope.

Instead, forward is split into two phases:

1. **Validate** (read-only, no mutation). For every entry's *required*
   names (the canonical P5-1 / P5-2 removals), forward confirms the
   `GoriyakuTag` row exists **and** the shrine currently has that relation.
   If a target shrine's identity does not match (existing guard, unchanged —
   see `_target_shrine`), that target is skipped exactly as before — an
   identity mismatch is not a precondition violation, it is "this pk is not
   (or no longer) the target". But if identity *does* match and any required
   tag or required relation is missing, forward raises
   `PreconditionViolation` **before mutating anything, for any target** —
   this is deliberately all-or-nothing across every entry in `RECONCILE`,
   not per-shrine.

   The *optional* `地域安泰` name (P5-3) is validated in the same phase under
   a 3-state STRICT_EXACT contract, not the plain required-relation rule:
     - tag row absent → not an error, simply skipped (best-effort, unchanged).
     - tag row present **and** relation present → validated for removal.
     - tag row present **but relation absent** → `PreconditionViolation`,
       same as a missing required relation. Without this, forward would
       treat it as a silent no-op while reverse's unconditional re-add would
       still `.add()` it, fabricating a relation that never existed
       pre-forward — exactly the STRICT_EXACT round-trip break this
       migration exists to prevent for the required relations.
2. **Mutate**. Reached only if every target passed validation. Removes the
   required relations and the optional relations validated in step 1
   (guaranteed present by step 1 in both cases) — nothing is removed, or
   even attempted, for an optional name whose row never existed.

A successful forward therefore implies: every relation reverse will
re-attach — required or optional — existed immediately before forward ran.
Reverse can then safely re-add the static required + optional tag sets —
this is now an **exact** round trip by construction (forward's own
precondition check covers both), not because reverse tracks which
relations it personally removed.

`Migration.atomic` is left at its Django default (`True`) — the whole
`RunPython` call runs inside one DB transaction, so a `PreconditionViolation`
raised mid-validation (or any exception mid-mutation) leaves zero relations
changed. No manual transaction handling is added.

Forward is intentionally **not** safely re-runnable after a successful
apply (`SAFE_REAPPLY = FAIL_CLOSED`, superseding the earlier idempotent-
forward contract): since forward removes the required relations, calling it
again finds them already absent and raises `PreconditionViolation`. Django
does not apply the same migration twice in ordinary operation; the real
retry path is `reverse` then `forward` again (tested).
"""

from django.db import migrations
from django.db.models import F

SHRINE_LOOKUP_FIELDS = ("id", "name_jp", "place_ref_id", "updated_at")

# (shrine pk, expected name_jp, required canonical tag names, optional legacy
# tag names). required = P5-1 / P5-2 canonical removals, forward-time
# precondition-checked (fail-closed). optional = P5-3 `地域安泰` -- also
# forward-time precondition-checked, but under the 3-state STRICT_EXACT
# contract in `_validate_target`: a missing tag row is a skip (never
# created), while a tag row present with no relation is a
# `PreconditionViolation` (never silently ignored).
RECONCILE = [
    (21, "長太稲荷神社", ["商売繁盛", "五穀豊穣"], ["地域安泰"]),
    (22, "給田六所神社", ["家内安全"], ["地域安泰"]),
]


class PreconditionViolation(Exception):
    """Raised by `reconcile_forward` when a target shrine's identity matches
    but a required `GoriyakuTag` row or required `Shrine <-> GoriyakuTag`
    relation is missing at forward time. Always raised before any mutation,
    for any target — see module docstring "fail-closed precondition guard"."""


def _target_shrine(Shrine, pk, expected_name):
    """The catalog row for this shrine (pk + exact name + no place_ref).

    A mismatch (renamed row, or only a `place_ref`-set duplicate present) makes
    that shrine a no-op — the duplicate shadow rows 103 / 101 are never hit.
    This existing identity guard is unchanged: an identity mismatch is not a
    precondition violation.
    """
    return (
        Shrine.objects.only(*SHRINE_LOOKUP_FIELDS)
        .filter(pk=pk, name_jp=expected_name, place_ref_id__isnull=True)
        .order_by(F("place_ref_id").asc(nulls_first=True), "id")
        .first()
    )


def _tags_by_name(GoriyakuTag, names):
    """Existing GoriyakuTag rows for `names`, matched by exact name (never PK).

    Names with no row (e.g. `地域安泰` in Production) are simply absent from the
    result — never created.
    """
    return list(GoriyakuTag.objects.filter(name__in=names))


def _validate_target(Shrine, GoriyakuTag, pk, expected_name, required_names, optional_names):
    """Phase 1 (read-only, no mutation).

    Returns ``(shrine, required_tags, optional_tags)``. ``shrine`` is
    ``None`` if this target's identity does not match (existing no-op
    contract, unchanged).

    Required names: raises `PreconditionViolation` if the shrine's identity
    matches but any required `GoriyakuTag` row, or the relation between it
    and the shrine, is missing.

    Optional names (STRICT_EXACT 3-state contract): a missing `GoriyakuTag`
    row is not an error -- that name is simply skipped (best-effort, as
    before). But if the row *does* exist, its relation to the shrine must
    also exist -- an optional tag row present with no relation would let
    `reconcile_reverse`'s unconditional re-add fabricate a relation that
    never existed pre-forward, so that combination is itself a
    `PreconditionViolation`, exactly like a missing required relation.
    """
    shrine = _target_shrine(Shrine, pk, expected_name)
    if shrine is None:
        return None, [], []

    required_tags = []
    for name in required_names:
        tag = GoriyakuTag.objects.filter(name=name).first()
        if tag is None:
            raise PreconditionViolation(
                f"temples.0097: required GoriyakuTag '{name}' does not exist "
                f"(shrine pk={pk})"
            )
        if not shrine.goriyaku_tags.filter(pk=tag.pk).exists():
            raise PreconditionViolation(
                f"temples.0097: required relation shrine pk={pk} <-> "
                f"GoriyakuTag '{name}' is missing at forward time"
            )
        required_tags.append(tag)

    optional_tags = []
    for name in optional_names:
        tag = GoriyakuTag.objects.filter(name=name).first()
        if tag is None:
            continue  # optional tag row absent -- not an error, simply skipped
        if not shrine.goriyaku_tags.filter(pk=tag.pk).exists():
            raise PreconditionViolation(
                f"temples.0097: optional GoriyakuTag '{name}' exists but its "
                f"relation to shrine pk={pk} is missing at forward time"
            )
        optional_tags.append(tag)

    return shrine, required_tags, optional_tags


def reconcile_forward(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    GoriyakuTag = apps.get_model("temples", "GoriyakuTag")

    # Phase 1 -- Validate every target (required AND optional relations). No
    # mutation happens in this loop. A PreconditionViolation on any one
    # target -- required or optional -- aborts before Phase 2 runs for *any*
    # target (fail-closed, all-or-nothing across the whole RECONCILE list --
    # not per-shrine).
    validated = []
    for pk, expected_name, required_names, optional_names in RECONCILE:
        shrine, required_tags, optional_tags = _validate_target(
            Shrine, GoriyakuTag, pk, expected_name, required_names, optional_names
        )
        validated.append((shrine, required_tags, optional_tags))

    # Phase 2 -- Mutate. Reached only if every target passed Phase 1. Only the
    # optional relations validated in Phase 1 (row exists AND relation
    # exists) are removed here -- an absent optional row was already skipped
    # in Phase 1 and never reaches this loop.
    for shrine, required_tags, optional_tags in validated:
        if shrine is None:
            continue
        if required_tags:
            shrine.goriyaku_tags.remove(*required_tags)
        if optional_tags:
            shrine.goriyaku_tags.remove(*optional_tags)


def reconcile_reverse(apps, schema_editor):
    """Re-attach exactly the required + optional relations from the static
    spec.

    Safe as an EXACT round trip for both the required AND optional relations
    because `reconcile_forward`'s Phase 1 now guarantees each existed
    immediately before Phase 2 removed it (see module docstring's 3-state
    optional contract). The optional `地域安泰` relation is still only
    re-added if its `GoriyakuTag` row exists in this environment (never
    created) -- but that row's absence is the only remaining reason it would
    be skipped, since forward already refuses to run at all if the row
    exists without the relation.
    """
    Shrine = apps.get_model("temples", "Shrine")
    GoriyakuTag = apps.get_model("temples", "GoriyakuTag")

    for pk, expected_name, required_names, optional_names in RECONCILE:
        shrine = _target_shrine(Shrine, pk, expected_name)
        if shrine is None:
            continue
        tags = _tags_by_name(GoriyakuTag, required_names + optional_names)
        if tags:
            shrine.goriyaku_tags.add(*tags)  # no-op for a tag already attached


class Migration(migrations.Migration):

    dependencies = [
        ("temples", "0096_source_backfill_id10_id22"),
    ]

    operations = [
        migrations.RunPython(reconcile_forward, reconcile_reverse),
    ]
