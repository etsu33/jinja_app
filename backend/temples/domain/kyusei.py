# backend/temples/domain/kyusei.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Literal, Dict, Any
from django.utils import timezone


# ---- Public types ---------------------------------------------------------

StarNum = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9]


@dataclass(frozen=True)
class KyuseiResult:
    # 例: 7, "七赤金星"
    num: StarNum
    name: str
    # 九星の「年」として扱った年（節分境界を反映した年）
    ki_year: int
    # ざっくりの流れ（UI/理由文向け）
    flow_label_ja: str
    theme_ja: str


# ---- Constants ------------------------------------------------------------

# NOTE: 境界は本来「立春」（毎年微妙にズレる）。最小実装として 2/4 を固定。
# 精度を上げたくなったら、ここだけ差し替えればよい。
DEFAULT_SETSUBUN_MONTH = 2
DEFAULT_SETSUBUN_DAY = 4

STAR_NAMES: Dict[int, str] = {
    1: "一白水星",
    2: "二黒土星",
    3: "三碧木星",
    4: "四緑木星",
    5: "五黄土星",
    6: "六白金星",
    7: "七赤金星",
    8: "八白土星",
    9: "九紫火星",
}

# 雑に強い「年の説明」テンプレ（当て物じゃなく推薦の“納得材料”）
STAR_FLOW: Dict[int, Dict[str, str]] = {
    1: {"flow": "整える", "theme": "足元固め・内省・基盤づくり"},
    2: {"flow": "整える", "theme": "継続・育成・コツコツ積み上げ"},
    3: {"flow": "攻める", "theme": "スタート・発信・スピード感"},
    4: {"flow": "整える", "theme": "ご縁・調整・信頼を育てる"},
    5: {"flow": "切り替える", "theme": "刷新・手放し・方向転換"},
    6: {"flow": "攻める", "theme": "決断・責任・成果を取りに行く"},
    7: {"flow": "楽しむ", "theme": "喜び・社交・金運/循環を意識"},
    8: {"flow": "整える", "theme": "変化への準備・守り・蓄える"},
    9: {"flow": "攻める", "theme": "注目・評価・表現/感性を磨く"},
}


# ---- Helpers --------------------------------------------------------------

def parse_birthdate(s: Optional[str]) -> Optional[date]:
    """
    Accepts:
      - "YYYY-MM-DD"
      - "YYYY/MM/DD"
      - "YYYYMMDD"
    Returns date or None.
    """
    if not s or not isinstance(s, str):
        return None
    t = s.strip()
    if not t:
        return None

    # YYYYMMDD
    if len(t) == 8 and t.isdigit():
        try:
            return date(int(t[0:4]), int(t[4:6]), int(t[6:8]))
        except Exception:
            return None

    # YYYY-MM-DD / YYYY/MM/DD
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(t, fmt).date()
        except Exception:
            continue

    return None


def _ki_year(d: date, *, setsubun_month: int = DEFAULT_SETSUBUN_MONTH, setsubun_day: int = DEFAULT_SETSUBUN_DAY) -> int:
    """
    九星の年切替（節分/立春境界の簡易版）。
    d が境界より前なら前年扱い。
    """
    boundary = date(d.year, setsubun_month, setsubun_day)
    return d.year - 1 if d < boundary else d.year


def _star_num_from_year(y: int) -> StarNum:
    """
    九星（年盤）の基本式（最小実装）:
      num = 11 - (y % 9)
    結果は 1..9 に収まる。
    例: 1984 -> 7（七赤）
    """
    r = y % 9
    n = 11 - r
    # n は 2..11 になるので 1..9 に正規化
    n = ((n - 1) % 9) + 1
    return n  # type: ignore[return-value]


def _build_result(num: StarNum, ki_year: int) -> KyuseiResult:
    name = STAR_NAMES[int(num)]
    meta = STAR_FLOW.get(int(num), {"flow": "整える", "theme": "バランスを取る"})
    return KyuseiResult(
        num=num,
        name=name,
        ki_year=ki_year,
        flow_label_ja=meta["flow"],
        theme_ja=meta["theme"],
    )


# ---- Public API -----------------------------------------------------------

def honmei_star(birthdate: Optional[str], *, setsubun_month: int = DEFAULT_SETSUBUN_MONTH, setsubun_day: int = DEFAULT_SETSUBUN_DAY) -> Optional[KyuseiResult]:
    """
    本命星（生まれ年ベース。節分境界考慮の簡易版）
    """
    d = parse_birthdate(birthdate)
    if not d:
        return None
    ky = _ki_year(d, setsubun_month=setsubun_month, setsubun_day=setsubun_day)
    num = _star_num_from_year(ky)
    return _build_result(num, ky)


def year_star(
    today: Optional[date] = None,
    *,
    setsubun_month: int = DEFAULT_SETSUBUN_MONTH,
    setsubun_day: int = DEFAULT_SETSUBUN_DAY,
) -> KyuseiResult:
    """
    年星（今年の流れ）。today を渡さなければ timezone.localdate()
    """
    d = today or timezone.localdate()
    ky = _ki_year(d, setsubun_month=setsubun_month, setsubun_day=setsubun_day)
    num = _star_num_from_year(ky)
    return _build_result(num, ky)


def kyusei_signals(birthdate: Optional[str], *, today: Optional[date] = None) -> Optional[Dict[str, Any]]:
    """
    concierge 側に刺しやすい dict 形式（_signals 用）
    """
    honmei = honmei_star(birthdate)
    if not honmei:
        return None

    ys = year_star(today=today)
    return {
        "honmei": {
            "num": honmei.num,
            "name": honmei.name,
            "ki_year": honmei.ki_year,
        },
        "year": {
            "num": ys.num,
            "name": ys.name,
            "ki_year": ys.ki_year,
            "flow_label_ja": ys.flow_label_ja,
            "theme_ja": ys.theme_ja,
        },
        "note": "年切替は簡易的に2/4境界（立春近似）で計算しています",
    }


DIRECTION_PALACES = {"北": 1, "北東": 8, "東": 3, "南東": 4, "南": 9, "南西": 2, "西": 7, "北西": 6}
OPPOSITE_DIRECTION = {"北": "南", "北東": "南西", "東": "西", "南東": "北西", "南": "北", "南西": "北東", "西": "東", "北西": "南東"}
STAR_ELEMENTS = {1: "水", 2: "土", 3: "木", 4: "木", 5: "土", 6: "金", 7: "金", 8: "土", 9: "火"}
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
TAISAI_DIRECTIONS = ("北", "北東", "北東", "東", "南東", "南東", "南", "南西", "南西", "西", "北西", "北西")
SOLAR_MONTH_DIRECTIONS = ("北東", "東", "南東", "南東", "南", "南西", "南西", "西", "北西", "北西", "北", "北東")


def annual_lucky_directions(birthdate: Optional[str], *, today: Optional[date] = None) -> Optional[Dict[str, Any]]:
    """年盤の凶方位を除外し、本命星と比和・相生になる方位を返す。月盤・日盤は扱わない。"""
    honmei = honmei_star(birthdate)
    if not honmei:
        return None
    target = today or timezone.localdate()
    annual = year_star(today=target)
    stars = {
        direction: ((annual.num + palace - 5 - 1 + 18) % 9) + 1
        for direction, palace in DIRECTION_PALACES.items()
    }
    excluded: set[str] = set()
    five_yellow = next((direction for direction, star in stars.items() if star == 5), None)
    honmei_direction = next((direction for direction, star in stars.items() if star == honmei.num), None)
    for direction in (five_yellow, honmei_direction):
        if direction:
            excluded.add(direction)
            excluded.add(OPPOSITE_DIRECTION[direction])
    taisai = TAISAI_DIRECTIONS[(annual.ki_year - 4) % 12]
    excluded.add(OPPOSITE_DIRECTION[taisai])
    honmei_element = STAR_ELEMENTS[honmei.num]
    lucky = []
    for direction, star in stars.items():
        if direction in excluded:
            continue
        element = STAR_ELEMENTS[star]
        if element == honmei_element or GENERATES[element] == honmei_element or GENERATES[honmei_element] == element:
            lucky.append(direction)
    return {
        "luckyDirection": lucky[0] if lucky else None,
        "luckyDirections": lucky,
        "targetYear": annual.ki_year,
        "calculationMethod": "annual_kyusei_v1",
        "excludedDirections": [direction for direction in DIRECTION_PALACES if direction in excluded],
        "source": "calculated",
    }


def _solar_month_index(d: date) -> int:
    """寅月=0。節入り日は固定近似（2/4, 3/6, 4/5 ...）。"""
    boundaries = ((2, 4), (3, 6), (4, 5), (5, 6), (6, 6), (7, 7), (8, 8), (9, 8), (10, 8), (11, 7), (12, 7))
    index = 10 if (d.month, d.day) < (1, 6) else 11
    for candidate, boundary in enumerate(boundaries):
        if (d.month, d.day) >= boundary:
            index = candidate
    return index


def planned_visit_lucky_directions(birthdate: Optional[str], visit_date: Optional[str]) -> Optional[Dict[str, Any]]:
    """参拝予定日の年盤と月盤がともに吉となる方位を返す（日盤は対象外）。"""
    planned = parse_birthdate(visit_date)
    honmei = honmei_star(birthdate)
    if not planned or not honmei:
        return None
    annual = annual_lucky_directions(birthdate, today=planned)
    if not annual:
        return None
    month_index = _solar_month_index(planned)
    ki_year = year_star(today=planned).ki_year
    branch = (ki_year - 4) % 12
    start_star = 8 if branch in {0, 3, 6, 9} else 5 if branch in {1, 4, 7, 10} else 2
    month_center = ((start_star - month_index - 1) % 9) + 1
    stars = {
        direction: ((month_center + palace - 5 - 1 + 18) % 9) + 1
        for direction, palace in DIRECTION_PALACES.items()
    }
    excluded: set[str] = set()
    for target_star in (5, honmei.num):
        direction = next((key for key, star in stars.items() if star == target_star), None)
        if direction:
            excluded.add(direction)
            excluded.add(OPPOSITE_DIRECTION[direction])
    excluded.add(OPPOSITE_DIRECTION[SOLAR_MONTH_DIRECTIONS[month_index]])
    honmei_element = STAR_ELEMENTS[honmei.num]
    monthly_lucky = []
    for direction, star in stars.items():
        if direction in excluded:
            continue
        element = STAR_ELEMENTS[star]
        if element == honmei_element or GENERATES[element] == honmei_element or GENERATES[honmei_element] == element:
            monthly_lucky.append(direction)
    combined = [direction for direction in annual["luckyDirections"] if direction in monthly_lucky]
    all_excluded = [direction for direction in DIRECTION_PALACES if direction in set(annual["excludedDirections"]) | excluded]
    return {
        "luckyDirection": combined[0] if combined else None,
        "luckyDirections": combined,
        "targetYear": annual["targetYear"],
        "targetMonth": planned.month,
        "solarMonthIndex": month_index + 1,
        "visitDate": planned.isoformat(),
        "calculationMethod": "annual_monthly_kyusei_v1",
        "excludedDirections": all_excluded,
        "source": "calculated",
    }
