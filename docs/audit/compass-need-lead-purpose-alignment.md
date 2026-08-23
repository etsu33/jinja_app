# Compass Need Lead Purpose Alignment Audit

## 1. Scope

[[compass-reason-evidence-priority.md]]（PR #2555）は、`PRIMARY_REASON_PRIORITY`のtext_hint/goriyaku_tag優先順位が実際のReason/Lead文言に影響を与えないことを確認する一方、**`_build_need_lead`がgoriyakuフィールドの先頭要素をPurpose非依存に採用するため、lead語（「〜のご利益で知られる」の〜部分）がPurposeと無関係になる**という、より実害の大きい問題を新たに発見した（protection群Top3の4件中3件でミスマッチ観測）。本監査はこの`_build_need_lead`のPurpose整合性問題を正式に監査する。監査のみであり、Production Codeは変更しない。実装（Part B）はAudit PRがdevelopへマージされ、母艦が採用方式を確定した後にのみ行う。

## 2. Baseline（Phase A0）

| 項目 | 結果 |
|---|---|
| `git fetch origin` | 実施 |
| local develop SHA | `a90e0db081855ffb6d2947dd5cb2836189a6c089` |
| origin/develop SHA | `a90e0db081855ffb6d2947dd5cb2836189a6c089`（一致） |
| `docs/audit/compass-reason-evidence-priority.md` | develop上に存在確認済み（PR #2555マージ済み） |
| protection Reason/Lead | `NEED_LABELS_JA`/`intent_map`/`_build_need_lead`のprotectionエントリすべて現存確認 |
| working tree | clean（既知の未追跡ファイルのみ） |
| branch/worktree collision | なし |
| 専用worktree | `../jinja_app-compass-lead-alignment-audit`（branch `audit/compass-need-lead-purpose-alignment`） |

STOP条件はいずれも該当せず。

## 3. Lead Input Contract（Phase A2）

`build_recommendation_reason(rec, ...)`（`concierge_chat_ranking.py` L1756-1828）から`_build_need_lead(tag, goriyaku)`（L1831-1850）への実際の呼び出しは、`tag`（=`_primary_reason_label`、Purpose tag名のみ）と`goriyaku`（候補のgoriyaku文字列）の2引数に限定されている。しかし `rec`（呼び出し元が保持するdict）には以下がフレッシュリードで確認された通り既に存在する:

| Input | Available at Lead Build? | Source |
|---|:---:|---|
| candidate goriyaku_tag_ids（生の候補GIDリスト） | ✓ | `rec.get("goriyaku_tag_ids")`（`_attach_breakdown`が`candidate_gid_set`として既に参照、L1099-1104） |
| Purpose別の期待GIDセット | ✓ | `NEED_TO_GORIYAKU_IDS[purpose]`（静的import、追加クエリ不要） |
| matched GID（Purpose∩候補GID） | △（未算出だが算出可能） | 上記2つのAND演算で導出可能。現状`rec`に直接保存されていない |
| matched GID label | ✗（未配線） | `goriyaku_tag_label_by_id`は**ユーザー選択GID検索専用**（`concierge_chat.py` L189/807: `_build_goriyaku_tag_label_by_id(goriyaku_tag_ids)`の引数はCompassでは常に`[]`、Compass経路では常に空dict） |
| matched text hint（実単語） | ✓ | `rec["_prefilter_debug"]["matched_text_hints_by_tag"][purpose]`（`_prefilter_candidates_for_need`が生成、L1588-1609、`row = dict(c)`でコピーされた後も同一オブジェクトとして`_attach_breakdown`/`build_recommendation_reason`まで伝播することを確認済み） |
| breakdown（score内訳） | ✓ | `rec["breakdown"]` |
| reason source（text_hint/goriyaku_tag） | ✓ | `rec["_primary_reason_source"]`（ただしLead生成には未使用、[[compass-reason-evidence-priority.md]] 3節参照） |
| consultation axis | ✓ | `_attach_breakdown`の引数として受領済み |

**重要な発見**: matched GIDのラベル取得に使える既存の`goriyaku_tag_label_by_id`は、Compassの呼び出し経路（`compass_recommendation_orchestrator.py`が`interpret_consultation(..., selected_goriyaku_tag_ids=[])`経由で`goriyaku_tag_ids=[]`を渡す）では**常に空dict**になる別機能（ユーザーGID検索フィルタ）専用のものであり、そのまま流用できない。ただし`NEED_TO_GORIYAKU_IDS[purpose]`は5〜8件程度の小さい固定集合であるため、`GoriyakuTag.objects.filter(id__in=NEED_TO_GORIYAKU_IDS[purpose]).values_list("id","name")`を**リクエストにつき1回**（候補件数に依らず）実行すれば、N+1なしでlabelを取得できる。

## 4. Current Algorithm（Phase A3）

`_build_need_lead`（L1831-1850）を条件分岐までtraceした:

```text
condition: goriyaku（候補のgoriyaku文字列）が非空
→ selected lead source: goriyaku.replace("、","・").replace("，","・").replace("/","・").split("・")[0]
  （Purpose/matched evidenceを一切参照しない、候補が持つgoriyaku表記の先頭要素を機械的に採用）
→ output: 例 "縁結び"（goriyaku="縁結び・厄除け・交通安全"の場合）

condition: goriyakuが空 かつ tagがfallback辞書のキーに存在
  fallback = {study:"学業成就", mental:"心願成就", rest:"心身浄化", love:"良縁成就",
              career:"仕事運", money:"金運", courage:"開運", protection:"厄除け"}
→ selected lead source: fallback[tag]
→ output: 例 tag="protection"なら"厄除け"

condition: goriyakuが空 かつ tagがfallback辞書に存在しない
→ selected lead source: 固定文字列 "ご利益"
→ output: "ご利益"
```

第1分岐（goriyaku非空、実務上ほぼ全候補が該当）が常に優先され、Purpose/matched evidenceに一切依存しない。この分岐が[[compass-reason-evidence-priority.md]] 11-12節で発見したミスマッチの直接原因である。

## 5. Five-Purpose Lead Baseline（Phase A4）

既存fixture（origin=(35.662443, 139.5920237), direction=["東"], targetDate=2026-08-23, distance_stage=15km, 候補12件）を再利用。

| Purpose | Rank | Shrine | Match Evidence | Current Lead |
|---|---:|---|---|---|
| love | 1 | 東京大神宮(44) | GID{1,20}∩text{縁結び,恋愛成就,恋愛} | 縁結び |
| love | 2 | 明治神宮(1) | GID{1}∩text{縁結び} | 縁結び |
| love | 3 | 赤坂氷川神社(60) | GID{1}∩text{縁結び} | 縁結び |
| career | 1 | 乃木神社(59) | GID{12}∩text{勝運,仕事運} | 仕事運 |
| career | 2 | 日枝神社(43) | GID{12,27}∩text{仕事運,出世} | 仕事運 |
| career | 3 | 愛宕神社(46) | GID{12,27}∩text{仕事運,出世} | 出世運 |
| money | 1 | 花園神社(61) | GID{4}∩text{商売繁盛,商売} | 商売繁盛 |
| money | 2 | 日枝神社(43) | GID{4}∩text{商売繁盛,商売} | **仕事運** |
| money | 3 | 芝大神宮(45) | GID{4}∩text{商売繁盛,商売} | **縁結び** |
| study | 1-3 | 長太稲荷神社×2/明治神宮 | Evidenceなし | (fallback、後述) |
| protection | 1 | 明治神宮(1) | GID{2}∩text{厄除} | **縁結び** |
| protection | 2 | 赤坂氷川神社(60) | GID{2}∩text{厄除} | **縁結び** |
| protection | 3 | 靖國神社(58) | GID{2,11}∩text{厄除} | 厄除け |

## 6. Alignment KPI（Phase A5/A6）

分類定義: ALIGNED（LeadがPurpose matchと直接整合＝matched GID labelのいずれかと一致）／RELATED（直接一致ではないが関連性あり）／MISALIGNED（Purposeと意味的に無関係）／GENERIC（Evidenceに基づかないfallback）。

| Purpose | Shrine | Lead | Classification | Evidence |
|---|---|---|---|---|
| love | 東京大神宮 | 縁結び | ALIGNED | matched GID#1"縁結び"と一致 |
| love | 明治神宮 | 縁結び | ALIGNED | 同上 |
| love | 赤坂氷川神社 | 縁結び | ALIGNED | 同上 |
| career | 乃木神社 | 仕事運 | ALIGNED | matched GID#12"仕事運"と一致 |
| career | 日枝神社 | 仕事運 | ALIGNED | 同上 |
| career | 愛宕神社 | 出世運 | ALIGNED | matched GID#27"出世運"と一致（careerの複数matched GIDのうち一つ） |
| money | 花園神社 | 商売繁盛 | ALIGNED | matched GID#4"商売繁盛"と一致 |
| money | 日枝神社 | 仕事運 | **MISALIGNED** | careerドメインの語。moneyのmatched GID#4"商売繁盛"とは無関係 |
| money | 芝大神宮 | 縁結び | **MISALIGNED** | loveドメインの語 |
| study | 長太稲荷神社×2/明治神宮 | (fallback文字列) | GENERIC | Purpose Evidenceなし |
| protection | 明治神宮 | 縁結び | **MISALIGNED** | loveドメインの語。protectionのmatched GID#2"厄除け"とは無関係 |
| protection | 赤坂氷川神社 | 縁結び | **MISALIGNED** | 同上 |
| protection | 靖國神社 | 厄除け | ALIGNED | matched GID#2"厄除け"と一致 |

KPI（全15 slot）:

- ALIGNED_COUNT = 8
- RELATED_COUNT = 0
- MISALIGNED_COUNT = 4
- GENERIC_COUNT = 3
- **LEAD_ALIGNMENT_RATE = 8 / 15 = 0.533**
- **ACCEPTABLE_RATE = (8 + 0) / 15 = 0.533**

Purpose別:

| Purpose | ALIGNED | RELATED | MISALIGNED | GENERIC |
|---|---:|---:|---:|---:|
| love | 3 | 0 | 0 | 0 |
| career | 3 | 0 | 0 | 0 |
| money | 1 | 0 | 2 | 0 |
| study | 0 | 0 | 0 | 3 |
| protection | 2 | 0 | 2 | 0 |

## 7. Matched GID → Lead Feasibility（Phase A7）

| Shrine | Matched GID | Label available? | Safe Lead Candidate? |
|---|---|:---:|:---:|
| 東京大神宮(44) | {1:縁結び, 20:恋愛成就} | ✓（新規バッチクエリで取得） | ✓（複数一致、昇順GID採用で決定的に"縁結び"） |
| 日枝神社(43, career) | {12:仕事運, 27:出世運} | ✓ | ✓（昇順採用で"仕事運"） |
| 愛宕神社(46) | {12:仕事運, 27:出世運} | ✓ | ✓（昇順採用で"仕事運"、現行の"出世運"から変化するが両者ともALIGNED） |
| 花園神社(61) | {4:商売繁盛} | ✓ | ✓ |
| 日枝神社(43, money) | {4:商売繁盛} | ✓ | ✓（現行の誤ったlead"仕事運"を修正） |
| 芝大神宮(45) | {4:商売繁盛} | ✓ | ✓（現行"縁結び"を修正） |
| 明治神宮(1) | {2:厄除け} | ✓ | ✓（現行"縁結び"を修正） |
| 赤坂氷川神社(60) | {2:厄除け} | ✓ | ✓（同上） |
| 靖國神社(58, protection) | {2:厄除け, 11:勝運} | ✓ | ✓（昇順採用で"厄除け"、現行と一致） |

確認結果:

1. **matched GID labelを直接Leadに使えるか**: 使える。9/9のケースで自然な単語として直接使用可能。
2. **label取得に追加DB queryが必要か**: 必要。ただし3節の通り、`NEED_TO_GORIYAKU_IDS[purpose]`（Purposeあたり最大8件程度の固定集合）に対する単一バッチクエリで足り、候補件数に比例しない。
3. **serializer/breakdown上に既に存在するか**: 存在しない。`matched_by_gid`はタグ名のみ保持し、GID id/labelは保持していない（[[compass-reason-evidence-priority.md]] Phase 1相当のfresh readで確認済み、`_attach_breakdown`内の`matched_by_gid`はtag名のリスト）。
4. **ID→labelの再lookupが必要か**: 必要（3節参照、既存`goriyaku_tag_label_by_id`は別スコープのため転用不可）。
5. **N+1 riskがあるか**: なし。Purposeの期待GIDセットは静的・小規模であり、リクエストにつき1回のクエリで全候補分をカバーできる。

**複数GID一致時のタイブレーク**: 東京大神宮(44)・日枝神社(43,46)・靖國神社(58)のように1候補が複数のPurpose-matched GIDを持つ場合がある。本監査では新しいgoriyaku taxonomyを作らない制約の下、**昇順GID idを採用する**という単純な決定的ルールを用いた（「どのGIDがより中心的か」という新しい優先度概念は導入しない）。この規則は観測した4例すべてで自然な結果を生んだが、DjangoのQuerySetは明示的な`order_by`なしでは順序を保証しないため、実装時は`sorted()`等による明示的な決定性の担保が必須である（非決定的な実装は同一候補でもリクエストごとにlead語が変わりうるため、STOP条件17「unrelated変更」には該当しないが品質上の要注意点として記録する）。

## 8. Matched Text → Lead Feasibility（Phase A8）

| 候補 | Purpose | matched phrase | 分類 |
|---|---|---|---|
| 靖國神社(58) | career（TEXT_ONLY） | 勝運 | **DIRECT**（単一語、そのまま自然に使用可能） |
| 東京大神宮(44) | love | 縁結び, 恋愛成就, 恋愛（複数一致） | NEEDS_NORMALIZATION（複数語のうちweight最大"縁結び"を採用する規則が必要） |
| 花園神社(61)/日枝神社(43)/芝大神宮(45) | money | 商売繁盛, 商売（複数一致、部分文字列関係） | NEEDS_NORMALIZATION（同上、weight最大"商売繁盛"を採用） |
| 乃木神社(59) | career | 勝運, 仕事運（複数一致） | NEEDS_NORMALIZATION |
| 日枝神社(43)/愛宕神社(46) | career | 仕事運, 出世（複数一致） | NEEDS_NORMALIZATION |

確認結果:

- **matched phraseをLeadへそのまま使えるか**: 単一一致の場合（career id=58の"勝運"）は使える。複数一致の場合は選定規則が必要。
- **substringなので不自然にならないか**: 観測した範囲（"商売"⊂"商売繁盛"等）では、weight最大の語（＝より具体的で長い語であることが多い）を採用すれば不自然にならない。
- **原文語彙として安全か**: `NEED_TEXT_WEIGHTS`の全語彙は、GoriyakuTagのlabelやgoriyakuフィールドの表記と重複する自然な日本語の御利益語であり、新規語彙の発明は不要。NOT_SAFEに分類される候補は観測されなかった。
- **weight語彙とユーザー可視語彙を同一視してよいか**: 本監査で観測した範囲では問題ない（[[compass-text-evidence-scoring-responsibility.md]] Phase 6の「Text一致語はgoriyakuフィールドの表記そのもの」という発見と整合）。

新しいnormalization logic（意味解析等）は不要で、「matched hint群のうちweightが最大のものを採用する」という**既存の`NEED_TEXT_WEIGHTS`の数値をそのまま使う軽量な選定規則**のみで足りることを確認した。

## 9. Purpose Fallback Feasibility（Phase A9）

`_build_need_lead`の既存fallback辞書（L1838-1849: study/mental/rest/love/career/money/courage/protection）はそのまま再利用可能であり、新規copyの発明は不要である。

**重要な境界条件**: study×3（GENERIC分類）は、`_build_need_lead`自体を修正しても救済されない。[[compass-reason-evidence-priority.md]] 3節で確認した通り、Purpose Evidenceが皆無の候補では`build_recommendation_reason`内の`primary_label`が`_resolve_primary_reason`のデフォルト値である**文字列"fallback"**になり（Purpose tag名の"study"にはならない）、`_build_need_lead("fallback", goriyaku)`が呼ばれる。`"fallback"`は`_build_need_lead`のfallback辞書のキーに存在しないため、常に`"ご利益"`（意味のない汎用語）になる。**これは`_build_need_lead`単体の入力（tag, goriyaku）を正しく設計しても解消できず、呼び出し元`build_recommendation_reason`が「Evidenceがない場合は要求されたPurpose自体（例: "study"）をtagとして渡す」よう調整しない限り解消しない。** この調整はReason Body（`intent_map`/`mapping`辞書の文言）自体は変更しない（tagとして"fallback"の代わりに実際のPurpose名を渡すだけで、辞書自体はどちらも既存のまま）。

## 10. Lead Strategy Options（Phase A10）

| Option | Purpose Alignment | Evidence Fidelity | Complexity | DB Risk | UX |
|---|---|---|---|---|---|
| A（現行, First Goriyaku） | 低（53.3%、4件のMISALIGNED観測） | 低（候補が持つ任意のgoriyaku表記、matched evidenceと無関係） | 最低（変更なし） | なし | 「なぜこの理由が出てくるのか」がPurposeと矛盾する場合がある |
| B（Matched GID First） | 高（本監査サンプルではMISALIGNED 4/4を解消） | 高（構造化されたPurpose-matched GIDそのもの） | 低〜中（1リクエストにつき1バッチクエリ追加、複数GID時のタイブレーク規則が必要） | なし（N+1なし、7節） | GID一致がない候補（TEXT_ONLYやGENERIC）はPurpose fallbackへ落ちる |
| C（Matched GID → Matched Text → Purpose Fallback） | 高（Bと同等＋TEXT_ONLY候補もカバー） | 最高（利用可能な最も具体的なEvidenceを常に使用） | 中（Bの構成に加え、複数text hit時のweight最大選定規則が必要、8節） | なし | 最も網羅的。career id=58のようなTEXT_ONLY候補にも意味のあるlead（"勝運"）を提供できる |
| D（Purpose Fallback Only） | 中（fallback辞書の質に依存、既存辞書は8 Purpose中8件が概ね妥当） | 低（候補固有の情報を一切使わない） | 最低 | なし | 候補ごとの個性が失われる（全候補が同じlead語になる） |

## 11. Read-only Lead Simulation（Phase A11）

| Purpose | Shrine | Current(A) | B | C | D |
|---|---|---|---|---|---|
| love | 東京大神宮(44) | 縁結び | 縁結び | 縁結び | 良縁成就 |
| love | 明治神宮(1) | 縁結び | 縁結び | 縁結び | 良縁成就 |
| love | 赤坂氷川神社(60) | 縁結び | 縁結び | 縁結び | 良縁成就 |
| career | 乃木神社(59) | 仕事運 | 仕事運 | 仕事運 | 仕事運 |
| career | 日枝神社(43) | 仕事運 | 仕事運 | 仕事運 | 仕事運 |
| career | 愛宕神社(46) | 出世運 | 仕事運 | 仕事運 | 仕事運 |
| money | 花園神社(61) | 商売繁盛 | 商売繁盛 | 商売繁盛 | 金運 |
| money | 日枝神社(43) | **仕事運** | 商売繁盛 | 商売繁盛 | 金運 |
| money | 芝大神宮(45) | **縁結び** | 商売繁盛 | 商売繁盛 | 金運 |
| protection | 明治神宮(1) | **縁結び** | 厄除け | 厄除け | 厄除け |
| protection | 赤坂氷川神社(60) | **縁結び** | 厄除け | 厄除け | 厄除け |
| protection | 靖國神社(58) | 厄除け | 厄除け | 厄除け | 厄除け |
| career | 靖國神社(58, rank5, TEXT_ONLY, Top3圏外) | 厄除け | 仕事運 | **勝運** | 仕事運 |

太字は現行(A)がMISALIGNEDだったケース。**Option B/CはTop3内の4件のMISALIGNEDを全てALIGNEDへ修正し、新たなMISALIGNEDは0件観測された。** career id=58（Top3圏外だがTEXT_ONLYの代表例）では、Option BはPurpose fallback（"仕事運"）に留まるのに対し、Option Cは実際の一致語（"勝運"）を使える点でCがBより情報量が多い。

## 12. Ranking Non-Impact（Phase A12）

[[compass-reason-evidence-priority.md]] Phase 13の確認をLeadについても再確認した。`_build_need_lead`/`_build_need_reason_text`は`build_recommendation_reason(rec, ...)`から呼ばれ、`concierge_chat.py` L215-224の通り**`_attach_breakdown`（scoreの確定）の後**に実行される。`rec["reason"] = build_recommendation_reason(...)`の戻り値は文字列であり、`rec["_score_total"]`・`rec["breakdown"]`のいずれにも書き戻されない。Compassのソート（`_sort_chat_recommendations`の非distance-tier分岐、[[compass-reason-evidence-priority.md]] 14節で確認済み）は`resolve_score_sort_key`・`distance_m`・`name`のみを参照し、`reason`/`_primary_reason_label`/`_build_need_lead`の出力を一切参照しない。したがって、Lead生成ロジックの変更は candidate filtering / score_need / rank_weighted / score_v3 / total score / sorting のいずれにも影響しない。

## 13. Reason Responsibility Boundary（Phase A13）

- **Lead**（`_build_need_lead`）: 「何のご利益/意味を冒頭に置くか」＝`f"{lead}のご利益で知られる{name}は、..."`の`{lead}`部分。
- **Reason Body**（`_build_need_reason_text`の`intent_map`/`mapping`辞書）: 「なぜこのPurposeに向いているか」＝`{user_intent}を願う参拝先として適しています。`の`{user_intent}`部分、およびgoriyaku空時の文全体。

本監査で確定したOption B/Cはいずれも`_build_need_lead`の内部ロジック（第1分岐の入力ソース切り替え）のみで完結し、`intent_map`/`mapping`辞書（Reason Body）は一切変更する必要がない。すでに9節で述べた「study等のGENERIC是正にはbuild_recommendation_reasonの`primary_label`解決を調整する必要がある」という点も、Reason Body自体（辞書の文言）ではなく、Lead/Reason生成に渡す**tag値**の解決ロジックの話であり、Reason Body変更には該当しない。**原則「Reason Body変更なし」を維持したままLeadのPurpose整合性を改善できる。**

## 14. Recommendation（Phase A14）

**推奨ラベル: `USE_MATCHED_EVIDENCE_CHAIN`（Option C）**

理由:

1. 10-11節の通り、Option B/Cはいずれも本監査サンプルの全MISALIGNED（4/4）を解消し、新規MISALIGNEDは0件だった。
2. Option Cは、Option Bではカバーできないcareer TEXT_ONLY候補（靖國神社/勝運）についても、Purpose fallbackという情報量の少ない語ではなく、実際に一致した具体的な語（勝運）を提示できる点で優れる。
3. 追加コストはOption Bと比較してわずか（8節で確認した通り、既存`NEED_TEXT_WEIGHTS`の値を用いた軽量な選定規則のみで足り、新しいnormalization logicは不要）。
4. リスク（DB N+1、Ranking影響）はOption B/Cともにゼロ（7節・12節）。

次点として、実装コストを最小に抑えたい場合は**`USE_MATCHED_GID_FIRST`（Option B）**も妥当な選択である（TEXT_ONLY候補のカバレッジを諦める代わりに、Text hint選定規則の実装が不要になる）。最終的な採用方式は母艦が確定する。

## 15. Implementation Scope（Phase A15相当、Part B予告）

Audit確定後の実装スコープ候補（Part Bで扱う、本監査では未実装）:

- `_build_need_lead`の第1分岐（goriyaku先頭要素採用）を、matched GID label（新規バッチクエリ、7節）→ matched text hint（既存`_prefilter_debug`、8節、Option C採用時のみ）→ 既存goriyaku先頭要素 → 既存Purpose fallback、の優先順位へ変更。
- `build_recommendation_reason`の呼び出し元（`concierge_chat.py` L189/223）から`matched_gids`/`matched_text_hints`相当の情報を`_build_need_lead`（または中間の`_build_need_reason_text`）へ渡すための、必要最小限の引数追加。
- （任意、9節）study等のGENERIC是正のため、`build_recommendation_reason`の`primary_label`が`"fallback"`の場合に実際のPurpose tagへフォールバックする調整。ただし本監査タスクの主眼（matched evidence時のMISALIGNED解消）とは独立した副次的改善であり、Part Bで別スコープとして扱うか、Mother Shipの判断を仰ぐ。
- Ranking/Scoring/Mapping/Text Weights/Reason Priority/Reason Bodyへの変更は一切含まない。

## 16. Mother Ship Decision Inputs

- 現行LEAD_ALIGNMENT_RATE=53.3%、うちMISALIGNEDは4件（money×2, protection×2）、全てOption B/Cで解消可能。
- Option CはOption Bの上位互換に近い（追加コストが小さく、TEXT_ONLY候補もカバーする）。
- 9節で発見したstudyのGENERIC是正は、`_build_need_lead`単体では解決できず、`build_recommendation_reason`の`primary_label`解決ロジックにも触れる必要がある。これをPart Bのスコープに含めるかは母艦判断が必要（本監査のPart A範囲外の追加変更となるため）。
- 複数GID一致時のタイブレーク規則（7節、昇順GID id採用）は、新しいgoriyaku taxonomyを作らない制約下での実用的な選択だが、母艦が別の基準を望む場合は再検討が必要。

## 17. Limitations

- studyはfixture内でPurpose Evidenceが一切マッチしないため、Option B/Cの効果を実データで検証できなかった（GENERIC是正は9節の通りスコープ境界の問題であり、Option自体の当否とは別軸）。
- 「同一候補が複数のPurpose-matched GIDを持つ場合の最適な選び方」は、昇順GID id採用という単純な規則で観測範囲内は良好だったが、全DBを通じた悉皆検証は行っていない（fixture内9候補のみ）。
- Text hint選定規則（weight最大採用）も同様にfixture内の観測（5候補）に基づく。
- 「ALIGNED/MISALIGNED」の判定は、matched GIDのlabelとlead語の文字列一致（またはドメインの明白な近さ）による人手判定であり、厳密な意味論的分類ロジックによるものではない。

## 18. STOP

本ドキュメント作成後、Draft PRを作成しSTOPする。Part B（実装）は、本Audit PRがdevelopへマージされ、母艦が採用Option（B/C/D等）を確定した後にのみ着手する。
