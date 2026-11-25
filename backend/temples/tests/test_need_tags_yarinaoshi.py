"""やり直し系の言葉を、相談の種類の挑戦（courage）だけにつなぐ。

決まりの正本：ドライブ「KAMI MUSUBI 相談の種類を取る辞書の決まり」（2026-11-22 えつこ決定）
- 言葉：やり直し・やり直す・再出発・再挑戦・立て直し
- 最初は気持ち（mental）にもつないだが、本番で遠い神社が上位に来たため、挑戦だけにした
- 「もう一度」は足さない（相談ではない文でも当たるため）
"""

import pytest

from temples.domain.need_tags import KEYWORDS, extract_need_tags
from temples.services.consultation_interpreter import NEED_KEYWORDS

YARINAOSHI_WORDS = ["やり直し", "やり直す", "再出発", "再挑戦", "立て直し"]


@pytest.mark.parametrize(
    "query",
    [
        "やり直したい",
        "人生をやり直したい",
        "一からやり直す",
        "再出発したい",
        "再挑戦したい",
        "立て直したい",
    ],
)
def test_yarinaoshi_extracts_courage_only(query):
    assert extract_need_tags(query).tags == ["courage"]


def test_mou_ichido_alone_is_not_a_need():
    assert extract_need_tags("もう一度行きたい").tags == []


def test_existing_queries_are_unchanged():
    assert extract_need_tags("転職したい").tags == ["career"]
    assert extract_need_tags("もう一度挑戦したい").tags == ["courage"]


def test_career_is_kept_with_yarinaoshi():
    assert extract_need_tags("仕事でやり直したい").tags[0] == "career"


def test_words_are_in_courage_only_in_both_tables():
    for word in YARINAOSHI_WORDS:
        assert word in KEYWORDS["courage"]
        assert word in NEED_KEYWORDS["courage"]
        assert word not in KEYWORDS["mental"]
        assert word not in NEED_KEYWORDS["mental"]
