"""MS-5: Channel B（Source Fact）だけが一致した Need の理由文。

docs/audit/shrine-expansion-wave0-db04-f1-goriyaku-mapping-boundary.md §12.14
（REASON_COPY_BOUNDARY = EVIDENCE_TYPED_CLAIM_STRENGTH）を、候補の既存の carrier
（PR-C の TypedNeedMatch）だけで実装する。DB は読まない。

- 事実の文の強さは evidence characterization（= TypedNeedMatch.signal_type）で決まる
  （E2 → 祈願の案内 / E3 → 現在の案内 / list 単位の併記 → まとめた claim）。「ご利益で知られる」（C1）は作らない。
- Source に帰属させる文字列は source_attested_wording だけ。canonical concept は Source の文言として示さない。
- Need の一致は事実の claim を強めない。Need に関する部分は事実の文と分けた Interpretation の文にする。
- 想定外の signal_type・wording が空のときは None を返し、呼び出し側は既存の generic fallback を使う。
"""

from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence

from temples.services.channel_b_typed_need_match import (
    CHANNEL_B_TYPED_NEED_MATCHES_KEY,
    TypedNeedMatch,
)

# evidence characterization → 事実の文の template（{subject} は「{name}の」または空）。
CHANNEL_B_FACT_TEMPLATES: dict[str, str] = {
    "official_prayer_supported": "{subject}公式の祈願案内に『{wording}』の記載があります。",
    "official_current_guidance_supported": "{subject}公式の現在の案内に『{wording}』の記載があります。",
    "official_prayer_and_current_guidance_list_level": (
        "{subject}公式の祈願・現在の案内の一覧に『{wording}』が含まれています。"
    ),
}
# Interpretation の文（神社の事実を新たに断定しない）。
CHANNEL_B_INTERPRETATION_TEXT = "今の悩みや願いに合わせて参拝先の候補に入れています。"


def select_channel_b_reason_match(
    rec: dict[str, Any],
    need_tags_clean: Sequence[str],
    channel_a_need_keys: Iterable[str],
) -> Optional[TypedNeedMatch]:
    """理由文に使う TypedNeedMatch を1件選ぶ（無ければ None）。

    request の Need の順で、Channel A が一致していない最初の Need を選ぶ。同じ Need の中では
    source_fact_key の順で最初のものを選ぶ（DB の id は使わない）。
    """
    carrier = rec.get(CHANNEL_B_TYPED_NEED_MATCHES_KEY)
    if not isinstance(carrier, (tuple, list)):
        return None
    matches = [
        item
        for item in carrier
        if isinstance(item, TypedNeedMatch)
        and isinstance(item.need, str)
        and isinstance(item.source_fact_key, str)
    ]
    channel_a = set(channel_a_need_keys)
    for need in need_tags_clean:
        if need in channel_a:
            continue
        same_need = sorted(
            (item for item in matches if item.need == need),
            key=lambda item: item.source_fact_key,
        )
        if same_need:
            return same_need[0]
    return None


def render_channel_b_reason(match: TypedNeedMatch, *, name: str) -> Optional[str]:
    """選んだ match から理由文を作る。安全に作れないときは None。"""
    template = CHANNEL_B_FACT_TEMPLATES.get(str(match.signal_type or ""))
    wording = match.source_attested_wording
    if template is None or not isinstance(wording, str) or not wording.strip():
        return None
    subject = f"{name}の" if name else ""
    fact = template.format(subject=subject, wording=wording.strip())
    return fact + CHANNEL_B_INTERPRETATION_TEXT
