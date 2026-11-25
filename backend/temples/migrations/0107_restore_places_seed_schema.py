"""places_seed / places_seed_state の physical schema を復旧する repair migration。

背景:
    Production の physical schema から `places_seed` / `places_seed_state` が欠落している
    一方で、Django の ProjectState（`0106` 時点）には両 model とも存在する。
    欠けているのは physical table だけなので、この migration は
    **database-only repair** として扱う。

state 契約:
    ここでは ProjectState を変更しない。`CreateModel` を state operation として
    追加すると、`0075_placesseed_placesseedstate_and_more` の定義と二重になる。
    したがって operation は `RunPython` 1 本だけで、state は 0106 のまま前進しない。

方式:
    DDL を人間が書き起こさず、historical app registry から取り出した model を
    `schema_editor.create_model()` に渡して Django 自身に
    column / FK / constraint / index を生成させる。
    既に table が存在する環境（通常の開発環境・CI・fresh DB）では no-op になる。

reverse:
    NO-OP。0106 以前の ProjectState でも両 model は存在する扱いなので、
    reverse で physical table だけを DROP すると schema drift を作り直してしまう。
"""

from django.db import migrations

# 作成順序は依存関係の順に固定する（PlacesSeedState は PlacesSeed へ
# OneToOne(primary_key=True) で従属するため、先に PlacesSeed が必要）。
TARGET_MODEL_NAMES = ("PlacesSeed", "PlacesSeedState")


def _existing_table_names(schema_editor):
    return set(schema_editor.connection.introspection.table_names())


def _existing_column_names(schema_editor, table_name):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        return {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }


def restore_missing_tables(apps, schema_editor):
    """欠落している table だけを作成する。既存 table には一切触れない。"""
    existing_tables = _existing_table_names(schema_editor)

    for model_name in TARGET_MODEL_NAMES:
        model = apps.get_model("temples", model_name)
        table_name = model._meta.db_table

        if table_name not in existing_tables:
            schema_editor.create_model(model)
            existing_tables.add(table_name)
            continue

        # ここから先は「table は在るが中身が期待と違う」ケース。
        # この migration の責務は欠落 table の復旧であって、任意の schema 差分修復
        # ではない。推測で ALTER せず、silent success にもせず、fail-closed にする。
        expected_columns = {field.column for field in model._meta.local_fields}
        actual_columns = _existing_column_names(schema_editor, table_name)
        missing_columns = sorted(expected_columns - actual_columns)

        if missing_columns:
            raise RuntimeError(
                f"0107 aborted: table '{table_name}' exists but is missing expected "
                f"column(s): {', '.join(missing_columns)}. "
                "This migration only restores entirely missing tables and will not "
                "guess a column-level repair. Investigate the schema drift and decide "
                "the fix explicitly before re-running."
            )


def noop_reverse(apps, schema_editor):
    """reverse では physical table を DROP しない（module docstring 参照）。"""


class Migration(migrations.Migration):
    dependencies = [
        ("temples", "0106_weekly_presentation_snapshot_foundation"),
    ]

    operations = [
        migrations.RunPython(restore_missing_tables, noop_reverse),
    ]
