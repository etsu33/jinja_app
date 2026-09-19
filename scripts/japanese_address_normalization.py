#!/usr/bin/env python
"""日本住所 Stage 2 structured normalization（deterministic / side-effect free）。

`docs/audit/position-audit-v2/japanese-address-structured-normalization-contract.md`
を authority として、日本住所の表記差を **安全に比較可能な構造** へ変換する。

## 責務の分離

```text
Stage 1          Lexical Normalization    文字表記のみを正規化
Stage 2          Structured Normalization 住所構造を解析・比較可能化
Identity Layer   同一神社かどうかを判定
```

本 module は Stage 1 と Stage 2 **だけ**を持つ。Identity 判定は行わない。

## 本 module が行わないこと（Contract §1 / §16）

* raw address の書き換え
* DB / Seed / Production の更新
* same shrine の確定（`SAME` / `DIFFERENT` / `NON_SHRINE` を返さない）
* fuzzy identity match
* 欠落住所の推測補完
* 座標による identity 救済
* network / filesystem アクセス

`evaluate` 相当の入口は純関数であり、同じ入力からは常に同じ出力を返す。

## Foundation only

本 module はまだどこからも呼ばれていない。Production identity / Position
Audit join / Shrine 永続化 / Recommendation / Compass / Ranking との結線は
本 PR の scope 外である（P2-B02 = foundation）。

既存の住所正規化（`backend/temples/geocoding/normalizer.py`,
`backend/temples/services/shrine_duplicate_normalize.py`,
`scripts/reconcile_production_shrine_identity.py`）の挙動は変更しない。
それらは別責務（表示整形 / 重複候補検索 / exact identity）であり、
本 module は置き換えない。

## fail-safe 原則

判断できないときは推測せず `AMBIGUOUS` / `UNSUPPORTED` を返す（Contract §16）。
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# normalization_status（Contract §3）
# ---------------------------------------------------------------------------
NORMALIZED = "NORMALIZED"
NO_CHANGE = "NO_CHANGE"
AMBIGUOUS = "AMBIGUOUS"
UNSUPPORTED = "UNSUPPORTED"

NORMALIZATION_STATUSES = frozenset({NORMALIZED, NO_CHANGE, AMBIGUOUS, UNSUPPORTED})

# ---------------------------------------------------------------------------
# normalization_rules_applied（Contract §4）
# ---------------------------------------------------------------------------
# 「適用していないルールを記録してはならない」。記録は適用順で行う。
RULE_CHOME_TO_BLOCK = "CHOME_TO_BLOCK"
RULE_BAN_TO_LOT = "BAN_TO_LOT"
RULE_BANCHI_TO_LOT = "BANCHI_TO_LOT"
RULE_GO_TO_SUB_LOT = "GO_TO_SUB_LOT"
RULE_STRUCTURED_NUMERIC_KANJI = "STRUCTURED_NUMERIC_KANJI"
RULE_BUILDING_COMPONENT_SPLIT = "BUILDING_COMPONENT_SPLIT"
RULE_FLOOR_COMPONENT_SPLIT = "FLOOR_COMPONENT_SPLIT"
RULE_UNIT_COMPONENT_SPLIT = "UNIT_COMPONENT_SPLIT"

NORMALIZATION_RULES = frozenset(
    {
        RULE_CHOME_TO_BLOCK,
        RULE_BAN_TO_LOT,
        RULE_BANCHI_TO_LOT,
        RULE_GO_TO_SUB_LOT,
        RULE_STRUCTURED_NUMERIC_KANJI,
        RULE_BUILDING_COMPONENT_SPLIT,
        RULE_FLOOR_COMPONENT_SPLIT,
        RULE_UNIT_COMPONENT_SPLIT,
    }
)

# ---------------------------------------------------------------------------
# review_reasons（Contract §5）
# ---------------------------------------------------------------------------
REASON_OAZA_STRUCTURE_AMBIGUOUS = "OAZA_STRUCTURE_AMBIGUOUS"
REASON_AZA_STRUCTURE_AMBIGUOUS = "AZA_STRUCTURE_AMBIGUOUS"
REASON_KOAZA_STRUCTURE_AMBIGUOUS = "KOAZA_STRUCTURE_AMBIGUOUS"
REASON_SPECIAL_ADDRESS_NOTATION = "SPECIAL_ADDRESS_NOTATION"
REASON_BUILDING_BOUNDARY_AMBIGUOUS = "BUILDING_BOUNDARY_AMBIGUOUS"
REASON_UNBANCHED_ADDRESS = "UNBANCHED_ADDRESS"
REASON_UNSUPPORTED_LOT_STRUCTURE = "UNSUPPORTED_LOT_STRUCTURE"
REASON_UNKNOWN_ADDRESS_PATTERN = "UNKNOWN_ADDRESS_PATTERN"

# 出力順を固定する canonical order。集合順に依存させない。
REVIEW_REASON_ORDER = (
    REASON_OAZA_STRUCTURE_AMBIGUOUS,
    REASON_AZA_STRUCTURE_AMBIGUOUS,
    REASON_KOAZA_STRUCTURE_AMBIGUOUS,
    REASON_SPECIAL_ADDRESS_NOTATION,
    REASON_BUILDING_BOUNDARY_AMBIGUOUS,
    REASON_UNBANCHED_ADDRESS,
    REASON_UNSUPPORTED_LOT_STRUCTURE,
    REASON_UNKNOWN_ADDRESS_PATTERN,
)
REVIEW_REASONS = frozenset(REVIEW_REASON_ORDER)
_REVIEW_REASON_RANK = {reason: index for index, reason in enumerate(REVIEW_REASON_ORDER)}

# ---------------------------------------------------------------------------
# address identity status（Contract §9.1）
# ---------------------------------------------------------------------------
# Stage 2 が Identity Layer へ渡す **evidence**。entity 判定ではない（§10）。
ADDRESS_EXACT_MATCH = "ADDRESS_EXACT_MATCH"
ADDRESS_NORMALIZED_MATCH = "ADDRESS_NORMALIZED_MATCH"
ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF = "ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF"
ADDRESS_DIFFERENT = "ADDRESS_DIFFERENT"
ADDRESS_AMBIGUOUS = "ADDRESS_AMBIGUOUS"
ADDRESS_UNSUPPORTED = "ADDRESS_UNSUPPORTED"

ADDRESS_IDENTITY_STATUSES = frozenset(
    {
        ADDRESS_EXACT_MATCH,
        ADDRESS_NORMALIZED_MATCH,
        ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF,
        ADDRESS_DIFFERENT,
        ADDRESS_AMBIGUOUS,
        ADDRESS_UNSUPPORTED,
    }
)


# ---------------------------------------------------------------------------
# Stage 1 — Lexical Normalization（Contract §2.2）
# ---------------------------------------------------------------------------
# `scripts/audit_shrine_positions_v2.py` の `normalize_address()` と
# **同一の規則**を実装する。両者が同値であることは
# `scripts/tests/test_japanese_address_normalization.py` が固定する。
#
# 依存方向を作らないため import ではなく再実装している。既存側の挙動は
# 変更しない（P2-B02 は foundation であり、統合は別 PR）。
#
# 既知の制約: dash 異体字集合に `ー`（U+30FC）を含む。住所表記で dash の
# 代用に使われるための既存契約だが、カタカナ長音を含む建物名は
# `パークタワー` -> `パークタワ-` のように変形する。既存 audit 契約との
# 同値性を優先し、本 PR では変更しない。
_WHITESPACE_RE = re.compile(r"\s+")
_POSTAL_PREFIX_RE = re.compile(r"^〒?\s*\d{3}\s*-?\s*\d{4}\s*")
_DASH_VARIANTS = "－‐‑‒–—―ー−"
_DASH_TABLE = {ord(ch): "-" for ch in _DASH_VARIANTS}
_JAPAN_PREFIX = "日本、"


def lexical_normalize(value: str | None) -> str:
    """Stage 1。**文字表記のみ**を正規化する（Contract §2.2）。

    行うのは NFKC / `日本、` prefix / 郵便番号 prefix / dash 異体字 /
    前後空白 / 連続空白だけである。

    丁目・番・番地・号 の意味的な書き換えは Stage 1 では **行わない**。
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.strip()
    if text.startswith(_JAPAN_PREFIX):
        text = text[len(_JAPAN_PREFIX) :]
    text = _POSTAL_PREFIX_RE.sub("", text)
    text = text.translate(_DASH_TABLE)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Stage 2 — parsing helpers
# ---------------------------------------------------------------------------

# 安全に解析できない特殊表記（Contract §5 / GC-A11）。
# 数値構造を発明せず UNSUPPORTED にする。
_SPECIAL_NOTATIONS: tuple[tuple[str, str], ...] = (
    ("無番地", REASON_UNBANCHED_ADDRESS),
    ("番外地", REASON_SPECIAL_ADDRESS_NOTATION),
)

_PREFECTURE_RE = re.compile(r"^(東京都|北海道|京都府|大阪府|\S{2,3}県)")
_MUNICIPALITY_RE = re.compile(r"^(\S+?[市区町村])")
# 政令指定都市の行政区（`横浜市中区`）。`市` の直後に来る `区` だけを足す。
_WARD_SUFFIX_RE = re.compile(r"^(\S+?区)")

_KANJI_DIGITS = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

# 漢数字を住所数値として認識するのは **`丁目` の直前だけ**（Contract §6）。
#
# `番` / `番地` / `号` の直前は意図的に対象外にしている。`麻布十番` のような
# 実在の町名を `十番` = lot 10 と誤読しうるためである。Contract が明示的に
# 許可している例は `二丁目 -> block=2` だけであり、そこへ fail-safe に絞る。
# 認識できなかった場合は誤変換せず、後段で AMBIGUOUS / UNSUPPORTED になる。
_KANJI_CHOME_RE = re.compile(r"[一二三四五六七八九十百]+(?=丁目)")

_CHOME_RE = re.compile(r"^(?P<value>\d+|[一二三四五六七八九十百]+)丁目")
_BAN_RE = re.compile(r"^\s*(?P<value>\d+)(?P<unit>番地|番)")
_GO_RE = re.compile(r"^\s*(?P<value>\d+)号(?!室)")
_HYPHEN_NUMBERS_RE = re.compile(r"^\s*-?\s*(?P<value>\d+(?:\s*-\s*\d+)*)")

_UNIT_SUFFIX_RE = re.compile(r"(?P<unit>\d+号室)$")
_FLOOR_SUFFIX_RE = re.compile(r"(?P<floor>地下\d+階|B\d+[Ff]?|\d+階|\d+[Ff])$")
_DIGIT_RE = re.compile(r"\d")

_OAZA_MARKER = "大字"
_KOAZA_MARKER = "小字"
_AZA_MARKER = "字"


def _kanji_to_int(token: str) -> int | None:
    """住所数値 token に限定した漢数字 -> int（1..999）。

    解釈できない形は `None` を返す（発明しない）。
    """
    if not token:
        return None
    if token.isdigit():
        return int(token)

    total = 0
    current = 0
    seen_any = False
    for char in token:
        if char in _KANJI_DIGITS:
            current = _KANJI_DIGITS[char]
            seen_any = True
        elif char == "十":
            total += (current or 1) * 10
            current = 0
            seen_any = True
        elif char == "百":
            total += (current or 1) * 100
            current = 0
            seen_any = True
        else:
            return None
    if not seen_any:
        return None
    return total + current


def _find_address_number_start(text: str) -> int | None:
    """住所数値 token の開始位置を返す。見つからなければ `None`。

    数値 token とみなすのは次だけである。

    * ASCII 数字（Stage 1 の NFKC で全角数字は ASCII になっている）
    * `丁目` が直後に続く漢数字列

    `二本松` / `三島` / `八幡` のような町名の漢数字はここで弾かれる。
    """
    for index, char in enumerate(text):
        if char.isdigit():
            return index
        if _KANJI_CHOME_RE.match(text, index):
            return index
    return None


@dataclass(frozen=True)
class _AreaComponents:
    locality: str | None
    oaza: str | None
    aza: str | None
    koaza: str | None


def _split_area(area: str) -> _AreaComponents:
    """町字部から `大字` / `字` / `小字` を component として取り出す。

    marker は **削除しない**（Contract §7）。locality と別 field に分けるだけで、
    `address_core` には marker 付きの表記がそのまま残る。
    """
    text = area.strip()
    if not text:
        return _AreaComponents(None, None, None, None)

    markers: list[tuple[str, int, int]] = []
    index = 0
    while index < len(text):
        if text.startswith(_OAZA_MARKER, index):
            markers.append(("oaza", index, len(_OAZA_MARKER)))
            index += len(_OAZA_MARKER)
        elif text.startswith(_KOAZA_MARKER, index):
            markers.append(("koaza", index, len(_KOAZA_MARKER)))
            index += len(_KOAZA_MARKER)
        elif text[index] == _AZA_MARKER:
            markers.append(("aza", index, len(_AZA_MARKER)))
            index += len(_AZA_MARKER)
        else:
            index += 1

    if not markers:
        return _AreaComponents(text or None, None, None, None)

    locality = text[: markers[0][1]].strip() or None
    values: dict[str, str | None] = {"oaza": None, "aza": None, "koaza": None}
    for position, (kind, start, length) in enumerate(markers):
        value_start = start + length
        value_end = markers[position + 1][1] if position + 1 < len(markers) else len(text)
        value = text[value_start:value_end].strip()
        values[kind] = value or None
    return _AreaComponents(locality, values["oaza"], values["aza"], values["koaza"])


@dataclass(frozen=True)
class _NumberComponents:
    block: int | None
    lot: int | None
    sub_lot: int | None
    rules: tuple[str, ...]
    rest: str
    review_reason: str | None


def _parse_numbers(tail: str) -> _NumberComponents:
    """住所数値部を `block` / `lot` / `sub_lot` へ解析する（Contract §6）。

    marker 付き token（`丁目` / `番` / `番地` / `号`）を先に消費し、残った
    hyphen 区切りの数値を空いている slot へ順に詰める。

    marker が1つも無い裸の数値列は位置で決める。

    ```text
    3個 -> block, lot, sub_lot
    2個 -> block, lot
    1個 -> lot        （番地単独とみなす）
    ```

    slot 数を超える数値列は発明せず `UNSUPPORTED_LOT_STRUCTURE` にする。
    """
    rules: list[str] = []
    block: int | None = None
    lot: int | None = None
    sub_lot: int | None = None
    marked = False

    rest = tail
    match = _CHOME_RE.match(rest)
    if match:
        token = match.group("value")
        value = _kanji_to_int(token)
        if value is None:
            return _NumberComponents(
                None, None, None, (), tail, REASON_UNSUPPORTED_LOT_STRUCTURE
            )
        block = value
        rules.append(RULE_CHOME_TO_BLOCK)
        if not token.isdigit():
            rules.append(RULE_STRUCTURED_NUMERIC_KANJI)
        marked = True
        rest = rest[match.end() :]

    match = _BAN_RE.match(rest)
    if match:
        lot = int(match.group("value"))
        rules.append(
            RULE_BANCHI_TO_LOT if match.group("unit") == "番地" else RULE_BAN_TO_LOT
        )
        marked = True
        rest = rest[match.end() :]

    match = _GO_RE.match(rest)
    if match:
        sub_lot = int(match.group("value"))
        rules.append(RULE_GO_TO_SUB_LOT)
        marked = True
        rest = rest[match.end() :]

    match = _HYPHEN_NUMBERS_RE.match(rest)
    if match:
        numbers = [int(part) for part in re.split(r"\s*-\s*", match.group("value"))]
        rest = rest[match.end() :]

        assigned: dict[str, int | None] = {
            "block": block,
            "lot": lot,
            "sub_lot": sub_lot,
        }
        if not marked and len(numbers) == 1:
            slots = ["lot"]
        else:
            slots = [name for name in ("block", "lot", "sub_lot") if assigned[name] is None]
        if len(numbers) > len(slots):
            return _NumberComponents(
                None, None, None, (), tail, REASON_UNSUPPORTED_LOT_STRUCTURE
            )
        for name, number in zip(slots, numbers):
            assigned[name] = number
        block, lot, sub_lot = assigned["block"], assigned["lot"], assigned["sub_lot"]

    if block is None and lot is None and sub_lot is None:
        return _NumberComponents(None, None, None, (), tail, REASON_UNKNOWN_ADDRESS_PATTERN)

    # 途切れた slot（`1丁目3号` のように block と sub_lot はあるが lot が
    # 無い形）は `-` 連結で誤った core を作るため解析しない。
    if block is not None and lot is None and sub_lot is not None:
        return _NumberComponents(
            None, None, None, (), tail, REASON_UNSUPPORTED_LOT_STRUCTURE
        )

    return _NumberComponents(block, lot, sub_lot, tuple(rules), rest, None)


@dataclass(frozen=True)
class _BuildingComponents:
    building: str | None
    floor: str | None
    unit: str | None
    rules: tuple[str, ...]
    review_reason: str | None


def _parse_building(rest: str) -> _BuildingComponents:
    """建物 / 階 / 部屋番号を分離する（Contract §2.6 / §8）。

    後方から `号室` -> 階 の順に取り、残りを建物名とする。
    残りに数字が混じる場合は住所本体との境界を確定できないため、
    推測せず `BUILDING_BOUNDARY_AMBIGUOUS` にする。
    """
    text = rest.strip()
    if not text:
        return _BuildingComponents(None, None, None, (), None)

    rules: list[str] = []
    unit: str | None = None
    floor: str | None = None

    match = _UNIT_SUFFIX_RE.search(text)
    if match:
        unit = match.group("unit")
        text = text[: match.start()].strip()
        rules.append(RULE_UNIT_COMPONENT_SPLIT)

    match = _FLOOR_SUFFIX_RE.search(text)
    if match:
        floor = match.group("floor")
        text = text[: match.start()].strip()
        rules.append(RULE_FLOOR_COMPONENT_SPLIT)

    building = text.strip() or None
    if building is not None:
        if _DIGIT_RE.search(building):
            # 住所の続きなのか建物名なのか決められない。
            return _BuildingComponents(
                None, None, None, (), REASON_BUILDING_BOUNDARY_AMBIGUOUS
            )
        rules.append(RULE_BUILDING_COMPONENT_SPLIT)

    # rules は「建物 -> 階 -> 部屋」の安定順で出す。
    ordered = [
        rule
        for rule in (
            RULE_BUILDING_COMPONENT_SPLIT,
            RULE_FLOOR_COMPONENT_SPLIT,
            RULE_UNIT_COMPONENT_SPLIT,
        )
        if rule in rules
    ]
    return _BuildingComponents(building, floor, unit, tuple(ordered), None)


# ---------------------------------------------------------------------------
# Structured Output Schema（Contract §2）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AddressNormalizationResult:
    """Stage 2 の構造化結果。

    `address_core` / `structured_address` は **comparison-only derived value**
    であり保存値ではない（Contract §2.5）。
    """

    raw_address: str
    lexical_address: str

    prefecture: str | None = None
    municipality: str | None = None
    locality: str | None = None
    oaza: str | None = None
    aza: str | None = None
    koaza: str | None = None

    block: int | None = None
    lot: int | None = None
    sub_lot: int | None = None

    address_core: str | None = None

    building_component: str | None = None
    floor_component: str | None = None
    unit_component: str | None = None

    structured_address: str | None = None

    normalization_status: str = UNSUPPORTED
    normalization_rules_applied: tuple[str, ...] = ()
    review_reasons: tuple[str, ...] = ()

    # marker を取り除いた比較用の射影。`大字` / `字` / `小字` の有無だけが
    # 違う住所を検出するために使う。住所そのものを書き換えた値ではない。
    core_without_area_markers: str | None = field(default=None, repr=False)

    @property
    def area_markers(self) -> tuple[str, ...]:
        """存在する町字 marker（比較順を固定するため tuple）。"""
        return tuple(
            name
            for name, value in (
                ("oaza", self.oaza),
                ("aza", self.aza),
                ("koaza", self.koaza),
            )
            if value is not None
        )

    @property
    def has_building_components(self) -> bool:
        return any(
            value is not None
            for value in (
                self.building_component,
                self.floor_component,
                self.unit_component,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """決定的な serialize（key 順は定義順で固定）。"""
        return {
            "raw_address": self.raw_address,
            "lexical_address": self.lexical_address,
            "prefecture": self.prefecture,
            "municipality": self.municipality,
            "locality": self.locality,
            "oaza": self.oaza,
            "aza": self.aza,
            "koaza": self.koaza,
            "block": self.block,
            "lot": self.lot,
            "sub_lot": self.sub_lot,
            "address_core": self.address_core,
            "building_component": self.building_component,
            "floor_component": self.floor_component,
            "unit_component": self.unit_component,
            "structured_address": self.structured_address,
            "normalization_status": self.normalization_status,
            "normalization_rules_applied": list(self.normalization_rules_applied),
            "review_reasons": list(self.review_reasons),
        }


@dataclass(frozen=True)
class AddressComparisonResult:
    """2住所の比較結果。

    これは **evidence** であり entity 判定ではない。`SAME` / `DIFFERENT` /
    `NON_SHRINE` は返さない（Contract §10 / §11）。
    """

    address_identity_status: str
    left: AddressNormalizationResult
    right: AddressNormalizationResult
    review_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "address_identity_status": self.address_identity_status,
            "review_reasons": list(self.review_reasons),
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }


def _order_reasons(reasons: list[str]) -> tuple[str, ...]:
    """review_reasons を canonical order で一意化する（決定性）。"""
    unique = {reason for reason in reasons if reason}
    return tuple(sorted(unique, key=lambda reason: _REVIEW_REASON_RANK[reason]))


def _unsupported(
    raw: str, lexical: str, reasons: list[str], **fields: Any
) -> AddressNormalizationResult:
    return AddressNormalizationResult(
        raw_address=raw,
        lexical_address=lexical,
        normalization_status=UNSUPPORTED,
        review_reasons=_order_reasons(reasons),
        **fields,
    )


def normalize_address_structured(raw_address: str | None) -> AddressNormalizationResult:
    """住所を Stage 1 + Stage 2 で構造化する（純関数）。

    同じ入力からは常に同じ構造・同じ status・同じ rules 順・同じ
    review_reasons 順を返す。network / DB / filesystem に触れない。
    """
    raw = "" if raw_address is None else str(raw_address)
    lexical = lexical_normalize(raw)

    if not lexical:
        return _unsupported(raw, lexical, [REASON_UNKNOWN_ADDRESS_PATTERN])

    # --- 特殊表記（Contract §5 / GC-A11）------------------------------------
    # 数値構造を発明しない。
    for notation, reason in _SPECIAL_NOTATIONS:
        if notation in lexical:
            return _unsupported(raw, lexical, [reason])

    # --- 都道府県 ----------------------------------------------------------
    match = _PREFECTURE_RE.match(lexical)
    if not match:
        return _unsupported(raw, lexical, [REASON_UNKNOWN_ADDRESS_PATTERN])
    prefecture = match.group(1)
    # 行政区画の区切りに入る空白は identity の意味を持たないため読み飛ばす
    # （`東京都 千代田区...`）。Stage 1 は連続空白を1つに畳むだけで削除しない。
    rest = lexical[match.end() :].lstrip()

    # --- 市区町村 ----------------------------------------------------------
    match = _MUNICIPALITY_RE.match(rest)
    if not match:
        return _unsupported(
            raw,
            lexical,
            [REASON_UNKNOWN_ADDRESS_PATTERN],
            prefecture=prefecture,
        )
    municipality = match.group(1)
    rest = rest[match.end() :].lstrip()

    # 政令指定都市の行政区は市名と一体で1つの municipality とする。
    if municipality.endswith("市"):
        ward = _WARD_SUFFIX_RE.match(rest)
        if ward:
            number_start = _find_address_number_start(rest)
            if number_start is None or ward.end() <= number_start:
                municipality += ward.group(1)
                rest = rest[ward.end() :]

    # --- 住所数値の開始位置 --------------------------------------------------
    number_start = _find_address_number_start(rest)
    if number_start is None:
        return _unsupported(
            raw,
            lexical,
            [REASON_UNKNOWN_ADDRESS_PATTERN],
            prefecture=prefecture,
            municipality=municipality,
        )

    area = _split_area(rest[:number_start])
    numbers = _parse_numbers(rest[number_start:])

    base_fields: dict[str, Any] = {
        "prefecture": prefecture,
        "municipality": municipality,
        "locality": area.locality,
        "oaza": area.oaza,
        "aza": area.aza,
        "koaza": area.koaza,
    }

    if numbers.review_reason is not None:
        return _unsupported(raw, lexical, [numbers.review_reason], **base_fields)

    building = _parse_building(numbers.rest)
    if building.review_reason is not None:
        return AddressNormalizationResult(
            raw_address=raw,
            lexical_address=lexical,
            normalization_status=AMBIGUOUS,
            review_reasons=_order_reasons([building.review_reason]),
            block=numbers.block,
            lot=numbers.lot,
            sub_lot=numbers.sub_lot,
            **base_fields,
        )

    # --- derived comparison values -----------------------------------------
    numeric = "-".join(
        str(value) for value in (numbers.block, numbers.lot, numbers.sub_lot)
        if value is not None
    )
    # marker を保持したままの町字表記（Contract §7: 自動削除禁止）。
    area_with_markers = "".join(
        part
        for part in (
            area.locality or "",
            f"{_OAZA_MARKER}{area.oaza}" if area.oaza else "",
            f"{_AZA_MARKER}{area.aza}" if area.aza else "",
            f"{_KOAZA_MARKER}{area.koaza}" if area.koaza else "",
        )
        if part
    )
    area_without_markers = "".join(
        part
        for part in (
            area.locality or "",
            area.oaza or "",
            area.aza or "",
            area.koaza or "",
        )
        if part
    )

    address_core = f"{prefecture}{municipality}{area_with_markers}{numeric}"
    core_without_markers = f"{prefecture}{municipality}{area_without_markers}{numeric}"

    building_tail = " ".join(
        part
        for part in (
            building.building or "",
            building.floor or "",
            building.unit or "",
        )
        if part
    )
    structured_address = (
        f"{address_core} {building_tail}" if building_tail else address_core
    )

    rules = numbers.rules + building.rules
    status = NORMALIZED if rules else NO_CHANGE

    return AddressNormalizationResult(
        raw_address=raw,
        lexical_address=lexical,
        block=numbers.block,
        lot=numbers.lot,
        sub_lot=numbers.sub_lot,
        address_core=address_core,
        building_component=building.building,
        floor_component=building.floor,
        unit_component=building.unit,
        structured_address=structured_address,
        normalization_status=status,
        normalization_rules_applied=rules,
        review_reasons=(),
        core_without_area_markers=core_without_markers,
        **base_fields,
    )


def compare_addresses(
    left_address: str | None, right_address: str | None
) -> AddressComparisonResult:
    """2住所を比較し address identity evidence を返す（Contract §9）。

    返すのは住所レベルの evidence だけである。entity の同一性（`SAME` /
    `DIFFERENT` / `NON_SHRINE`）は Identity Layer の責務であり、
    `ADDRESS_NORMALIZED_MATCH` から自動的に `SAME` を導いてはならない（§11）。

    判定順:

    ```text
    1. raw 完全一致            -> ADDRESS_EXACT_MATCH
    2. どちらかが UNSUPPORTED  -> ADDRESS_UNSUPPORTED
    3. どちらかが AMBIGUOUS    -> ADDRESS_AMBIGUOUS
    4. lexical 一致            -> ADDRESS_NORMALIZED_MATCH
    5. 町字 marker の非対称     -> ADDRESS_AMBIGUOUS / ADDRESS_DIFFERENT
    6. address_core 一致        -> 建物差の有無で分岐
    7. それ以外                -> ADDRESS_DIFFERENT
    ```

    5 を 6 より先に置くのが重要である。`大字` の有無だけが違う住所を
    `ADDRESS_NORMALIZED_MATCH` にも `ADDRESS_DIFFERENT` にも倒さず、
    `ADDRESS_AMBIGUOUS` として Identity Layer へ送る（Contract §7）。
    """
    left = normalize_address_structured(left_address)
    right = normalize_address_structured(right_address)

    # 1. raw 完全一致は最も強い住所 evidence（Contract §9.2）。
    if left.raw_address == right.raw_address and left.raw_address != "":
        return AddressComparisonResult(ADDRESS_EXACT_MATCH, left, right)

    # 2 / 3. 片側でも解析できていなければ推測しない。
    if UNSUPPORTED in (left.normalization_status, right.normalization_status):
        return AddressComparisonResult(
            ADDRESS_UNSUPPORTED,
            left,
            right,
            _order_reasons(list(left.review_reasons) + list(right.review_reasons)),
        )
    if AMBIGUOUS in (left.normalization_status, right.normalization_status):
        return AddressComparisonResult(
            ADDRESS_AMBIGUOUS,
            left,
            right,
            _order_reasons(list(left.review_reasons) + list(right.review_reasons)),
        )

    # 4. Stage 1 だけで一致した（Contract GC-A02）。
    if left.lexical_address == right.lexical_address:
        return AddressComparisonResult(ADDRESS_NORMALIZED_MATCH, left, right)

    # 5. `大字` / `字` / `小字` の有無が非対称（Contract §7 / GC-A06..A08）。
    if left.area_markers != right.area_markers:
        if left.core_without_area_markers == right.core_without_area_markers:
            reasons = []
            for marker, reason in (
                ("oaza", REASON_OAZA_STRUCTURE_AMBIGUOUS),
                ("aza", REASON_AZA_STRUCTURE_AMBIGUOUS),
                ("koaza", REASON_KOAZA_STRUCTURE_AMBIGUOUS),
            ):
                if (marker in left.area_markers) != (marker in right.area_markers):
                    reasons.append(reason)
            return AddressComparisonResult(
                ADDRESS_AMBIGUOUS, left, right, _order_reasons(reasons)
            )
        return AddressComparisonResult(ADDRESS_DIFFERENT, left, right)

    # 6. 住所本体の一致。
    if left.address_core is not None and left.address_core == right.address_core:
        same_building = (
            left.building_component == right.building_component
            and left.floor_component == right.floor_component
            and left.unit_component == right.unit_component
        )
        if same_building:
            return AddressComparisonResult(ADDRESS_NORMALIZED_MATCH, left, right)
        # 建物差は捨てない。SAME にもしない（Contract §8 / §9.4）。
        return AddressComparisonResult(
            ADDRESS_CORE_MATCH_WITH_COMPONENT_DIFF, left, right
        )

    # 7.
    return AddressComparisonResult(ADDRESS_DIFFERENT, left, right)
