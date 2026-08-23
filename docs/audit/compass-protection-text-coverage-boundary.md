> **Status: Complete. Audit only — `NEED_TEXT_WEIGHTS`を含むProduction Codeは変更していない。**

# Compass Protection Text Coverage Boundary Audit

## 1. Scope

PR #2545（Mapping）・PR #2549（Reason/Lead）反映後の`protection`について、`NEED_TEXT_WEIGHTS["protection"]`を実装する前に、`mental`との意味境界・語彙の重複リスク・実コードのoverlap挙動を監査する。主対象`protection`、副対象`mental`。AUDIT ONLY、`NEED_TEXT_WEIGHTS`を含む実装は一切行っていない。

## 2. Baseline

- 作業開始時点のlocal `develop` HEAD = `origin/develop` HEAD = `43c516bcf8ee4439f2d6e33a340d21b659e3a58c`
- 専用worktree（`../jinja_app-compass-protection-text-boundary`、branch `audit/compass-protection-text-coverage-boundary`）をこのSHAから作成。main working treeは変更していない
- PR #2549のcode（`intent_map["protection"]="厄除けや守り"`、`_build_need_lead`のfallback`"protection": "厄除け"`）がdevelopに存在することをfresh readで確認
- `protection == {11, 32, 2}`確認（drift無し）

## 3. mental Existing Vocabulary（Phase 2）

`NEED_TEXT_WEIGHTS["mental"]`（`concierge_chat_ranking.py` L419-427、fresh read、既存Audit記載と一致・drift無し）:

| Phrase | Weight |
|---|---:|
| 厄除 | 2 |
| 厄払い | 3 |
| 浄化 | 2 |
| 心を整える | 2 |
| 不安 | 2 |
| 落ち着く | 2 |
| 静か | 1 |
| 守護 | 1 |
| 守ってほしい | 1 |

既存監査で指摘された4語（厄除・厄払い・守護・守ってほしい）に加え、**「浄化」も同種の語であることを今回のfresh readで追加確認した**（既存監査は4語のみ言及、5語目としてのdrift）。

**mentalで使われている理由の裏付け**: `mental`のconsultation_axis（`restart_mindset`）のキーワードリスト（`consultation_axis.py` `CONSULTATION_AXIS_KEYWORDS["restart_mindset"]`）を確認したが、「気持ちを切り替えたい」「前向き」「再出発」「リセット」「動き出したい」等であり、**厄除/厄払い/浄化/守護/守ってほしいのいずれとも一致しない**。`mental`のReason intent_map（"不安や心の安定"）とも直接の意味的つながりが薄い。コード上・docs上、これら5語が`mental`に置かれている根拠となる明示的なコメントや設計文書は見つからなかった。

## 4. protection Existing Vocabulary Evidence（Phase 3）

repo内既存資産のみを検索した（新規語彙の作成なし）。

| Phrase | Existing Source | Current Purpose/Responsibility | Candidate Status |
|---|---|---|---|
| 厄, 厄除, 厄払い, 厄を落としたい, 浄化, 邪気, お祓い, お祓いしたい, 清めたい, 災難, 守護, 守って, 守ってほしい, 守られたい, 流れが悪い, 悪い流れ | `consultation_interpreter.py` `NEED_KEYWORDS["protection"]`（**稼働中**、Concierge自由記述query解析で実際に使用） | Concierge query-side意図抽出（Compassは`query=""`のため不使用） | **DIRECT**（同一責務のquery側taxonomyが、これら全語を明確にprotectionへ分類している） |
| 厄, 厄除, 厄払い, 厄を落としたい, 浄化, 邪気, お祓い, お祓いしたい, 清めたい, 災難, 守護, 流れが悪い, 悪い流れ, 守って, 守ってほしい, 守られたい | `need_tags.py` `KEYWORDS["protection"]`（**稼働中**、`extract_need_tags()`経由で`concierge_chat_need.py`から実際に呼ばれる） | 同上（独立した並行実装、同じ結論） | **DIRECT**（2つ目の独立稼働中システムが同じ分類を再確認） |
| 厄(除\|払), 厄を落としたい, 流れが悪い, 悪い流れ, 清めたい, お祓い, 守って, 守られたい（正規表現） | `need_tags.py` `REGEX["protection"]`（**稼働中**、同上の関数から使用） | 同上 | **DIRECT**（表記ゆれ対応の正規表現でも同じ分類） |
| 厄, 厄を落としたい, 清めたい, お祓いしたい, 流れが悪い | `need_tags.py` `NEED_TEXT_HINTS["protection"]`（**未使用・死んだコード**、ファイル内外どこからも参照されていないことをgrep確認済み） | 定義のみ、責務なし | **DIRECT**（方向性としては同じ分類だが、コード自体が非稼働のため証拠としての重みは他3件より弱い） |
| 厄除け（GoriyakuTag実ラベル、id=2） | 隔離local DB、`backfill_goriyaku_tags`由来 | Mapping（`NEED_TO_GORIYAKU_IDS["protection"]`）採用済み | 該当なし（既にmapping層で採用済み） |
| 方除け | `docs/product/history-theme-taxonomy.md` L108のみ | history_theme taxonomyの一覧言及のみ、実装なし | **NO**（実装エビデンスなし） |
| 八方除け, 災難除け, 魔除け | 検索結果0件 | 該当なし | **NO** |
| 守り | 複数箇所（`meaning-translation-mapping.md`、`shrine_meaning_composer.py`のhistory_theme "守り"カテゴリ） | history_theme taxonomyの1カテゴリ、health/family/money等も含む広い概念（既存監査`compass-protection-signal-completion.md`で確認済み、今回再確認） | **NO**（意味範囲がprotectionより広い） |
| 無事, 安全, 祓い, 清め | 主に`shrine_meaning_composer.py`のhistory_theme別copy、または他purpose（travel_safe）に分散 | 個別に異なる責務 | **NO**〜**MOTHER_SHIP_DECISION**（語ごとに判断が割れる） |

**最重要の発見**: `NEED_KEYWORDS`（consultation_interpreter.py）・`KEYWORDS`（need_tags.py）・`REGEX`（need_tags.py）という**3つの独立した、現在も稼働中のコードパス**が、揃って厄除/厄払い/浄化/守護/守ってほしいを**protection専用**として分類している。この3つはいずれも`NEED_TEXT_WEIGHTS["mental"]`とは別のtaxonomyだが、Purpose定義の意味的な「正本」として機能しており、`NEED_TEXT_WEIGHTS["mental"]`の現在の内容と**直接矛盾している**。

## 5. mental / protection Semantic Boundary（Phase 4）

| Dimension | mental | protection |
|---|---|---|
| Purpose label（`NEED_LABELS_JA`） | "不安・心" | "厄除け・守り" |
| need tag定義（`NEED_KEYWORDS`/`KEYWORDS`） | 不安, 落ち込み, ストレス, 自信, 焦り, しんどい, つらい, 辛い, 苦しい, 悩み, 迷い, 考えすぎ, 心を整えたい, 気持ちを切り替えたい, 疲れ, 流れが悪い, 最近うまくいかない | 厄, 厄除, 厄払い, 厄を落としたい, 浄化, 邪気, お祓い, 清めたい, 災難, 守護, 流れが悪い, 悪い流れ, 守って, 守ってほしい, 守られたい |
| consultation_axis接続 | `restart_mindset`（キーワード: 気持ちを切り替えたい/前向き/再出発/リセット/動き出したい） | **なし（"other"へfallback、`compass-protection-signal-completion.md`で確認済み）** |
| `NEED_TEXT_WEIGHTS`（現状） | 厄除/厄払い/浄化/心を整える/不安/落ち着く/静か/守護/守ってほしい（9語） | **未定義（0語）** |
| Reason intent_map | "不安や心の安定" | "厄除けや守り"（PR #2549で追加済み） |
| Lead fallback | "心願成就" | "厄除け"（PR #2549で追加済み） |
| history_themeとの接続 | `resolve_history_theme_candidate_boost`は`consultation_axis`ベース。mentalは`restart_mindset`軸を持つため理論上boost対象になり得る | `consultation_axis="other"`のため、history_theme_candidate_boostは常に発火しない構造（既存監査で確認済み） |

**mental側候補概念**: 不安・気持ちの落ち込み・ストレス・気持ちの切り替え（現行`NEED_KEYWORDS`/consultation_axisと一致）。
**protection側候補概念**: 厄除け・お祓い・浄化・災難除け・守護（現行`NEED_KEYWORDS`/`KEYWORDS`/`REGEX`と一致）。

「流れが悪い」「悪い流れ」のみは、`NEED_KEYWORDS`の時点で**両Purposeに意図的に重複登録されている**（mental: "流れが悪い"のみ、protection: "流れが悪い"+"悪い流れ"）——これは既存taxonomy自身が許容している数少ない共有語であり、他の語（厄除/厄払い/浄化/守護/守ってほしい）とは性質が異なる。

## 6. Vocabulary Classification（Phase 5）

| Phrase | Classification | Evidence |
|---|---|---|
| 厄除 | **PROTECTION_ONLY** | `NEED_KEYWORDS`・`KEYWORDS`・`REGEX`の3つの稼働中コードが揃ってprotectionへ分類。mental側のconsultation_axis（restart_mindset）とは無関係 |
| 厄払い | **PROTECTION_ONLY** | 同上 |
| 浄化 | **PROTECTION_ONLY** | 同上（既存監査が見落としていた5語目、今回追加確認） |
| 守護 | **PROTECTION_ONLY** | 同上 |
| 守ってほしい | **PROTECTION_ONLY** | 同上 |
| 心を整える, 不安, 落ち着く, 静か | **MENTAL_ONLY** | `NEED_KEYWORDS["mental"]`・`restart_mindset`軸と直接一致。protection側のいずれの資産にも出現しない |
| 流れが悪い | **AMBIGUOUS**（既存taxonomy自体が両方に登録済み） | `NEED_KEYWORDS`がmental/protection双方に意図的に含めている稀な例外 |

**重要**: 「守護」「守ってほしい」等が現在`NEED_TEXT_WEIGHTS["mental"]`にあるという事実だけではSHARED_SAFEと判断していない（制約#16の通り）。3つの独立した稼働中コードパスが一貫してprotection側に分類しているという、語の現在地とは反対方向のEvidenceを優先した。**したがって、真にSHARED_SAFEと呼べる語は「流れが悪い」系のみであり、厄除/厄払い/浄化/守護/守ってほしいはPROTECTION_ONLYに分類する。**

`NEED_TEXT_WEIGHTS["mental"]`からこれら5語を削除すべきかは本監査のスコープ外（制約#2で明示的に禁止）であり、`MOTHER_SHIP_DECISION`として記録するのみに留める。

## 7. Scoring Overlap（Phase 6）

`_prefilter_candidates_for_need()`（`concierge_chat_ranking.py` L1556-1645、fresh read）の該当箇所:

```python
for tag in need_tags_clean:
    ...
    text_weights = NEED_TEXT_WEIGHTS.get(tag, {})
    tag_matched_hints = [hint for hint in text_weights.keys() if hint in material]
    if tag_matched_hints:
        score += 1
        matched.append(f"{tag}:text")
        matched_text_hints_by_tag[tag] = tag_matched_hints
        text_score_by_tag[tag] = sum(text_weights[h] for h in tag_matched_hints)
```

確認結果:

1. **1候補がmental/protection双方にhit可能か**: 構造上YES（`need_tags_clean`に両方が含まれれば、同じ`material`文字列に対して両方のtagが独立にチェックされる）。ただし**Compassは`purpose: str`単一引数（`compass_recommendation_orchestrator.py` L176）であり、`docs/product/compass-mvp-runtime-contract.md` L187「purposeは単一のneed_tagスラッグ値とする（MVPは複数選択に対応しない）」により、Compass経由では`need_tags_clean`が常に1要素——mental+protection同時発火は**Compassでは構造的に発生しない**（Phase 8で詳述）
2. **加点は累積するか**: YES。`score`は全tagループを通じた単一変数であり、複数tagがヒットすれば各tagの寄与が単純加算される
3. **同一文字列hitがtagごとに二重加点されるか**: YES（`matched_text_hints_by_tag`・`text_score_by_tag`はtagキーの辞書であり、同じ単語が複数tagの`text_weights`に存在すれば、tagの数だけ独立にカウントされる）。ただしこれはCompass単体では上記1の理由により発生しない
4. **`score_need`への集約**: `score_need`（`_attach_breakdown`側、別関数）は`matched_all`（tagの重複除去リスト）の**件数**であり、単語のヒット数ではない。Compass（1 purpose/call）では`score_need`は常に0か1
5. **rank_weighted/score_v3への伝播**: `score_need_rank_weighted`は`text_score_by_tag`の**値の合計**（重み付き強度）を反映するため、こちらはヒット数・重みに応じて連続的に変化する。**score_needが0/1の二値であるのに対し、rank_weighted/score_v3は強度を反映する**という既存の設計上の役割分担を確認した

**Compass自身の文脈での本当のoverlapリスクは「1回の呼び出し内での二重加点」ではなく、「同じ語彙を複数Purposeの辞書に置いた場合、mental呼び出しとprotection呼び出しの独立した2回の呼び出しで、同一候補が両方にhitしてしまい、Purpose間の差別化が薄れること」である**（Phase 10で詳述）。

## 8. Single-purpose Behavior（Phase 7）

同一fixture（origin=(35.662443, 139.5920237)、direction_context={referenceDirections:["東"]}）で、mental単独呼び出しとprotection単独呼び出しを比較した（read-only、既存パイプラインそのまま実行）。

SET-A（§9）を`unittest.mock.patch.dict`で`NEED_TEXT_WEIGHTS["protection"]`へ一時注入した状態で:

- protection呼び出し: Top3が明治神宮(1)/赤坂氷川神社(60)/靖國神社(58)へ変化（§12 Simulation参照）
- mental呼び出し（同じpatch適用下）: Top3は靖國神社(58)/明治神宮(1)/赤坂氷川神社(60)——**mental自身のNEED_TEXT_WEIGHTS["mental"]エントリは変更していないため、mentalの結果は不変のまま独立して動作する**ことを確認

Purpose選択によってRecommendationが適切に分離されるかという点では、**各呼び出しは自分のtagの辞書のみを参照するため、mentalの語彙定義自体を変更しない限りmentalの挙動には影響しない**——これは確認できた。ただし、同じ候補（明治神宮・赤坂氷川神社）が**mental呼び出しでもprotection呼び出しでも共にTop3へ入っている**（§12実測）——これは「共有語彙により同一候補が両Purposeで浮上する」という差別化低下の直接的な実例である（Phase 10）。

## 9. Multi-purpose Behavior（Phase 8）

**NOT_APPLICABLE（Compassにおいて）**。`compass_recommendation_orchestrator.get_compass_recommendations(purpose: str, ...)`のシグネチャは単一文字列であり、`docs/product/compass-mvp-runtime-contract.md` L187で「purposeは単一のneed_tagスラッグ値とする（MVPは複数選択に対応しない）」と明記されている。したがって、mental+protectionを同時に`need_tags_clean`へ渡すシナリオはCompassの現行Runtime Contract上発生しない。

（参考、スコープ外の観察）: `_prefilter_candidates_for_need`のシグネチャ自体は`need_tags: List[str]`（複数対応）であり、Concierge側の`interpret_consultation`→`build_need_profile`は自由記述query次第で複数need_tagsを抽出し得る構造になっているが、これはCompassとは別の呼び出し経路であり、今回のAudit対象（Compass Protection Text Coverage）の範囲外として深追いしていない。

## 10. Protection Candidate Sets（Phase 9）

| Phrase | Set | Reason |
|---|---|---|
| 厄除 | **SET-A** | 3つの稼働中コードパスでPROTECTION_ONLY、既存weight(2)がmentalに実在（transplant評価用に利用可） |
| 厄払い | **SET-A** | 同上、既存weight(3) |
| 浄化 | **SET-A** | 同上、既存weight(2) |
| 守護 | **SET-A** | 同上、既存weight(1) |
| 守ってほしい | **SET-A** | 同上、既存weight(1) |
| 流れが悪い, 悪い流れ | **SET-B**（CONDITIONAL） | `NEED_KEYWORDS`自体が既にmental/protection双方に登録している既存の共有語——protectionへ追加する場合、mentalとの意図的な共有として扱うか、`NEED_TEXT_WEIGHTS`では敢えて含めないかはProduct判断（`MOTHER_SHIP_DECISION`） |
| 厄, 厄を落としたい, 邪気, お祓い, お祓いしたい, 清めたい, 災難, 守って, 守られたい | **SET-B**（CONDITIONAL） | `NEED_KEYWORDS`/`KEYWORDS`/`REGEX`にはprotection語として存在するが、`NEED_TEXT_WEIGHTS`のいずれのPurposeにも既存weightが無い——**weightをどう決めるかはProduct判断（`INSUFFICIENT_WEIGHT_EVIDENCE`寄り、§12参照）** |
| 方除け, 八方除け, 災難除け, 魔除け | **EXCLUDE** | repo内に実装済みのweight/text hint資産が存在しない。§4の通り"方除け"はtaxonomy一覧言及のみ |
| 守り | **EXCLUDE** | history_theme taxonomyの1カテゴリであり、protectionより意味範囲が広い（health/family/money等を含む）。制約#17により意味を混同しない |

## 11. Purpose Sensitivity Expected Impact（Phase 10）

### Intended improvement

goriyaku_tagを持たないが自由記述goriyakuに厄除け等のprotection意味語を持つ候補を拾えること——理論上は成立するが、§4の分析ではGoriyakuTag backfillと自由記述goriyaku textが強く相関している既存データ（`compass-purpose-signal-coverage.md`で確認済みのパターン）のため、実際にはgid未matchでtext-onlyという候補は稀である可能性が高い。

### Possible risk（§12で実測確認）

**既にgoriyaku_tag matchしている候補へtext scoreが重なり、過剰boostになる。** これは仮説ではなく、§12のsimulationで実際に観測された（`_score_total`が0.60→1.32へ倍増、Top3の1枠が入れ替わった）。原因は「厄除け」がGoriyakuTag（id=2）としても自由記述テキストとしても同時に存在する候補が多いこと——23件のDirection候補中10件（約43%）が自由記述に「厄除」を含んでいた（§12実測）。

### Cross-purpose risk

mental/protection共有語彙（§6でPROTECTION_ONLYと分類したものの、現状mentalにも存在する厄除/厄払い/浄化/守護/守ってほしい）により、同一候補が**mental purpose選択時にもprotection purpose選択時にも**浮上し得る（§8で実測: 明治神宮・赤坂氷川神社が両呼び出しのTop3に共通して出現）。これはPurpose Differentiationの低下と評価できる——ただしこれは今回新規に追加する語による影響ではなく、**既にmental側に存在する語がこの共有を生んでいる**（protection側へ同じ語を追加しても、mentalとの重複状態自体は変わらない。むしろprotection側でも正しく機能するようになる分、両Purposeの対称性は改善する）。

## 12. Simulation（Phase 11）

SET-A（厄除:2, 厄払い:3, 浄化:2, 守護:1, 守ってほしい:1——mentalの既存weightをそのまま転用、新規weight発明なし）を`unittest.mock.patch.dict`で`NEED_TEXT_WEIGHTS["protection"]`へ一時注入し、既存Purpose Sensitivity fixtureをread-only実行した（ファイル変更なし）。

| Metric | Before（現状） | After（SET-A patch） |
|---|---|---|
| Top3 | 明治神宮(1)/乃木神社(59)/赤坂氷川神社(60) | 明治神宮(1)/赤坂氷川神社(60)/**靖國神社(58)** |
| `_score_total`（明治神宮） | 0.6069056032997854 | **1.3269056032997855**（倍増） |
| `_score_total`（赤坂氷川神社） | 0.6018925651942543 | **1.3218925651942544**（倍増） |
| matched（明治神宮） | ["protection:gid"] | ["protection:gid", "**protection:text**"]（"厄除"がhit） |
| 乃木神社の扱い | Top3内（rank2） | **Top3から脱落**（"厄除"を含まないためtext boostを受けられず、他候補に追い抜かれた） |

**candidate count**: Direction=23（不変）、Distance=12（不変、`distance_stage_km`も15で不変——Text Coverage追加はDirection/Distance集合自体には影響しない、既存監査の結論と整合）
**churn**: **Top3構成に実際の変化あり（1/3枠）**。score_needは3件とも1のまま不変（textマッチは`score_need`ではなく`rank_weighted`/`_score_total`へのみ影響、§7の設計確認と整合）

`weight`は§10の通りmentalの既存値をそのまま転用したためINSUFFICIENT_WEIGHT_EVIDENCEには該当しない（SET-Aのみ、SET-Bはweight未定のためsimulation対象外とした）。

## 13. Option Comparison（Phase 12）

| 基準 | Option A（protection専用語彙のみ追加） | Option B（SET-A + protection専用語彙） | Option C（mentalから移動） | Option D（両方再設計） |
|---|---|---|---|---|
| 1. Purpose boundary | 明確（新規語彙はSET-B由来のみ、mentalに触れない） | SET-Aがmentalとの重複を残したまま追加されるため境界がやや曖昧 | 最も明確（重複解消） | 設計次第 |
| 2. Ranking churn | 低〜中（SET-B語彙のweight未定のため影響予測が難しい） | **中〜高**（§12実測、Top3の1/3が変化） | 中（mental側のRankingも変化し得る、regression範囲が広い） | 高（両方変化） |
| 3. Regression risk | 低（mentalに触れない） | 低〜中（mentalは不変だがprotection側churnあり） | **高**（mental既存test・既存Purpose Sensitivity双方のregressionが必要） | 最高 |
| 4. Existing taxonomy整合 | 中（SET-Bはweight根拠が薄い） | **高**（SET-Aは3つの稼働中taxonomyと整合） | 高（重複解消でtaxonomy一貫性は最も高い） | 設計次第 |
| 5. Testability | 高 | 高 | 中（mental側のexisting testも見直しが必要） | 低 |
| 6. Rollback | 高（1辞書エントリ） | 高（同上） | 中（2箇所變更） | 低 |
| 7. Product judgment量 | 高（SET-Bのweight全て未定） | 中（SET-Aはweight既存、残りはSET-B分のみ） | 高（mental側の影響評価も必要） | 最高 |
| 8. 他Purposeへの波及 | なし | なし（mentalの辞書は不変） | **あり**（mental自身のRanking/Reason/Purpose Sensitivityが変化） | あり |

**推奨Option**: **A（またはB、SET-Aのweight根拠が十分に強いと判断されれば）を推奨**。Cは制約#2（mentalの既存語彙を削除・変更しない）に抵触するため今回のスコープでは選択できない。Dは過大。AとBの選択は、SET-Aの「既存weight転用」という設計判断をProductとして受け入れるか（受け入れればB、慎重を期すならAのみでSET-B語彙選定を先に固めるか）に依存し、`MOTHER_SHIP_DECISION`とする。

## 14. Recommended Implementation Scope

- 最小構成: SET-A（厄除/厄払い/浄化/守護/守ってほしい、既存weight転用）のみを`NEED_TEXT_WEIGHTS["protection"]`へ追加
- SET-B（厄・お祓い・清めたい等、weight未定）・「流れが悪い」系（mentalとの意図的共有）は別途Product判断後
- §12で確認した「既存gid matchへのtext boost重複」リスクを実装PRのdescriptionに明記し、Purpose Sensitivity regressionを実装PRでも再実行することを必須とする

## 15. Test Scope（Phase 13、design only）

- protection専用語（SET-A）が実際にhitすることを確認するunit test
- mental専用語（心を整える等）がprotectionへhitしないことを確認するunit test（cross-contamination防止）
- protection専用語（SET-A）がmentalへhitしないことを確認するunit test（逆方向）
- 既存goriyaku_tag matchへのtext boost重複が実際に発生するケースのunit test（§12のパターンを固定化）
- Purpose Sensitivity regression（既存fixtureでのTop3/score_need/churn記録）
- Ranking churn許容範囲の明示（今回は許容する前提のPRになる点を、Explanation-onlyだった前回PR #2549との違いとして明記）
- 他Purpose（love/career/money/study）のNEED_TEXT_WEIGHTS regression（変更していないことの確認）

## 16. Mother Ship Decision Inputs

- SET-Aをそのまま採用するか（mentalの既存weightを転用する設計判断の是非）
- SET-B（厄・お祓い・清めたい等）のweightをどう決めるか、または今回は見送るか
- 「流れが悪い」「悪い流れ」をprotectionへも追加するか（既存`NEED_KEYWORDS`は既に両Purpose共有だが、`NEED_TEXT_WEIGHTS`でも同様の共有にするかは独立した判断）
- §12で観測した「gid+text二重加点によるスコア倍増」を許容するか、それとも別の設計（例: 同一tag内でgidとtextが同時ヒットした場合はtext分を減衰させる等）を検討するか——ただし後者は本監査のスコープを超えるscoring logic変更に該当するため、あくまで論点提示のみ
- `NEED_TEXT_WEIGHTS["mental"]`から厄除/厄払い/浄化/守護/守ってほしいを将来的に削除・整理すべきか（今回は変更しない、別タスク）

## 17. Out of Scope

`NEED_TEXT_WEIGHTS`（実装0件）・`mental`の既存語彙（削除・変更0件）・`NEED_TO_GORIYAKU_IDS`・Reason/Lead（PR #2549で完了済み、今回は変更なし）・Ranking weight・scoring logic・Purpose taxonomy・consultation_axis・DB/Goriyaku master・migration・frontendはいずれも本監査で変更していない（`git diff --stat`で確認）。

## 18. Limitations

- SET-B語彙（厄・お祓い・清めたい等）はweightの根拠となる既存数値が無いため、simulationを実施していない（`INSUFFICIENT_WEIGHT_EVIDENCE`、指示通り無理に行わなかった）
- §12のsimulationは1つの固定fixture（origin/direction）のみで実施した。他のorigin/directionでのchurn度合いは未検証
- Concierge側（Compass以外）でmental+protectionが同時にneed_tagsへ入り得るかどうかの深追いは、今回のAudit対象外として意図的に行っていない（§9）
- `NEED_TEXT_HINTS`（need_tags.py、未使用コード）自体がなぜ作られ、なぜ使われなくなったのかの経緯は本監査では調査していない
