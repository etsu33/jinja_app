"""テスト用：本番の GoriyakuTag 39件の「番号 → 名前」。

相談の種類との一致は札の名前から概念を引いて決める（temples.domain.need_to_goriyaku_concepts）。
番号で候補を作っていたテストは、この表で名前を足す（goriyaku_tag_names）。
番号は docs/audit/goriyaku-mapping-master-integrity.md の本番の正本と同じ。
"""

from __future__ import annotations

from typing import Iterable, List

CANONICAL_GORIYAKU_TAG_NAME_BY_ID = {
    1: "縁結び", 2: "厄除け", 3: "交通安全", 4: "商売繁盛", 5: "五穀豊穣", 6: "開運",
    7: "家内安全", 8: "福徳", 9: "学業成就", 10: "合格祈願", 11: "勝運", 12: "仕事運",
    13: "航海安全", 14: "海上安全", 15: "武運長久", 16: "安産", 17: "八方除", 18: "夫婦円満",
    19: "八難除", 20: "恋愛成就", 21: "導き", 22: "美容", 23: "方除け", 24: "健康長寿",
    25: "芸能", 26: "家庭円満", 27: "出世運", 28: "金運", 29: "芸能運", 30: "強運厄除け",
    31: "技芸上達", 32: "八方除け", 33: "病気平癒", 34: "火防", 35: "子宝", 36: "心願成就",
    37: "延命長寿", 38: "足腰健康", 39: "農業守護",
}


def canonical_tag_names(goriyaku_tag_ids: Iterable[int]) -> List[str]:
    """本番の番号の一覧を、札の名前の一覧にする（知らない番号は飛ばす）。"""
    return [CANONICAL_GORIYAKU_TAG_NAME_BY_ID[int(i)] for i in goriyaku_tag_ids if int(i) in CANONICAL_GORIYAKU_TAG_NAME_BY_ID]
