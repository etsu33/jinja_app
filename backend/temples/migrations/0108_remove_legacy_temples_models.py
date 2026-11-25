"""legacy な temples model 4件を正式に退役させる。

対象（Mother Ship Decision D1-D4 = REMOVE）:
    Like                            -> temples_like
    ConciergeRecommendationClickLog -> temples_concierge_recommendation_click_log
    ConciergeHistory                -> temples_conciergehistory
    RankingLog                      -> temples_rankinglog

いずれも現行コードからの参照が 0 件（`.objects` 使用なし、API reader/writer なし、
ACTIVE model からの FK/O2O/M2M なし）であることを実装前 audit で確認済み。

なぜ plain DeleteModel を使わないか:
    Production ではこの 4 table が既に physical missing である。
    `DeleteModel` は `DROP TABLE`（IF EXISTS なし）を発行するため、
    Production で適用すると存在しない table に対して失敗する。
    一方 fresh DB / CI では historical migration により table が存在する。
    両方の環境で成立させるため、`SeparateDatabaseAndState` で
    database 側（`DROP TABLE IF EXISTS`）と state 側（`DeleteModel`）を分離する。

CASCADE を付けない理由:
    この 4 model を参照する残存 model は存在しない（audit 実測）。
    もし `DROP TABLE IF EXISTS` だけで失敗するなら、それは未知の依存が
    active schema 側に存在することを意味するので、CASCADE で押し通さずに
    失敗させて調査する。

reverse:
    このmigrationは**意図的に irreversible**。
    reverse を no-op にすると「state だけ 4 model が復活し、physical table は
    復活しない」という新しい schema drift を作ってしまう。
    安全な reverse には canonical な CREATE schema が必要で、それは legacy model の
    正式退役という本migrationの目的と矛盾する。
    先頭の RunPython ガードにより、`Migration.unapply()` は Phase 1 で
    `IrreversibleError` を送出し、**database も state も一切変更しないまま停止**する。
"""

from django.db import migrations

# db_table は model metadata と historical migration の双方で確認した値。
# 推測で書かない。
#   temples_like                                -> 0044（db_table 指定なし＝既定名）
#   temples_concierge_recommendation_click_log  -> 0076（db_table 明示）
#   temples_conciergehistory                    -> 0001_initial（既定名）
#   temples_rankinglog                          -> 0001_initial（既定名）
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
        ("temples", "0107_restore_places_seed_schema"),
    ]

    operations = [
        # reverse_code=None により reversible=False となり、unapply は
        # IrreversibleError で即座に停止する（module docstring 参照）。
        migrations.RunPython(_forwards_noop, reverse_code=None),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # reverse_sql は指定しない（= None）。no-op reverse は禁止。
                migrations.RunSQL(sql=f'DROP TABLE IF EXISTS "{table}";')
                for table in LEGACY_TABLES
            ],
            state_operations=[
                migrations.DeleteModel(name=model_name) for model_name in LEGACY_MODELS
            ],
        ),
    ]
