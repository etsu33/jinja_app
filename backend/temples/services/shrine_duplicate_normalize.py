"""
神社・住所の重複候補検索用の正規化（serializer/view には置かない）。
"""

from __future__ import annotations

import re

# 住所でハイフン類を ASCII ハイフンへ寄せる（長音 ー は住所表記でもダッシュ誤用されうるため含める）
_ADDRESS_DASH_CHARS = (
    "\u2212",  # − MINUS SIGN
    "\u2010",  # ‐ HYPHEN
    "\u2011",  # ‑ NON-BREAKING HYPHEN
    "\u2012",  # ‒ FIGURE DASH
    "\u2013",  # – EN DASH
    "\u2014",  # — EM DASH
    "\u30fc",  # ー KATAKANA-HIRAGANA PROLONGED SOUND MARK
)


def normalize_shrine_name_for_duplicate(value: str) -> str:
    """
    神社名の正規化（比較・検索用）。
    - trim
    - 全角スペース → 半角スペース
    - 連続空白 → 1 つ
    - 全角括弧 → 半角 ()
    """
    s = (value or "").strip()
    s = s.replace("\u3000", " ")
    s = " ".join(s.split())
    s = s.replace("（", "(").replace("）", ")")
    return s


def shrine_name_duplicate_base_key(normalized_name: str) -> str:
    """
    正規化済み神社名から括弧内を除いた比較用キー。
    例: 神田神社(神田明神) -> 神田神社
    """
    s = (normalized_name or "").strip()
    if not s:
        return ""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\([^()]*\)", "", s)
        s = " ".join(s.split())
    return s.strip()


def normalize_shrine_address_for_duplicate(value: str) -> str:
    """
    住所の簡易正規化（比較・検索用）。
    - trim
    - 全角・半角スペース・タブ等の空白を除去
    - ダッシュ類を ASCII '-' に寄せる
    - 都道府県名は削除しない
    - 丁目・番地の厳密な表記ゆれは扱わない
    """
    s = (value or "").strip()
    for sp in ("\u3000", " ", "\t", "\n", "\r", "\f", "\v"):
        s = s.replace(sp, "")
    for ch in _ADDRESS_DASH_CHARS:
        s = s.replace(ch, "-")
    return s
