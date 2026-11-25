"""本番から削除した神社の一覧（名前, 住所）。

Base Seed と知識データ（knowledge_seeds）は「後ろに足すだけ」の決まりで行を外せない。
ここに載せた神社は、取り込みで作り直さず、知識データの取り込みでも飛ばす。
削除前の控えは Google ドライブ「KAMIMUSUBI」フォルダの
「削除前の控え_長太稲荷神社・給田六所神社_2026-11-12.json」。
"""

from __future__ import annotations

REMOVED_SHRINES: frozenset[tuple[str, str]] = frozenset(
    {
        # 地域の氏神様のため削除（2026-11-12）
        ("長太稲荷神社", "日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０"),
        ("給田六所神社", "日本、〒157-0064 東京都世田谷区給田１丁目３−７"),
    }
)


def is_removed_shrine(name_jp: str, address: str) -> bool:
    return ((name_jp or "").strip(), (address or "").strip()) in REMOVED_SHRINES
