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
- `.add()` on the M2M is a no-op when the relation already exists (idempotent);
- reverse removes exactly the relations this migration added and deletes the
  Source row only when it is left with no remaining relations.

`SELECT` on `Shrine` excludes `location` (`.only(...)`, the 0091/0094 legacy
`text`-column guard).
"""

from django.db import migrations
from django.db.models import F

SHRINE_LOOKUP_FIELDS = ("id", "name_jp", "place_ref_id", "updated_at")

VERIFIED_AT = "2026-08-29T00:00:00+00:00"

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


def _get_or_create_source(ShrineKnowledgeSource, spec, *, create):
    src = ShrineKnowledgeSource.objects.filter(
        url=spec["url"], source_type=spec["source_type"]
    ).first()
    if src is not None or not create:
        return src
    return ShrineKnowledgeSource.objects.create(
        source_type=spec["source_type"],
        title=spec["title"],
        publisher=spec.get("publisher", ""),
        url=spec["url"],
        language=spec.get("language", ""),
        verification_status="source_confirmed",
        confidence=spec.get("confidence", ""),
        verified_at=VERIFIED_AT,
    )


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
        src = _get_or_create_source(ShrineKnowledgeSource, entry["source"], create=True)
        for h in histories:
            h.sources.add(src)  # no-op if already related


def revert_source_backfill(apps, schema_editor):
    Shrine = apps.get_model("temples", "Shrine")
    ShrineHistory = apps.get_model("temples", "ShrineHistory")
    ShrineKnowledgeSource = apps.get_model("temples", "ShrineKnowledgeSource")

    for entry in BACKFILL:
        shrine = _target_shrine(Shrine, entry["shrine_id"], entry["shrine_name"])
        if shrine is None:
            continue
        src = _get_or_create_source(ShrineKnowledgeSource, entry["source"], create=False)
        if src is None:
            continue
        histories = _matching_histories(ShrineHistory, shrine.id, entry["histories"])
        for h in histories:
            h.sources.remove(src)
        # delete the Source only if nothing else references it anymore
        if not src.deities.exists() and not src.histories.exists():
            src.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("temples", "0095_batch17_recommendation_evidence_activation"),
    ]

    operations = [
        migrations.RunPython(apply_source_backfill, revert_source_backfill),
    ]
