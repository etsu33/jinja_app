# Compass Need Lead Purpose Alignment — Implementation

## Scope

Lead selection responsibility のみを変更した。Ranking / Scoring / Mapping（`NEED_TO_GORIYAKU_IDS`）/ Text Coverage（`NEED_TEXT_WEIGHTS`）/ `PRIMARY_REASON_PRIORITY` / Reason Body（`intent_map`/`mapping`辞書の文言そのもの）は一切変更していない。

## Adopted Option

[[compass-need-lead-purpose-alignment.md]]（PR #2556）の推奨 `USE_MATCHED_EVIDENCE_CHAIN`（Option C）をそのまま実装した。別Optionへの変更は行っていない。

## Before

`_build_need_lead(tag, goriyaku)` は goriyaku文字列の先頭要素（`・`区切りの最初の項目）を、Purpose/matched evidenceと無関係に採用していた。

## After

優先順位:

1. matched goriyaku_tag label（Purpose∩候補GID、GID id昇順で決定的に1件選択）
2. matched text_hint（`_prefilter_debug.matched_text_hints_by_tag`、weight最大の語）
3. 既存Purpose fallback辞書
4. generic fallback（`"ご利益"`）

`goriyaku`引数自体は呼び出し元シグネチャの安定性のために残したが、Lead選択には一切使用しない。

### 変更した関数

- `backend/temples/services/concierge_chat_ranking.py`
  - `_build_need_lead(tag, goriyaku, *, matched_gid_label=None, matched_text_hint=None)` — 優先順位をEvidence Chainへ変更。
  - `_build_need_reason_text(tag, *, name="", goriyaku="", matched_gid_label=None, matched_text_hint=None)` — 新パラメータを`_build_need_lead`へ橋渡し。
  - `_resolve_matched_lead_evidence(rec, tag, need_gid_label_by_id)`（新規） — `rec["goriyaku_tag_ids"]`と`NEED_TO_GORIYAKU_IDS`（既存の`need_tags_to_goriyaku_ids`ヘルパ経由）から matched GID を、`rec["_prefilter_debug"]["matched_text_hints_by_tag"]`から matched text hint を、追加DBクエリなしで解決する。
  - `build_recommendation_reason(rec, *, public_mode, birthdate, need_tags, need_gid_label_by_id=None)` — 新パラメータを追加し、`_resolve_matched_lead_evidence`の結果を`_build_need_reason_text`へ渡す。
- `backend/temples/services/concierge_chat.py`
  - importに`NEED_TO_GORIYAKU_IDS`を追加（既存モジュールの参照のみ、変更なし）。
  - `_attach_chat_rec_enrichment`に`need_gid_label_by_id`パラメータを追加し、`build_recommendation_reason`へ橋渡し。
  - リクエストにつき1回、`need_tags`が期待するGoriyakuTag id集合（`NEED_TO_GORIYAKU_IDS`由来）に対して既存の`_build_goriyaku_tag_label_by_id`ヘルパを再利用したバッチクエリ（`need_gid_label_by_id`）を新設。既存の`goriyaku_tag_label_by_id`（ユーザー選択GID検索専用、Compass経路では常に空）とは別物。

## Five-Purpose Results（同一fixture: origin=(35.662443, 139.5920237), direction=["東"], targetDate=2026-08-23, distance_stage=15km, 候補12件）

Top3のBefore/After Lead（Before値は[[compass-need-lead-purpose-alignment.md]] Phase A4のベースラインを再掲）:

| Purpose | Rank | Shrine | Before Lead | After Lead | Alignment |
|---|---:|---|---|---|---|
| love | 1 | 東京大神宮(44) | 縁結び | 縁結び | ALIGNED→ALIGNED |
| love | 2 | 明治神宮(1) | 縁結び | 縁結び | ALIGNED→ALIGNED |
| love | 3 | 赤坂氷川神社(60) | 縁結び | 縁結び | ALIGNED→ALIGNED |
| career | 1 | 乃木神社(59) | 仕事運 | 仕事運 | ALIGNED→ALIGNED |
| career | 2 | 日枝神社(43) | 仕事運 | 仕事運 | ALIGNED→ALIGNED |
| career | 3 | 愛宕神社(46) | 出世運 | 仕事運 | ALIGNED→ALIGNED（GID昇順採用により語が変化、両方ともmatched GID label） |
| money | 1 | 花園神社(61) | 商売繁盛 | 商売繁盛 | ALIGNED→ALIGNED |
| money | 2 | 日枝神社(43) | **仕事運** | 商売繁盛 | **MISALIGNED→ALIGNED** |
| money | 3 | 芝大神宮(45) | **縁結び** | 商売繁盛 | **MISALIGNED→ALIGNED** |
| study | 1-3 | 長太稲荷神社×2/明治神宮 | (goriyaku先頭語 or "ご利益") | ご利益 | GENERIC→GENERIC（Purpose Evidence自体が皆無のため、无理な是正は行っていない） |
| protection | 1 | 明治神宮(1) | **縁結び** | 厄除け | **MISALIGNED→ALIGNED** |
| protection | 2 | 赤坂氷川神社(60) | **縁結び** | 厄除け | **MISALIGNED→ALIGNED** |
| protection | 3 | 靖國神社(58) | 厄除け | 厄除け | ALIGNED→ALIGNED |

参考（Top3圏外、career TEXT_ONLY代表例）: career/靖國神社(58, rank5) — Before Lead="厄除け"(matched evidenceと無関係)、After Lead="勝運"(実際に一致したtext hint)。

## Alignment

- MISALIGNED before = 4（money×2, protection×2）
- MISALIGNED after = **0**
- new MISALIGNED = **0**
- study(GENERIC) 3件は本実装の対象外のまま（Purpose Evidence自体が存在しないため、[[compass-need-lead-purpose-alignment.md]] Phase A9で確認済みのスコープ境界どおり）。副次効果として、Before側で goriyaku非空だった候補（例: study/明治神宮、Before lead="縁結び"）も含め、GENERIC候補は一律で generic fallback "ご利益" へ統一された（matched evidence無しでLeadを推測しないという制約20と整合）。

## Ranking

churn = **0**。5 Purpose全12候補について `score_need` / `_score_total`（score_v3・rank_weighted等の全内訳を含む重み付き総合スコア）/ `matched_need_tags` / Top3の並び順を実DBで実測し、Before（[[compass-need-lead-purpose-alignment.md]]記録値）と完全一致することを確認した。コード経路としても、Lead生成は`_attach_breakdown`（score確定処理）の**後**に呼ばれ、その戻り値は`rec["reason"]`という文字列フィールドにのみ格納され、`_score_total`/`breakdown`のいずれにも書き戻されない（[[compass-need-lead-purpose-alignment.md]] Phase A12で確認済み、今回のdiffは`_attach_breakdown`・Ranking/sort関数のいずれにも触れていない）。

## Score

churn = **0**（上記Rankingの実測に含む。`score_need`/`_score_total`/`matched_need_tags`は5 Purpose×12候補すべてでBefore値と1桁も違わず一致）。

## Query Impact

candidate単位の追加DBクエリ = **0**。`need_gid_label_by_id`はリクエストにつき1回（`concierge_chat.py`内、候補ループの外）、`GoriyakuTag.objects.filter(id__in=...)`（既存ヘルパ`_build_goriyaku_tag_label_by_id`の再利用）のみで取得している。新しいrepository layer・新しいperformance frameworkは作っていない。

## Unit Tests

- `backend/temples/tests/test_need_lead_purpose_alignment.py`（新規、17テスト）: `_build_need_lead`のEvidence Chain（7-1〜7-6相当）、`_resolve_matched_lead_evidence`のGID/text解決とタイブレーク、`build_recommendation_reason`のEvidence配線（GID優先・TEXT_ONLY・no-evidence・generic・後方互換）を全てカバー。
- `backend/temples/tests/test_protection_explanation_coverage.py`（既存、更新）: 新契約下でのgoriyaku-first廃止を反映するよう3件のアサーションを更新（テスト名も新挙動に合わせて変更）。他9件は無変更（goriyaku空ケース・intent_map文言・outcome-guarantee禁止チェックは元々goriyaku非空分岐に依存していないため影響を受けない）。

## Regression

- Focused（新規+更新テスト）: 35 passed, 0 failed
- Compass関連スイート（orchestrator/direction_filter/runtime/api）: 98 passed, 0 failed
- `temples`アプリ full suite: **1686 passed, 15 skipped（既存スキップと同数、内容も同一）, 0 failed**

## Out of Scope

- Text Evidence Scoring（Option A/B/C/D、[[compass-text-evidence-scoring-responsibility.md]]）は未実装のまま。
- `PRIMARY_REASON_PRIORITY`は無変更。
- `NEED_TO_GORIYAKU_IDS`/`NEED_TEXT_WEIGHTS`は無変更（読み取りのみ）。
- Reason Body（`intent_map`/`mapping`の文言）は無変更。
- studyのGENERIC是正（Purpose Evidence自体の欠如）は対象外のまま。

## Next

Text Evidence Scoring Decision（[[compass-text-evidence-scoring-responsibility.md]] / [[compass-protection-text-evidence-overlap.md]]）へ戻る。Lead Purpose Alignmentはこの実装PRのマージをもってCLOSEDとする。Text Scoringの実装は別PRで行う。
