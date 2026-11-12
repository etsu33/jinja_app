"""英語の相談文から、英語版の特徴語（Sight / Craft / Story / Feel）を辞書で取り出す。

語彙と辞書の正本は Google スプレッドシート
「KAMI MUSUBI 英語版の特徴語と10社の当てはめ表」の「語彙」タブ（2026-11-12 作成）。
変えるときはスプレッドシートを先に直し、この定数に手で反映する。

この段は「取り出して記録する」だけで、並び順には使わない。
神社側の特徴語データが入るまで（作業の順番3）、点数には反映しない。
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

FEATURE_WORDS_VERSION = "2026-11-12"

CATEGORIES: Tuple[str, ...] = ("Sight", "Craft", "Story", "Feel")


@dataclass(frozen=True)
class FeatureWord:
    id: str
    category: str
    label_en: str
    meaning_ja: str
    synonyms: Tuple[str, ...]


FEATURE_WORDS: Tuple[FeatureWord, ...] = (
    FeatureWord(
        "S_MOUNTAIN",
        "Sight",
        "mountaintop",
        "山の上・山頂にある",
        ("mountain", "mountains", "mountaintop", "summit", "peak"),
    ),
    FeatureWord(
        "S_VIEW",
        "Sight",
        "panoramic view",
        "境内から街や平野を一望できる",
        ("view", "views", "panorama", "panoramic", "overlook", "scenic view", "city view"),
    ),
    FeatureWord(
        "S_SEA",
        "Sight",
        "by the sea",
        "海・潮の満ち引きの場所に建つ",
        ("sea", "ocean", "tide", "tides", "seaside", "waterfront", "coast", "island"),
    ),
    FeatureWord(
        "S_FOREST",
        "Sight",
        "sacred forest",
        "鎮守の杜・緑に囲まれた境内",
        ("forest", "woods", "grove", "greenery", "nature", "green", "trees"),
    ),
    FeatureWord(
        "S_POND", "Sight", "pond", "境内に池がある", ("pond", "ponds", "lotus pond", "water garden")
    ),
    FeatureWord(
        "S_GIANT_TREE",
        "Sight",
        "ancient tree",
        "樹齢の長い巨木・由緒ある木",
        ("old tree", "ancient tree", "big tree", "giant tree", "sacred tree", "ginkgo"),
    ),
    FeatureWord(
        "S_TREE_AVENUE",
        "Sight",
        "tree-lined approach",
        "並木・並木の参道",
        ("tree-lined", "avenue of trees", "cedar", "cedars", "pine", "pines"),
    ),
    FeatureWord(
        "S_FLOWERS",
        "Sight",
        "seasonal flowers",
        "花の名所・季節の花",
        (
            "flowers",
            "flower",
            "blossoms",
            "azalea",
            "azaleas",
            "plum",
            "plum blossoms",
            "cherry blossoms",
            "sakura",
            "peony",
            "peonies",
            "lotus",
        ),
    ),
    FeatureWord(
        "S_AUTUMN",
        "Sight",
        "autumn colors",
        "紅葉・黄葉",
        ("autumn", "fall", "autumn leaves", "fall colors", "foliage", "yellow leaves"),
    ),
    FeatureWord(
        "S_STEPS",
        "Sight",
        "long stairs",
        "大きな石段・長い階段",
        ("stairs", "steps", "stone steps", "staircase"),
    ),
    FeatureWord(
        "C_NATIONAL_TREASURE",
        "Craft",
        "national treasure",
        "国宝の建造物がある",
        ("national treasure", "national treasures"),
    ),
    FeatureWord(
        "C_WORLD_HERITAGE",
        "Craft",
        "world heritage",
        "世界遺産",
        ("world heritage", "unesco", "heritage site"),
    ),
    FeatureWord(
        "C_HERITAGE",
        "Craft",
        "designated cultural property",
        "国・都道府県の文化財指定・登録の建物",
        (
            "cultural property",
            "cultural asset",
            "historic building",
            "historic buildings",
            "heritage building",
        ),
    ),
    FeatureWord(
        "C_ORIGINAL_BUILDINGS",
        "Craft",
        "centuries-old buildings",
        "江戸時代以前の社殿が今も残る",
        (
            "original",
            "centuries old",
            "edo period building",
            "old buildings",
            "historic architecture",
            "wooden architecture",
        ),
    ),
    FeatureWord(
        "C_CARVINGS",
        "Craft",
        "elaborate carvings",
        "彫刻が見どころ",
        ("carving", "carvings", "carved", "sculpture", "sculptures", "ornate", "detailed"),
    ),
    FeatureWord(
        "C_VERMILION",
        "Craft",
        "vermilion lacquer",
        "朱塗りの社殿",
        ("red", "vermilion", "vermillion", "colorful", "colourful", "lacquer", "lacquered"),
    ),
    FeatureWord(
        "C_SHIMENAWA",
        "Craft",
        "giant sacred rope",
        "大注連縄",
        ("rope", "ropes", "shimenawa", "straw rope", "giant rope"),
    ),
    FeatureWord(
        "C_OLDEST",
        "Craft",
        "oldest of its kind",
        "最古と公式に書かれたもの",
        ("oldest", "earliest", "most ancient"),
    ),
    FeatureWord(
        "C_TREASURE_HALL",
        "Craft",
        "treasure museum",
        "宝物殿・展示施設",
        (
            "museum",
            "treasure",
            "treasures",
            "artifacts",
            "artefacts",
            "swords",
            "exhibition",
            "exhibit",
        ),
    ),
    FeatureWord(
        "ST_SHOGUN",
        "Story",
        "Tokugawa shoguns",
        "徳川将軍家とのゆかり",
        ("shogun", "shoguns", "tokugawa", "ieyasu", "edo", "edo period"),
    ),
    FeatureWord(
        "ST_SAMURAI",
        "Story",
        "samurai history",
        "武将・武家とのゆかり",
        (
            "samurai",
            "warrior",
            "warriors",
            "warlord",
            "warlords",
            "minamoto",
            "yoritomo",
            "kamakura shogunate",
        ),
    ),
    FeatureWord(
        "ST_MYTH",
        "Story",
        "myths and legends",
        "神話・伝説",
        ("myth", "myths", "mythology", "legend", "legends", "folklore", "gods", "kojiki"),
    ),
    FeatureWord(
        "ST_ANIMAL",
        "Story",
        "sacred animal",
        "神格化された動物・神使",
        ("wolf", "wolves", "sacred animal", "animal spirit", "guardian animal"),
    ),
    FeatureWord(
        "ST_SCHOLAR",
        "Story",
        "god of learning",
        "学問の神",
        (
            "study",
            "studies",
            "exam",
            "exams",
            "test",
            "tests",
            "scholar",
            "learning",
            "student",
            "students",
            "school",
        ),
    ),
    FeatureWord(
        "ST_ANCIENT",
        "Story",
        "over 1,000 years old",
        "創建（伝承を含む）が西暦1000年より前",
        (
            "ancient",
            "old shrine",
            "very old",
            "oldest shrine",
            "thousand years",
            "1000 years",
            "long history",
        ),
    ),
    FeatureWord(
        "ST_IMPERIAL",
        "Story",
        "imperial connection",
        "皇室とのゆかり",
        ("imperial", "emperor", "emperors", "imperial palace", "imperial family", "royal"),
    ),
    FeatureWord(
        "ST_SPIRIT_LEGEND",
        "Story",
        "legend of a powerful spirit",
        "御霊・祟りの伝承",
        ("ghost", "ghosts", "spirit", "spirits", "curse", "cursed", "haunted", "vengeful"),
    ),
    FeatureWord(
        "ST_POP_CULTURE",
        "Story",
        "pop culture and literature",
        "アニメ・文学・映画の舞台やコラボ",
        ("anime", "manga", "pop culture", "novel", "literature", "film", "movie"),
    ),
    FeatureWord(
        "ST_SYNCRETISM",
        "Story",
        "Shinto-Buddhist blend",
        "神仏習合の名残",
        ("buddhist", "buddhism", "temple", "syncretism", "shinto and buddhist"),
    ),
    FeatureWord(
        "ST_MOUNTAIN_WORSHIP",
        "Story",
        "sacred mountain worship",
        "山岳信仰・修験",
        ("sacred mountain", "mountain worship", "pilgrimage", "ascetic", "ascetics", "yamabushi"),
    ),
    FeatureWord(
        "F_QUIET",
        "Feel",
        "quiet",
        "静か・静寂",
        ("quiet", "peaceful", "calm", "tranquil", "serene", "silence", "silent"),
    ),
    FeatureWord(
        "F_URBAN_OASIS",
        "Feel",
        "green oasis in the city",
        "都心にありながら緑豊か",
        (
            "in the city",
            "city center",
            "city centre",
            "downtown",
            "urban",
            "oasis",
            "central tokyo",
            "escape the city",
        ),
    ),
    FeatureWord(
        "F_FESTIVAL",
        "Feel",
        "festival",
        "大きな祭り・行事",
        (
            "festival",
            "festivals",
            "matsuri",
            "parade",
            "procession",
            "portable shrine",
            "mikoshi",
            "event",
        ),
    ),
    FeatureWord(
        "F_HIKE",
        "Feel",
        "hike to reach",
        "歩いて登る",
        ("hike", "hiking", "trek", "trekking", "climb", "climbing", "trail"),
    ),
    FeatureWord(
        "F_DOG",
        "Feel",
        "dog friendly",
        "愛犬と参拝できる",
        ("dog", "dogs", "pet", "pets", "dog friendly"),
    ),
    FeatureWord(
        "F_CEREMONY",
        "Feel",
        "join a formal prayer",
        "社殿に上がる祈祷を受けられる",
        ("ceremony", "ritual", "rituals", "prayer", "blessing", "purification", "experience"),
    ),
    FeatureWord(
        "F_PERFORMANCE",
        "Feel",
        "traditional performance",
        "雅楽・神楽・能の奉納",
        ("gagaku", "kagura", "noh", "traditional music", "traditional dance", "performance"),
    ),
    FeatureWord(
        "F_CAFE",
        "Feel",
        "cafe on site",
        "境内で食事・お茶ができる",
        ("cafe", "café", "tea", "lunch", "food", "restaurant", "eat"),
    ),
    FeatureWord(
        "F_PHOTO",
        "Feel",
        "photo spot",
        "撮影スポット",
        ("photo", "photos", "photogenic", "picture", "pictures", "instagram", "photo spot"),
    ),
    FeatureWord(
        "F_GOSHUIN",
        "Feel",
        "goshuin stamps",
        "御朱印",
        ("goshuin", "stamp", "stamps", "seal", "shrine stamp", "stamp book"),
    ),
    FeatureWord(
        "F_CHARM",
        "Feel",
        "unique amulets",
        "特色あるお守り",
        ("amulet", "amulets", "charm", "charms", "omamori", "talisman", "souvenir"),
    ),
)


@dataclass(frozen=True)
class FeatureWordResult:
    ids: List[str] = field(default_factory=list)
    hits: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def matched(self) -> bool:
        return bool(self.ids)

    def as_payload(self) -> dict:
        return {
            "version": FEATURE_WORDS_VERSION,
            "ids": list(self.ids),
            "hits": {k: list(v) for k, v in self.hits.items()},
            "matched": self.matched,
        }


_NON_WORD = re.compile(r"[^a-z0-9]+")


def _normalize(text: str) -> str:
    """小文字にし、アクセントを外し、英数字以外を空白1つにまとめる。前後に空白を付ける。"""
    folded = unicodedata.normalize("NFKD", text or "")
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch)).lower()
    return " " + _NON_WORD.sub(" ", folded).strip() + " "


def _build_index() -> List[Tuple[str, str]]:
    """(特徴語ID, 前後に空白を付けた辞書の言葉) を、言葉の長い順に並べる。

    長い言葉から照合し、当たった部分は消してから短い言葉を照合する。
    「national treasure」が当たったとき、中の「treasure」（宝物殿）を重ねて拾わないため。
    """
    pairs: List[Tuple[str, str]] = []
    for word in FEATURE_WORDS:
        for syn in word.synonyms:
            norm = _normalize(syn).strip()
            if norm:
                pairs.append((word.id, " " + norm + " "))
    pairs.sort(key=lambda pair: len(pair[1]), reverse=True)
    return pairs


_INDEX = _build_index()


def extract_feature_words(text: str | None) -> FeatureWordResult:
    """英語の相談文から特徴語IDを取り出す。単語の区切りで照合する（red が tired に当たらない）。

    長い言葉を先に照合し、当たった部分は以降の照合から外す。
    ids は語彙の並び順。hits は ID ごとに当たった辞書の言葉。
    """
    remaining = _normalize(text or "")
    if not remaining.strip():
        return FeatureWordResult()
    hits: Dict[str, List[str]] = {}
    for word_id, phrase in _INDEX:
        if phrase in remaining:
            hits.setdefault(word_id, []).append(phrase.strip())
            # 当たった部分を区切り記号に置き換える。前後の空白は残し、隣の単語の照合を壊さない。
            remaining = remaining.replace(phrase, " | ")
    ids = [w.id for w in FEATURE_WORDS if w.id in hits]
    return FeatureWordResult(ids=ids, hits={k: hits[k] for k in ids})


def is_english_request(language: str | None) -> bool:
    """リクエストの language が英語のときだけ True。未指定は日本語として扱う。"""
    value = (language or "").strip().lower()
    return value == "en" or value.startswith("en-")
