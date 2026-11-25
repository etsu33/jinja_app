"""Atomic bounded DDL. Referenced UNIQUEs precede composite FKs.
Reverse removes FKs before referenced UNIQUEs; no data repair or backfill.
"""

from django.db import migrations, models
from temples.constraints_highlights import CompositeForeignKey

DDL_LIMITS = "SET LOCAL lock_timeout = '5s'; SET LOCAL statement_timeout = '60s';"


class Migration(migrations.Migration):
    atomic = True
    dependencies = [("temples", "0124_highlight_translation_location_hint")]
    operations = [
        migrations.RunSQL(DDL_LIMITS, reverse_sql=migrations.RunSQL.noop),
        migrations.AddConstraint(
            model_name="shrinehighlight",
            constraint=models.UniqueConstraint(fields=["id", "shrine"], name="hl_id_shrine_unique"),
        ),
        migrations.AddConstraint(
            model_name="shrinehistory",
            constraint=models.UniqueConstraint(
                fields=["id", "shrine"], name="history_id_shrine_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="shrinehighlighthistory",
            constraint=CompositeForeignKey(
                name="hl_history_highlight_shrine_fk",
                fields=["highlight", "shrine"],
                to_model="temples.ShrineHighlight",
                to_fields=["id", "shrine"],
            ),
        ),
        migrations.AddConstraint(
            model_name="shrinehighlighthistory",
            constraint=CompositeForeignKey(
                name="hl_history_history_shrine_fk",
                fields=["history", "shrine"],
                to_model="temples.ShrineHistory",
                to_fields=["id", "shrine"],
            ),
        ),
        # Reverse starts here, so its DDL has the same time limits.
        migrations.RunSQL(migrations.RunSQL.noop, reverse_sql=DDL_LIMITS),
    ]
