"""英語版の特徴語を、神社ごとに当てはめたもの（10社）。

正本は Google スプレッドシート
「KAMI MUSUBI 英語版の特徴語と10社の当てはめ表」の「当てはめ表」タブ（2026-11-12）。
根拠の引用文と出典URLはスプレッドシートにある。ここには特徴語のIDだけを写す。
変えるときはスプレッドシートを先に直し、この定数に手で反映する。

神社は ID ではなく、神社の知識データ（temples/data/knowledge_seeds）と同じ
正式名称＋住所で持つ。本番の神社への結びつけは resolve_shrine が行う。

この段は「記録する」だけで、並び順には使わない（作業の順番3の検証用）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

SHRINE_FEATURES_VERSION = "2026-11-12"


@dataclass(frozen=True)
class ShrineFeatureEntry:
    name_jp: str
    address: str
    feature_ids: Tuple[str, ...]


SHRINE_FEATURES: Tuple[ShrineFeatureEntry, ...] = (
    ShrineFeatureEntry(
        name_jp="日枝神社",
        address="東京都千代田区永田町2-10-5",
        feature_ids=(
            "S_FOREST",
            "F_URBAN_OASIS",
            "C_VERMILION",
            "C_TREASURE_HALL",
            "ST_SHOGUN",
            "ST_IMPERIAL",
            "F_FESTIVAL",
            "F_PERFORMANCE",
            "F_CAFE",
            "F_GOSHUIN",
        ),
    ),
    ShrineFeatureEntry(
        name_jp="赤坂氷川神社",
        address="東京都港区赤坂6-10-12",
        feature_ids=(
            "S_FOREST",
            "F_URBAN_OASIS",
            "S_GIANT_TREE",
            "S_AUTUMN",
            "S_FLOWERS",
            "C_HERITAGE",
            "C_ORIGINAL_BUILDINGS",
            "C_OLDEST",
            "ST_SHOGUN",
            "ST_ANCIENT",
            "F_QUIET",
            "F_FESTIVAL",
            "F_PERFORMANCE",
            "F_GOSHUIN",
            "F_CHARM",
        ),
    ),
    ShrineFeatureEntry(
        name_jp="根津神社",
        address="東京都文京区根津1-28-9",
        feature_ids=(
            "S_FOREST",
            "F_URBAN_OASIS",
            "S_FLOWERS",
            "C_HERITAGE",
            "C_ORIGINAL_BUILDINGS",
            "ST_SHOGUN",
            "ST_ANCIENT",
            "ST_MYTH",
            "ST_SYNCRETISM",
            "F_FESTIVAL",
        ),
    ),
    ShrineFeatureEntry(
        name_jp="神田神社（神田明神）",
        address="東京都千代田区外神田2-16-2",
        feature_ids=(
            "C_VERMILION",
            "C_HERITAGE",
            "C_CARVINGS",
            "S_GIANT_TREE",
            "C_TREASURE_HALL",
            "ST_SHOGUN",
            "ST_SAMURAI",
            "ST_SPIRIT_LEGEND",
            "ST_ANCIENT",
            "ST_POP_CULTURE",
            "F_FESTIVAL",
            "F_CEREMONY",
            "F_CHARM",
        ),
    ),
    ShrineFeatureEntry(
        name_jp="湯島天満宮",
        address="東京都文京区湯島3-30-1",
        feature_ids=(
            "S_FLOWERS",
            "S_STEPS",
            "ST_SCHOLAR",
            "ST_ANCIENT",
            "ST_SHOGUN",
            "ST_POP_CULTURE",
            "C_TREASURE_HALL",
            "F_PHOTO",
            "F_FESTIVAL",
        ),
    ),
    ShrineFeatureEntry(
        name_jp="武蔵御嶽神社",
        address="東京都青梅市御岳山176",
        feature_ids=(
            "S_MOUNTAIN",
            "S_VIEW",
            "S_STEPS",
            "F_HIKE",
            "ST_ANIMAL",
            "ST_MYTH",
            "ST_MOUNTAIN_WORSHIP",
            "ST_SAMURAI",
            "ST_SYNCRETISM",
            "ST_ANCIENT",
            "C_HERITAGE",
            "C_ORIGINAL_BUILDINGS",
            "F_DOG",
        ),
    ),
    ShrineFeatureEntry(
        name_jp="鶴岡八幡宮",
        address="神奈川県鎌倉市雪ノ下2-1-31",
        feature_ids=(
            "S_STEPS",
            "S_VIEW",
            "S_POND",
            "S_FLOWERS",
            "C_HERITAGE",
            "ST_SAMURAI",
            "F_FESTIVAL",
            "F_CEREMONY",
            "F_PHOTO",
        ),
    ),
    ShrineFeatureEntry(
        name_jp="日光東照宮",
        address="栃木県日光市山内2301",
        feature_ids=(
            "C_NATIONAL_TREASURE",
            "C_WORLD_HERITAGE",
            "C_CARVINGS",
            "C_ORIGINAL_BUILDINGS",
            "C_TREASURE_HALL",
            "S_TREE_AVENUE",
            "ST_SHOGUN",
        ),
    ),
    ShrineFeatureEntry(
        name_jp="出雲大社",
        address="島根県出雲市大社町杵築東195",
        feature_ids=(
            "C_NATIONAL_TREASURE",
            "C_ORIGINAL_BUILDINGS",
            "C_OLDEST",
            "C_SHIMENAWA",
            "S_TREE_AVENUE",
            "ST_MYTH",
            "ST_IMPERIAL",
            "F_FESTIVAL",
            "F_PERFORMANCE",
        ),
    ),
    ShrineFeatureEntry(
        name_jp="厳島神社",
        address="広島県廿日市市宮島町1-1",
        feature_ids=(
            "S_SEA",
            "ST_ANCIENT",
            "C_NATIONAL_TREASURE",
            "C_WORLD_HERITAGE",
            "C_TREASURE_HALL",
            "ST_SAMURAI",
            "ST_MYTH",
            "ST_IMPERIAL",
        ),
    ),
)
