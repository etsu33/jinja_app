# backend/common/storage_cleanup.py
"""DB row の削除に合わせて、Storage 上の実ファイルも削除する共通契約。

Account Deletion 専用ではない。通常の Profile / Goshuin の削除・差し替えでも
同じ契約を使う。

守る境界:
    - Storage の削除は **DB transaction が commit されたあと**に行う。
      commit 前に消すと、rollback したときに DB には残っているのにファイルだけ
      失われる（復旧不能）。
    - rollback した場合は削除しない。`transaction.on_commit` は rollback 時に
      callback を破棄するため、これは自動的に満たされる。
    - Local / R2 で分岐しない。`FieldFile.storage` の abstraction をそのまま使う。
    - 失敗を握りつぶさない。ERROR log を残す。

log に出さないもの:
    - ファイル名（利用者がアップロードした名前を含みうる）
    - 例外メッセージと traceback
      boto3 系の例外は bucket / key を本文へ含めることがあり、key は
      ファイル名そのもの。credential が載る可能性も排除できない。
      そのため例外の **型名だけ** を出す。traceback を出さないのは意図的で、
      これは可観測性より PII 非出力を優先した判断。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from django.db import transaction

logger = logging.getLogger(__name__)


def _safe_prefix(name: str) -> str:
    """log に出してよい範囲。`upload_to` 由来の固定ディレクトリだけを残す。

    "icons/abc.png" -> "icons/"
    "goshuin/2026/x.jpg" -> "goshuin/2026/"
    ファイル名本体は落とすので、利用者由来の文字列は出ない。
    """
    if "/" not in name:
        return "<root>"
    return name.rsplit("/", 1)[0] + "/"


def delete_stored_file(storage: Any, name: str) -> bool:
    """今すぐ storage から削除する。成功したら True。

    `storage.exists()` は事前確認しない。S3/R2 では往復が1回増えるだけで、
    存在しない key への delete は成功扱いになるため、確認する利点がない。
    """
    try:
        storage.delete(name)
        return True
    except Exception as exc:
        logger.error(
            "[storage-cleanup] failed to delete stored file "
            "storage=%s prefix=%s error_type=%s "
            "(DB row is already deleted; the file is now orphaned and needs manual cleanup)",
            type(storage).__name__,
            _safe_prefix(name),
            type(exc).__name__,
        )
        return False


def schedule_stored_file_delete(fieldfile: Optional[Any]) -> None:
    """FieldFile の実ファイル削除を、transaction commit 後へ予約する。

    storage と name は **予約時点で確保する**。commit 時には instance が既に
    DB から消えており、FieldFile を参照し直せる保証がないため。
    """
    if not fieldfile:
        return

    name = getattr(fieldfile, "name", None) or ""
    if not name:
        return

    storage = getattr(fieldfile, "storage", None)
    if storage is None:
        return

    # on_commit は rollback 時に callback を破棄する。
    # = DB が巻き戻ったらファイルも消さない、が自動的に成立する。
    transaction.on_commit(lambda: delete_stored_file(storage, name))
