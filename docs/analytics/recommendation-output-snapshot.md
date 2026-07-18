> **Status: Archive**
>
> 本ドキュメントは、Recommendation Score v2の実出力を保存した時点スナップショットである。
>
> 現行の出力は実際のAPIレスポンスおよび関連する実装コードを最終的な正本とする。

# Recommendation Output Snapshot

## 目的

Representative case ごとの Recommendation Score v2 実出力を保存する。

この snapshot は、推薦結果が検索結果ではなく、ユーザー状態と神社意味の接続になっているかを確認するための監査資料である。

---

## 実行条件

- candidates_count: `105`
- source: `build_chat_recommendations`
- output: `docs/analytics/recommendation-output-snapshot.md`

---

## 転職不安

- case_id: `career-anxiety`
- query: 転職が不安で、背中を押してほしい
- public_mode: `need`
- flow: `A`
- birthdate: `-`
- extra_condition: `-`
- expected_need_tags: `career / mental / courage`
- actual_need_tags: `career / mental / courage`
- expected_history_theme: `勝負 / 導き / 再出発`
- displayed_count: `-`

#### 1. 妙義神社

- shrine_id: `88`
- history_theme: `勝負`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `career / mental / courage`
- matched_visit_style_tags: `-`
- score_v2.total: `4.8`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 4.8000 |
| `shrine_meaning_match` | 0.9000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「前進・後押し」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 16.0, 'weight': 0.3, 'contribution': 4.8}`

##### rank_comparison

- label: -
- summary: -
- top_summary: 相談内容との一致は「前進・後押し」が主因です。特に 悩みとの一致 が順位を押し上げています。

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 2. 武蔵御嶽神社

- shrine_id: `71`
- history_theme: `静寂`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `career / mental / courage`
- matched_visit_style_tags: `-`
- score_v2.total: `4.8`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 4.8000 |
| `shrine_meaning_match` | 0.9000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「前進・後押し」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 16.0, 'weight': 0.3, 'contribution': 4.8}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 3. 石清水八幡宮

- shrine_id: `12`
- history_theme: `守り`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `career / mental / courage`
- matched_visit_style_tags: `-`
- score_v2.total: `4.8`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 4.8000 |
| `shrine_meaning_match` | 0.9000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「前進・後押し」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 16.0, 'weight': 0.3, 'contribution': 4.8}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

---

## 疲労回復

- case_id: `rest-quiet`
- query: 最近疲れていて、静かに落ち着きたい
- public_mode: `need`
- flow: `A`
- birthdate: `-`
- extra_condition: `静かに過ごしたい`
- expected_need_tags: `mental / rest`
- actual_need_tags: `mental / rest`
- expected_history_theme: `静寂 / 復興`
- displayed_count: `-`

#### 1. 護王神社

- shrine_id: `99`
- history_theme: `復興`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `mental / rest`
- matched_visit_style_tags: `quiet`
- score_v2.total: `2.27`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 1.9200 |
| `shrine_meaning_match` | 0.6000 |
| `context_match` | 0.3500 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「不安・心」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 6.4, 'weight': 0.3, 'contribution': 1.92}`

##### rank_comparison

- label: -
- summary: -
- top_summary: 相談内容との一致は「不安・心」が主因です。特に 悩みとの一致 が順位を押し上げています。

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 2. 酒列磯前神社

- shrine_id: `83`
- history_theme: `復興`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `mental / rest`
- matched_visit_style_tags: `quiet`
- score_v2.total: `2.27`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 1.9200 |
| `shrine_meaning_match` | 0.6000 |
| `context_match` | 0.3500 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「不安・心」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 6.4, 'weight': 0.3, 'contribution': 1.92}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 3. 高良大社

- shrine_id: `96`
- history_theme: `復興`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `mental / rest`
- matched_visit_style_tags: `quiet`
- score_v2.total: `2.27`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 1.9200 |
| `shrine_meaning_match` | 0.6000 |
| `context_match` | 0.3500 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「不安・心」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 6.4, 'weight': 0.3, 'contribution': 1.92}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

---

## 金運・事業

- case_id: `money-business-flow`
- query: 売上を伸ばしたい。事業の流れを良くしたい
- public_mode: `need`
- flow: `A`
- birthdate: `-`
- extra_condition: `-`
- expected_need_tags: `money / career / courage`
- actual_need_tags: `money / courage`
- expected_history_theme: `巡り / 勝負`
- displayed_count: `-`

#### 1. 千住神社

- shrine_id: `67`
- history_theme: `勝負`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `money / courage`
- matched_visit_style_tags: `-`
- score_v2.total: `3.7199999999999998`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 3.7200 |
| `shrine_meaning_match` | 0.6000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「前進・後押し」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 12.4, 'weight': 0.3, 'contribution': 3.7199999999999998}`

##### rank_comparison

- label: -
- summary: -
- top_summary: 相談内容との一致は「前進・後押し」が主因です。特に 悩みとの一致 が順位を押し上げています。

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 2. 宮地嶽神社

- shrine_id: `39`
- history_theme: `勝負`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `money / courage`
- matched_visit_style_tags: `-`
- score_v2.total: `3.7199999999999998`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 3.7200 |
| `shrine_meaning_match` | 0.6000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「前進・後押し」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 12.4, 'weight': 0.3, 'contribution': 3.7199999999999998}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 3. 富岡八幡宮

- shrine_id: `49`
- history_theme: `勝負`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `money / courage`
- matched_visit_style_tags: `-`
- score_v2.total: `3.7199999999999998`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 3.7200 |
| `shrine_meaning_match` | 0.6000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「前進・後押し」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 12.4, 'weight': 0.3, 'contribution': 3.7199999999999998}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

---

## 縁結び

- case_id: `relationship-marriage`
- query: 良縁がほしい。人との関係を見直したい
- public_mode: `need`
- flow: `A`
- birthdate: `-`
- extra_condition: `-`
- expected_need_tags: `marriage / relationship / love`
- actual_need_tags: `love`
- expected_history_theme: `縁`
- displayed_count: `-`

#### 1. 東京大神宮

- shrine_id: `44`
- history_theme: `縁`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `love`
- matched_visit_style_tags: `-`
- score_v2.total: `3.48`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 3.4800 |
| `shrine_meaning_match` | 0.3000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「恋愛」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 11.6, 'weight': 0.3, 'contribution': 3.48}`

##### rank_comparison

- label: -
- summary: -
- top_summary: 相談内容との一致は「恋愛」が主因です。特に 悩みとの一致 が順位を押し上げています。

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 2. 九頭龍神社 新宮

- shrine_id: `93`
- history_theme: `縁`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `love`
- matched_visit_style_tags: `-`
- score_v2.total: `1.68`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 1.6800 |
| `shrine_meaning_match` | 0.3000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「恋愛」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 5.6, 'weight': 0.3, 'contribution': 1.68}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 3. 二荒山神社

- shrine_id: `54`
- history_theme: `縁`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `love`
- matched_visit_style_tags: `-`
- score_v2.total: `1.68`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 1.6800 |
| `shrine_meaning_match` | 0.3000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「恋愛」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 5.6, 'weight': 0.3, 'contribution': 1.68}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

---

## 学業・集中

- case_id: `study-focus`
- query: 資格試験に合格したい。集中したい
- public_mode: `need`
- flow: `A`
- birthdate: `-`
- extra_condition: `-`
- expected_need_tags: `study / focus`
- actual_need_tags: `study / focus`
- expected_history_theme: `学び`
- displayed_count: `-`

#### 1. 亀戸天神社

- shrine_id: `47`
- history_theme: `学び`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `study / focus`
- matched_visit_style_tags: `study`
- score_v2.total: `4.01`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 3.6600 |
| `shrine_meaning_match` | 0.6000 |
| `context_match` | 0.3500 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「focus」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 12.2, 'weight': 0.3, 'contribution': 3.6599999999999997}`

##### rank_comparison

- label: -
- summary: -
- top_summary: 相談内容との一致は「focus」が主因です。特に 悩みとの一致 が順位を押し上げています。

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 2. 太宰府天満宮

- shrine_id: `6`
- history_theme: `学び`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `study / focus`
- matched_visit_style_tags: `study`
- score_v2.total: `4.01`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 3.6600 |
| `shrine_meaning_match` | 0.6000 |
| `context_match` | 0.3500 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「focus」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 12.2, 'weight': 0.3, 'contribution': 3.6599999999999997}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 3. 湯島天満宮

- shrine_id: `64`
- history_theme: `学び`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `study / focus`
- matched_visit_style_tags: `study`
- score_v2.total: `4.01`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 3.6600 |
| `shrine_meaning_match` | 0.6000 |
| `context_match` | 0.3500 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「focus」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 12.2, 'weight': 0.3, 'contribution': 3.6599999999999997}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

---

## 厄除け・浄化

- case_id: `protection-cleansing`
- query: 最近流れが悪い。厄を落としたい
- public_mode: `need`
- flow: `A`
- birthdate: `-`
- extra_condition: `-`
- expected_need_tags: `protection / mental / courage`
- actual_need_tags: `-`
- expected_history_theme: `浄化 / 守り / 巡り`
- displayed_count: `-`

#### 1. admin承認テスト神社

- shrine_id: `102`
- history_theme: `-`
- reason_source: `reason:original`
- action_state: `none`
- matched_need_tags: `-`
- matched_visit_style_tags: `-`
- score_v2.total: `-`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 0.0000 |
| `shrine_meaning_match` | 0.0000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 近さや候補条件を含めた総合順位です。
- primary_axis: `fallback`
- top_contributors: `-`

##### rank_comparison

- label: -
- summary: -
- top_summary: 近さや候補条件を含めた総合順位です。

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 2. 三峯神社

- shrine_id: `17`
- history_theme: `勝負`
- reason_source: `reason:original`
- action_state: `none`
- matched_need_tags: `-`
- matched_visit_style_tags: `-`
- score_v2.total: `-`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 0.0000 |
| `shrine_meaning_match` | 0.0000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 近さや候補条件を含めた総合順位です。
- primary_axis: `fallback`
- top_contributors: `-`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 3. 乃木神社

- shrine_id: `59`
- history_theme: `勝負`
- reason_source: `reason:original`
- action_state: `none`
- matched_need_tags: `-`
- matched_visit_style_tags: `-`
- score_v2.total: `-`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 0.0000 |
| `shrine_meaning_match` | 0.0000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 近さや候補条件を含めた総合順位です。
- primary_axis: `fallback`
- top_contributors: `-`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

---

## 旅行・出張安全

- case_id: `travel-safe`
- query: 出張前に安全に移動したい
- public_mode: `need`
- flow: `A`
- birthdate: `-`
- extra_condition: `-`
- expected_need_tags: `travel_safe`
- actual_need_tags: `travel_safe`
- expected_history_theme: `導き / 守り`
- displayed_count: `-`

#### 1. 住吉大社

- shrine_id: `11`
- history_theme: `守り`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `travel_safe`
- matched_visit_style_tags: `-`
- score_v2.total: `0.6`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 0.6000 |
| `shrine_meaning_match` | 0.3000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「travel_safe」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 2.0, 'weight': 0.3, 'contribution': 0.6}`

##### rank_comparison

- label: -
- summary: -
- top_summary: 相談内容との一致は「travel_safe」が主因です。特に 悩みとの一致 が順位を押し上げています。

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 2. 住吉神社（博多）

- shrine_id: `57`
- history_theme: `守り`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `travel_safe`
- matched_visit_style_tags: `-`
- score_v2.total: `0.6`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 0.6000 |
| `shrine_meaning_match` | 0.3000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「travel_safe」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 2.0, 'weight': 0.3, 'contribution': 0.6}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 3. 厳島神社

- shrine_id: `38`
- history_theme: `縁`
- reason_source: `reason:matched_need_tags`
- action_state: `none`
- matched_need_tags: `travel_safe`
- matched_visit_style_tags: `-`
- score_v2.total: `0.6`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 0.6000 |
| `shrine_meaning_match` | 0.3000 |
| `context_match` | 0.0000 |
| `element_match` | 0.0000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.0000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「travel_safe」が主因です。特に 悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 2.0, 'weight': 0.3, 'contribution': 0.6}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

---

## 相性補助ありの仕事相談

- case_id: `compat-career`
- query: 仕事の流れを整えて、次の一歩を決めたい
- public_mode: `compat`
- flow: `B`
- birthdate: `1988-03-12`
- extra_condition: `-`
- expected_need_tags: `career / courage`
- actual_need_tags: `career / courage`
- expected_history_theme: `導き / 勝負 / 再出発`
- displayed_count: `-`

#### 1. 宇佐神宮

- shrine_id: `8`
- history_theme: `勝負`
- reason_source: `reason:compat`
- action_state: `none`
- matched_need_tags: `career / courage`
- matched_visit_style_tags: `quiet`
- score_v2.total: `4.15`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 1.6000 |
| `shrine_meaning_match` | 0.4000 |
| `context_match` | 0.3500 |
| `element_match` | 1.6000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.6000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「前進・後押し」が主因です。特に 生年月日との相性・悩みとの一致 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'element', 'axis_ja': '生年月日との相性', 'raw': 2.0, 'weight': 0.8, 'contribution': 1.6} / {'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 8.0, 'weight': 0.2, 'contribution': 1.6}`

##### rank_comparison

- label: -
- summary: -
- top_summary: 相談内容との一致は「前進・後押し」が主因です。特に 生年月日との相性・悩みとの一致 が順位を押し上げています。

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 2. 妙義神社

- shrine_id: `88`
- history_theme: `勝負`
- reason_source: `reason:compat`
- action_state: `none`
- matched_need_tags: `career / courage`
- matched_visit_style_tags: `quiet`
- score_v2.total: `3.77`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 2.3200 |
| `shrine_meaning_match` | 0.4000 |
| `context_match` | 0.3500 |
| `element_match` | 0.8000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.3000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「前進・後押し」が主因です。特に 悩みとの一致・生年月日との相性 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 11.6, 'weight': 0.2, 'contribution': 2.32} / {'axis': 'element', 'axis_ja': '生年月日との相性', 'raw': 1.0, 'weight': 0.8, 'contribution': 0.8}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

#### 3. 武蔵御嶽神社

- shrine_id: `71`
- history_theme: `静寂`
- reason_source: `reason:compat`
- action_state: `none`
- matched_need_tags: `career / courage`
- matched_visit_style_tags: `quiet`
- score_v2.total: `3.77`

##### score_v2.components

| component | value |
|---|---:|
| `user_state_match` | 2.3200 |
| `shrine_meaning_match` | 0.4000 |
| `context_match` | 0.3500 |
| `element_match` | 0.8000 |
| `distance_score` | 0.0000 |
| `popularity_score` | 0.0000 |
| `astro_bonus` | 0.3000 |
| `behavior_signal` | 0.0000 |
| `behavior_contribution` | 0.0000 |
| `capped_behavior_contribution` | 0.0000 |
| `behavior_ratio` | 0.0000 |
| `direction_bonus` | 0.0000 |

##### rank_explanation

- summary: 相談内容との一致は「前進・後押し」が主因です。特に 悩みとの一致・生年月日との相性 が順位を押し上げています。
- primary_axis: `need`
- top_contributors: `{'axis': 'need', 'axis_ja': '悩みとの一致', 'raw': 11.6, 'weight': 0.2, 'contribution': 2.32} / {'axis': 'element', 'axis_ja': '生年月日との相性', 'raw': 1.0, 'weight': 0.8, 'contribution': 0.8}`

##### rank_comparison

- label: -
- summary: -
- top_summary: -

##### _explanation_payload

- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -

---

## TODO

```markdown
- [x] representative case を8件定義
- [x] build_chat_recommendations を service 直叩きで実行
- [x] recommendations_v2 相当の top3 recommendations を保存
- [x] score_v2 を保存
- [x] rank_explanation を保存
- [x] rank_comparison を保存
- [x] _explanation_payload を保存
- [x] docs/analytics/recommendation-output-snapshot.md 作成
- [ ] 実出力を見て検索結果化していないか判定
- [ ] 代表ケースごとの差分を次PRで改善候補へ分解
```
