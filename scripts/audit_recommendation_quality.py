from pathlib import Path
import json
import re
from difflib import SequenceMatcher
from datetime import datetime


FIXTURE_PATH = Path("fixtures/recommendation_audit/sample_recommendations.json")
OUTPUT_PATH = Path("logs/recommendation_quality_audit.json")


ABSTRACT_ACTION_WORDS = [
    "前向き",
    "行動しましょう",
    "整えましょう",
    "意識しましょう",
    "大切にしましょう",
]


SHALLOW_REASON_WORDS = [
    "ご利益",
    "おすすめです",
    "良い",
]

SIMILARITY_THRESHOLD = 0.78

NORMALIZATION_REPLACEMENTS = [
    ("3つ", "三つ"),
    ("おすすめです", ""),
    ("おすすめ", ""),
    ("神社です", ""),
    ("参拝先です", ""),
    ("があります", "がある"),
    ("あるため", "ある"),
    ("しましょう", "する"),
    ("してください", "する"),
    ("しておいてください", "する"),
]


def load_fixture():
    if not FIXTURE_PATH.exists():
        raise FileNotFoundError(f"Fixture not found: {FIXTURE_PATH}")

    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def score_reason_depth(reason: str) -> tuple[int, list[str]]:
    issues = []

    if len(reason) < 35:
        issues.append("推薦理由が短く、相談内容との接続が浅い可能性があります。")

    if any(word in reason for word in SHALLOW_REASON_WORDS):
        issues.append("推薦理由が一般的なご利益説明に寄っています。")

    score = 5 - len(issues)
    return max(score, 1), issues


def score_action_specificity(action: str) -> tuple[int, list[str]]:
    issues = []

    if len(action) < 25:
        issues.append("行動提案が短く、具体的な実行単位になっていません。")

    if any(word in action for word in ABSTRACT_ACTION_WORDS):
        issues.append("行動提案が抽象的です。")

    score = 5 - len(issues)
    return max(score, 1), issues


def score_history_theme_fit(user_query: str, history_theme: str) -> tuple[int, list[str]]:
    issues = []

    career_keywords = ["仕事", "働き方", "キャリア", "方向性"]
    love_keywords = ["恋愛", "結婚", "ご縁", "パートナー"]

    if any(word in user_query for word in career_keywords) and history_theme != "career":
        issues.append("相談内容はcareer寄りですが、history_themeが一致していません。")

    if any(word in user_query for word in love_keywords) and history_theme != "love":
        issues.append("相談内容はlove寄りですが、history_themeが一致していません。")

    score = 5 - len(issues) * 2
    return max(score, 1), issues


def normalize_for_similarity(text: str) -> str:
    normalized = text.strip()
    normalized = re.sub(r"[、。,.!！?？\s]", "", normalized)

    for source, replacement in NORMALIZATION_REPLACEMENTS:
        normalized = normalized.replace(source, replacement)

    return normalized


def character_ngrams(text: str, size: int = 2) -> set[str]:
    if len(text) <= size:
        return {text} if text else set()

    return {text[index : index + size] for index in range(len(text) - size + 1)}


def text_similarity(left: str, right: str) -> float:
    left_normalized = normalize_for_similarity(left)
    right_normalized = normalize_for_similarity(right)

    if not left_normalized or not right_normalized:
        return 0.0

    shorter, longer = sorted([left_normalized, right_normalized], key=len)
    contained_phrase_ratio = 0.0
    if len(shorter) >= 6 and shorter in longer:
        contained_phrase_ratio = 0.9

    sequence_ratio = SequenceMatcher(None, left_normalized, right_normalized).ratio()
    left_ngrams = character_ngrams(left_normalized)
    right_ngrams = character_ngrams(right_normalized)
    overlap_ratio = len(left_ngrams & right_ngrams) / len(left_ngrams | right_ngrams)

    return max(sequence_ratio, overlap_ratio, contained_phrase_ratio)


def find_near_duplicate_pairs(
    recommendations: list[dict],
    field_name: str,
) -> list[tuple[dict, dict, float]]:
    pairs = []

    for left_index, left_recommendation in enumerate(recommendations):
        left_text = left_recommendation.get(field_name, "")
        if not left_text:
            continue

        for right_recommendation in recommendations[left_index + 1 :]:
            right_text = right_recommendation.get(field_name, "")
            if not right_text:
                continue

            similarity = text_similarity(left_text, right_text)
            if similarity >= SIMILARITY_THRESHOLD:
                pairs.append((left_recommendation, right_recommendation, similarity))

    return pairs


def pair_label(pair: tuple[dict, dict, float]) -> str:
    left, right, similarity = pair
    left_name = left.get("shrine_name") or f"rank {left.get('rank')}"
    right_name = right.get("shrine_name") or f"rank {right.get('rank')}"
    return f"{left_name} / {right_name} ({similarity:.2f})"


def score_semantic_duplication(recommendations: list[dict]) -> tuple[int, list[str]]:
    issues = []

    duplicated_reason_pairs = find_near_duplicate_pairs(recommendations, "reason")
    duplicated_action_pairs = find_near_duplicate_pairs(recommendations, "action_suggestion")

    duplicated_reason_count = len(duplicated_reason_pairs)
    duplicated_action_count = len(duplicated_action_pairs)

    if duplicated_reason_count > 0:
        sample_pairs = "、".join(pair_label(pair) for pair in duplicated_reason_pairs[:3])
        issues.append(f"推薦理由に重複または近い表現があります: {sample_pairs}")

    if duplicated_action_count > 0:
        sample_pairs = "、".join(pair_label(pair) for pair in duplicated_action_pairs[:3])
        issues.append(f"行動提案に重複または近い表現があります: {sample_pairs}")

    score = 5 - duplicated_reason_count - duplicated_action_count
    return max(score, 1), issues


def audit_recommendation(user_query: str, recommendation: dict) -> dict:
    reason = recommendation.get("reason", "")
    action = recommendation.get("action_suggestion", "")
    history_theme = recommendation.get("history_theme", "")

    reason_score, reason_issues = score_reason_depth(reason)
    action_score, action_issues = score_action_specificity(action)
    theme_score, theme_issues = score_history_theme_fit(user_query, history_theme)

    scores = {
        "reason_depth": reason_score,
        "action_specificity": action_score,
        "history_theme_fit": theme_score,
    }

    overall_score = round(sum(scores.values()) / len(scores) * 20)
    issues = reason_issues + action_issues + theme_issues

    return {
        "rank": recommendation.get("rank"),
        "shrine_name": recommendation.get("shrine_name"),
        "history_theme": history_theme,
        "overall_score": overall_score,
        "audit_status": classify_audit_status(overall_score, issues),
        "scores": scores,
        "issues": issues,
    }


def classify_audit_status(overall_score: int, issues: list[str]) -> str:
    if overall_score < 50:
        return "fail"

    if overall_score < 70:
        return "warn"

    if len(issues) >= 4:
        return "warn"

    return "pass"


def validate_semantic_duplication_detector():
    recommendations = [
        {
            "rank": 1,
            "shrine_name": "A神社",
            "reason": "仕事運にご利益があるためおすすめです。",
            "action_suggestion": "参拝後に、今の職場で伸ばせる専門性と転職で得たい条件を三つずつ書き出してください。",
        },
        {
            "rank": 2,
            "shrine_name": "B神社",
            "reason": "仕事運のご利益があります。",
            "action_suggestion": "参拝後、今の職場で伸ばせる専門性と転職で得たい条件を3つずつ書き出してください。",
        },
        {
            "rank": 3,
            "shrine_name": "C神社",
            "reason": "静かな境内で自分の考えを整理し、次の選択を落ち着いて見直す相談に向いています。",
            "action_suggestion": "帰宅後に今週断る予定を一つだけ選び、短い返事の文面を作ってください。",
        },
    ]

    score, issues = score_semantic_duplication(recommendations)

    if score >= 5:
        raise AssertionError("near-duplicate recommendation reasons/actions were not detected")

    if not any("推薦理由" in issue for issue in issues):
        raise AssertionError("near-duplicate recommendation reasons were not reported")

    if not any("行動提案" in issue for issue in issues):
        raise AssertionError("near-duplicate action suggestions were not reported")


def main():
    validate_semantic_duplication_detector()
    cases = load_fixture()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    audit_results = []

    for case in cases:
        user_query = case.get("user_query", "")
        recommendations = case.get("recommendations", [])

        duplication_score, duplication_issues = score_semantic_duplication(recommendations)

        case_result = {
            "case_id": case.get("case_id"),
            "user_query": user_query,
            "recommendation_count": len(recommendations),
            "semantic_duplication": {
                "score": duplication_score,
                "issues": duplication_issues,
            },
            "results": [
                audit_recommendation(user_query, recommendation)
                for recommendation in recommendations
            ],
        }

        audit_results.append(case_result)

    output = {
        "generated_at": datetime.now().isoformat(),
        "status": "ok",
        "audit_type": "rule_based_v1",
        "results": audit_results,
    }

    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"✅ Audit result saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
