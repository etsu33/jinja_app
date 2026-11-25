"""気持ち（mental）の文字の語に「厄除」「厄払い」を入れない（2026-11-23 えつこ決定）。

厄除けは「守護・厄除け」の相談（protection）で、ご利益の対応表から扱う。
決まりの正本：ドライブ「KAMI MUSUBI 相談の種類を取る辞書の決まり」
"""

from temples.domain.need_to_goriyaku_concepts import NEED_TO_GORIYAKU_CONCEPTS
from temples.services.concierge_chat_ranking import NEED_TEXT_WEIGHTS


def test_mental_text_weights_do_not_contain_yakuyoke():
    assert "厄除" not in NEED_TEXT_WEIGHTS["mental"]
    assert "厄払い" not in NEED_TEXT_WEIGHTS["mental"]


def test_protection_still_covers_misfortune_warding():
    assert "misfortune_warding" in NEED_TO_GORIYAKU_CONCEPTS["protection"]
