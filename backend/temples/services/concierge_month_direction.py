"""コンシェルジュの結果に添える「今月の方角」.

ドライブ「KAMI MUSUBI コンシェルジュとコンパスの役割の線引き」（2026-11-26 えつこさん決定）:

- 生年月日はコンシェルジュの並び順には使わない（PR #3464 のまま）。
  この module は並び順を決めたあとの結果に、情報を添えるだけ。順位・点数・推薦理由は変えない。
- 出す人: マイページで生年月日を登録した、ログイン中の人だけ。
  生年月日はサーバーのプロフィール（users.UserProfile.birthday）からだけ読む。
  相談で送られてきた生年月日（本文・filters・profile_context）は、今までどおり使わない。
- 結果の上に1回だけ「今月のあなたの方角」を出す（応答の month_direction）。
- その方角にある神社にだけ in_month_direction: true を付ける。合わない神社には何も付けない
  （「方角が違う」という情報は応答に含めない）。凶方位は扱わない。
- 方角はコンパスと同じ九星（年盤・月盤。共通方位が無いときは月盤）で計算する
  （temples.services.compass_runtime.build_compass_direction_runtime）。西洋の四元素は使わない。
- 神社ごとの印は、相談に出発地点があるときだけ。無いときは month_direction だけ。
- 英語（インバウンド）の相談には出さない。

既存の direction_reference（予定日の参考方位と、一致・不一致の両方を持つ）とは別の項目にする。
direction_reference は「異なります」も表示する作りのため、この決定には使わない。
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Iterable, Mapping, Optional

from temples.services.compass_runtime import build_compass_direction_runtime
from temples.services.direction_reference import _bearing, _coordinate, _direction_label

logger = logging.getLogger(__name__)

IN_MONTH_DIRECTION_KEY = "in_month_direction"
SUPPORTED_LANGUAGE = "ja"


def resolve_registered_birthday(user: Any) -> Optional[str]:
    """ログイン中の人がサーバーのプロフィールに登録した生年月日（YYYY-MM-DD）。無ければ None。"""
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    try:
        profile = user.profile
    except Exception:
        # プロフィールが無い人（作られていない人）もいる。
        return None
    birthday = getattr(profile, "birthday", None)
    if isinstance(birthday, date):
        return birthday.isoformat()
    return None


def _clear_marks(recommendation_lists: Iterable[list[Any]]) -> None:
    for recommendations in recommendation_lists:
        for recommendation in recommendations:
            if isinstance(recommendation, dict):
                recommendation.pop(IN_MONTH_DIRECTION_KEY, None)


def _mark_recommendations(
    recommendation_lists: Iterable[list[Any]],
    *,
    origin: Mapping[str, Any] | None,
    reference_directions: set[str],
) -> None:
    origin_lat = _coordinate(origin, "lat", "latitude") if origin else None
    origin_lng = _coordinate(origin, "lng", "longitude") if origin else None
    has_origin = origin_lat is not None and origin_lng is not None

    for recommendations in recommendation_lists:
        for recommendation in recommendations:
            if not isinstance(recommendation, dict):
                continue
            recommendation.pop(IN_MONTH_DIRECTION_KEY, None)
            if not has_origin:
                continue
            shrine_lat = _coordinate(recommendation, "latitude", "lat")
            shrine_lng = _coordinate(recommendation, "longitude", "lng")
            if shrine_lat is None or shrine_lng is None:
                continue
            try:
                label = _direction_label(
                    _bearing(
                        from_lat=origin_lat,
                        from_lng=origin_lng,
                        to_lat=shrine_lat,
                        to_lng=shrine_lng,
                    )
                )
            except Exception:
                # 神社のデータと利用者の入力はログに出さない。
                logger.error("concierge_month_direction_candidate_failed")
                continue
            if label in reference_directions:
                recommendation[IN_MONTH_DIRECTION_KEY] = True


def build_concierge_month_direction(
    *,
    user: Any,
    language: Optional[str],
    origin: Mapping[str, Any] | None,
    recommendation_lists: Iterable[list[Any]],
    target_date: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """条件がそろえば month_direction を返し、方角に当たる神社へ印を付ける。

    条件がそろわないとき（ログインしていない・生年月日が未登録・英語・方角が出ない）は
    None を返し、神社の印も外す。並び順・点数・推薦理由には触れない。
    `target_date` はテスト用の注入点で、省略時は今日（Asia/Tokyo）。
    """
    lists = [items for items in recommendation_lists if isinstance(items, list)]

    if (language or SUPPORTED_LANGUAGE).strip().lower() != SUPPORTED_LANGUAGE:
        _clear_marks(lists)
        return None

    birthday = resolve_registered_birthday(user)
    if not birthday:
        _clear_marks(lists)
        return None

    runtime = build_compass_direction_runtime(birthdate=birthday, target_date=target_date)
    if not isinstance(runtime, dict):
        # 計算できない・今月は方角が無い。何も添えない（「方角が無い」とも書かない）。
        _clear_marks(lists)
        return None

    reference_directions = [
        str(value) for value in runtime.get("referenceDirections") or [] if str(value).strip()
    ]
    if not reference_directions:
        _clear_marks(lists)
        return None

    _mark_recommendations(lists, origin=origin, reference_directions=set(reference_directions))

    # 生年月日そのものは応答に含めない。
    return {
        "reference_directions": reference_directions,
        "calculation_method": runtime.get("calculationMethod"),
        "target_date": runtime.get("targetDate"),
        "note": runtime.get("note"),
    }


__all__ = [
    "IN_MONTH_DIRECTION_KEY",
    "build_concierge_month_direction",
    "resolve_registered_birthday",
]
