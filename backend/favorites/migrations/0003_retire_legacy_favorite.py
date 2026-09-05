# backend/favorites/migrations/0003_retire_legacy_favorite.py
"""legacy `favorites.Favorite`（table `favorites_favorite`）の退役 — Stage 1。

live 正本は `temples.models.Favorite`（table `temples_favorite`）であり、本 app の
`Favorite` は別 schema の legacy model。runtime consumer は 0 件だが、Production の
table に残存 row がある可能性を排除できないため、**DeleteModel の前に必ず件数を確認する
fail-safe guard** を置く。

guard は row が 1 件でも存在したら `LegacyFavoritesDataFound` を raise して migration 全体を
失敗させる。PostgreSQL は DDL が transactional で、Django の migration は既定で atomic の
ため、guard が失敗した時点で transaction ごと rollback され、table も row も一切変更されない。
データの自動削除は行わない（人間が中身を確認して判断する）。

operation 順序は `guard -> DeleteModel` を必ず維持すること。
"""

from django.db import migrations

# 失敗を機械的に識別するための marker。テストと運用ログの双方から参照する。
LEGACY_DATA_MARKER = "LEGACY_FAVORITES_DATA_PRESENT"

LEGACY_TABLE = "favorites_favorite"


class LegacyFavoritesDataFound(RuntimeError):
    """legacy favorites table に row が残っている状態で 0003 が実行された。"""


def guard_legacy_favorites_is_empty(apps, schema_editor):
    """`favorites_favorite` が空でなければ migration を STOP させる。

    historical model を使う（runtime の `from favorites.models import Favorite` は
    このモジュール削除後に壊れるため禁止）。
    """
    Favorite = apps.get_model("favorites", "Favorite")
    row_count = Favorite.objects.using(schema_editor.connection.alias).count()
    if row_count:
        raise LegacyFavoritesDataFound(
            f"{LEGACY_DATA_MARKER}: legacy favorites table '{LEGACY_TABLE}' still holds "
            f"{row_count} row(s). This migration does NOT delete them automatically. "
            f"Migration STOPPED before DeleteModel; no table or row was modified "
            f"(the transaction is rolled back). Inspect '{LEGACY_TABLE}', migrate or "
            f"archive the data by hand, then re-run this migration."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("favorites", "0002_remove_favorite_favorites_f_user_id_5e9d49_idx_and_more"),
    ]

    operations = [
        # 1) 先に空であることを保証する（空でなければここで migration が失敗する）
        migrations.RunPython(
            guard_legacy_favorites_is_empty,
            migrations.RunPython.noop,
        ),
        # 2) 空だった場合にのみ model / table を削除する
        migrations.DeleteModel(name="Favorite"),
    ]
