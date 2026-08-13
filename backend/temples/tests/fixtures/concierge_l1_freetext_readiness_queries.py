# backend/temples/tests/fixtures/concierge_l1_freetext_readiness_queries.py
"""L1 Free-text Recommendation Readiness Audit fixture set.

See docs/audit/concierge-l1-freetext-readiness.md. Natural-language
consultation sentences (not the fixed chip copy) across the themes
required by the audit brief, plus a required "ambiguous / weak intent"
group. No L2/L3 signal is attached to any case -- these are evaluated
with query only (see test_concierge_l1_freetext_readiness.py).

`theme` groups cases for the per-theme sections of the audit doc.
`intent_clarity` is "clear" or "ambiguous" -- used to split
clear_intent_other_rate from ambiguous_intent_other_rate (Task 7).
"""

CONCIERGE_L1_FREETEXT_READINESS_QUERIES = [
    # --- 仕事・キャリア (career) ---
    {
        "id": "l1_career_001",
        "query": "仕事を辞めるか迷っている",
        "theme": "career",
        "intent_clarity": "clear",
    },
    {
        "id": "l1_career_002",
        "query": "今の働き方を続けていいのか分からない",
        "theme": "career",
        "intent_clarity": "clear",
    },
    {
        "id": "l1_career_003",
        "query": "新しい仕事に挑戦したいけど不安",
        "theme": "career",
        "intent_clarity": "clear",
    },
    # --- 疲労・休息 (rest) ---
    {
        "id": "l1_rest_001",
        "query": "最近少し疲れていて気持ちを落ち着けたい",
        "theme": "rest",
        "intent_clarity": "clear",
    },
    {
        "id": "l1_rest_002",
        "query": "何も考えず少しゆっくりしたい",
        "theme": "rest",
        "intent_clarity": "clear",
    },
    {
        "id": "l1_rest_003",
        "query": "気持ちが張り詰めているので一度休みたい",
        "theme": "rest",
        "intent_clarity": "clear",
    },
    # --- 人間関係 (relationship) ---
    {
        "id": "l1_relationship_001",
        "query": "人間関係で少し疲れている",
        "theme": "relationship",
        "intent_clarity": "clear",
    },
    {
        "id": "l1_relationship_002",
        "query": "大切な人との関係を整理したい",
        "theme": "relationship",
        "intent_clarity": "clear",
    },
    {
        "id": "l1_relationship_003",
        "query": "職場の人間関係がうまくいかず悩んでいる",
        "theme": "relationship",
        "intent_clarity": "clear",
    },
    # --- 恋愛・縁 (love) ---
    {
        "id": "l1_love_001",
        "query": "恋愛について一度気持ちを整理したい",
        "theme": "love",
        "intent_clarity": "clear",
    },
    {
        "id": "l1_love_002",
        "query": "いい出会いがあればいいなと思っている",
        "theme": "love",
        "intent_clarity": "clear",
    },
    # --- お金・仕事成果 (money) ---
    {
        "id": "l1_money_001",
        "query": "仕事のお金の流れを良くしたい",
        "theme": "money",
        "intent_clarity": "clear",
    },
    {
        "id": "l1_money_002",
        "query": "これから事業をうまく軌道に乗せたい",
        "theme": "money",
        "intent_clarity": "clear",
    },
    # --- 一歩踏み出す (courage) ---
    {
        "id": "l1_courage_001",
        "query": "新しいことを始めたいけど勇気が出ない",
        "theme": "courage",
        "intent_clarity": "clear",
    },
    {
        "id": "l1_courage_002",
        "query": "環境を変えたいと思っている",
        "theme": "courage",
        "intent_clarity": "clear",
    },
    # --- 学業 (study, bonus theme for coverage) ---
    {
        "id": "l1_study_001",
        "query": "資格取得に向けて集中力を保ちたいけど自信がない",
        "theme": "study",
        "intent_clarity": "clear",
    },
    # --- 曖昧・弱いIntent (ambiguous, required) ---
    {
        "id": "l1_ambiguous_001",
        "query": "なんとなく神社に行きたい",
        "theme": "ambiguous",
        "intent_clarity": "ambiguous",
    },
    {
        "id": "l1_ambiguous_002",
        "query": "最近なんとなくモヤモヤしている",
        "theme": "ambiguous",
        "intent_clarity": "ambiguous",
    },
    {
        "id": "l1_ambiguous_003",
        "query": "少し気分転換したい",
        "theme": "ambiguous",
        "intent_clarity": "ambiguous",
    },
    {
        "id": "l1_ambiguous_004",
        "query": "特に悩みはないけどどこか行きたい",
        "theme": "ambiguous",
        "intent_clarity": "ambiguous",
    },
]
