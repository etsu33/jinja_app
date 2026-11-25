"""NoGIS lineage 側で legacy な temples model 4件を退役させる。

主系の `temples/migrations/0108_remove_legacy_temples_models.py` と
**同一の 4 model / 同一の 4 table** を対象にする。NoGIS lineage は
test/CI 専用（`TEMPLES_USE_NOGIS_MIGRATIONS` が真のときだけ使われる）だが、
`makemigrations --check` はこの lineage の final state と現行 model 定義を
突き合わせるため、主系だけを更新すると drift として検出される。

対象 model はいずれも NoGIS 側では
`0008_actionevent_conciergehistory_and_more` が作成している。
既存の NoGIS migration は 1 行も変更していない（forward に 1 本足すだけ）。

実装方針は主系 0108 と同じ:
    - `SeparateDatabaseAndState` で database 側と state 側を分離する
    - database 側は `DROP TABLE IF EXISTS`（CASCADE は使わない）
    - reverse は no-op にせず、先頭の RunPython ガードで明示的に
      `IrreversibleError` を送出させる
"""

from django.db import migrations

LEGACY_TABLES = (
    "temples_like",
    "temples_concierge_recommendation_click_log",
    "temples_conciergehistory",
    "temples_rankinglog",
)

LEGACY_MODELS = (
    "Like",
    "ConciergeRecommendationClickLog",
    "ConciergeHistory",
    "RankingLog",
)


def _forwards_noop(apps, schema_editor):
    """forward では何もしない。reverse を明示的に不可能にするためのガード。"""


class Migration(migrations.Migration):
    dependencies = [
        ("temples", "0012_weekly_presentation_snapshot_foundation"),
    ]

    operations = [
        migrations.RunPython(_forwards_noop, reverse_code=None),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(sql=f'DROP TABLE IF EXISTS "{table}";') for table in LEGACY_TABLES
            ],
            state_operations=[
                migrations.DeleteModel(name=model_name) for model_name in LEGACY_MODELS
            ],
        ),
    ]
