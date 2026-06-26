from pathlib import Path
import json
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

def score_semantic_duplication(recommendations: list[dict]) -> tuple[int, list[str]]:
    issues = []

    reasons = [
        recommendation.get("reason", "")
        for recommendation in recommendations
    ]

    actions = [
        recommendation.get("action_suggestion", "")
        for recommendation in recommendations
    ]

    duplicated_reason_count = len(reasons) - len(set(reasons))
    duplicated_action_count = len(actions) - len(set(actions))

    if duplicated_reason_count > 0:
        issues.append("推薦理由に重複があります。")

    if duplicated_action_count > 0:
        issues.append("行動提案に重複があります。")

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


def main():
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
