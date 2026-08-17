> **Status: Audit — 時点記録**
>
> 本ドキュメントは、Concierge・Compat Mode・Direction/Kyusei・Recommendation・Shrine Knowledge・Premium Experienceに関する既存の稼働中契約を突き合わせ、既存の「吉方位はDirection Audit完了まで前面化しない」ゲートが、完了済みのCompass監査シリーズによって充足されたと見なせるかを判定した時点記録である。コード・Model・Migration・Serializer・Ranking・Concierge挙動・Premium UI・Analyticsの変更は一切含まない。既存正本文書の文言も変更しない。
>
> 前提となる監査（本書はこれらの結論を再利用しつつ、新規に発見した契約と突き合わせて検証した）:
> - `docs/audit/premium-visit-compass-recommendation-feasibility.md`（分類B、技術的Capability検証）
> - `docs/audit/premium-visit-compass-time-model-contract.md`（Primary Time Model: MONTH、時間粒度検証）
> - `docs/audit/concierge-compass-meaning-action-authority-boundary.md`（分類B、Authority/Meaning-Action境界検証）

# Compass Contract Reconciliation — Direction Audit Completion監査

## 1. Executive Summary

**結論（先出し）: Direction Audit Status = DIRECTION AUDIT COMPLETE WITH CONTRACT CLARIFICATION。Final Classification = CLEAR WITH CONTRACT FOLLOW-UP。**

本監査は、「Direction Audit」という語を含む契約文書を全リポジトリから再検索し、**前回3監査では未発見だった2つ目の独立したゲート**を新たに発見した。

1. `docs/product/concierge-first-final-spec.md:29`（**Status: Active**）— 「吉方位はDirection Audit完了まで前面化しない」というUI前面化に関するゲート。
2. `docs/analytics/recommendation-score-v2-foundation.md:41,242`（**Status: Reference**）— 「吉方位はDirection Audit完了までスコア本体に入れない」というScore本体組み込みに関する別ゲート。

この2つを同一のゲートとして扱わず、個別に追跡した結果、以下が判明した（FACT）:

- ゲート2（Score本体組み込み）は、それを含む文書自体がReference（歴史的設計資料）であり、かつ自らを「現行のスコア式・重みは`docs/analytics/recommendation-score-v2-current-design.md`を正本とする」と明記している。その**Active**な後継文書`recommendation-score-v2-current-design.md`を直接確認したところ、`direction_signal`が既に`score_total_ranked`の一部として明記され（`:41,67`）、かつ「element / birthdate / direction は主理由を上書きしない」という保護原則も既に明記されている（`:217`）。つまりこのゲートは、正式な「Direction Audit完了」宣言文書こそ存在しないものの、**現行のActiveな契約が既にこの領域を安全側のガードレール付きで通過済みであるという事実によって、実質的に無効化（superseded）されている**。
- ゲート1（UI前面化）は現在もActiveであり、かつ現行実装・現行UI契約（`compat-mode-ui-flow.md`）はこれを遵守している（方位はHome Heroに表示されず、独立した補助カードとしてのみ表示される）。このゲートが本来問おうとしていた懸念——「技術的能力」「時間的精度の誠実性」「Authority境界の明確さ」——は、完了済みの3監査によって具体的な証拠付きで検証済みである。

両ゲートとも**明示的な完了基準（チェックリストや承認プロセス）を定義していない**（FACT、Section 3で確認）。したがって本監査は、ゲートの文言そのものを変更せず（指示通り）、ゲートが示す**懸念**が現時点でどこまで技術的・契約的に解消されているかを判定するに留める。結論として、Compassという別Productにおいて方位を前面化すること自体は正当化できるだけの監査的裏付けが揃ったが、これは**「Concierge自体の前面化禁止を解除する」という意味ではなく**、「Concierge以外の場所（Compass）でなら前面化してよい」という**製品境界の確定**として解釈すべきである（Section 4）。ゲート文言の正式な更新・クローズは、本監査の範囲外の製品判断として残す。

## 2. Scope / Non-Goals

**対象**: Direction Audit完了ゲートの契約源泉の特定、完了基準の有無、完了済みCompass監査群との突き合わせ、Concierge境界の再確認、Compat Mode境界の再確認、Compass Product Promiseの再検証、Meaning/Action契約の正式化、Authority Matrixの確定版作成、時間/コピー契約の再確認、Premium整合性の再確認、西洋占星術スコープの判定、Taxonomy/Health不整合の分類、`target_date`命名の最終判定。

**対象外（今回変更しない）**: 本番Frontend/Backendコード、Concierge挙動、Recommendationスコアリング・Weight、DB Model、Migration、Serializer、Analytics、Compass実装、既存正本文書の文言そのもの（`concierge-first-final-spec.md`等のゲート文言は変更しない）。

## 3. Active Contract Inventory

`grep`によりリポジトリ全体から「Direction Audit」を含む文書を再走査した結果（FACT）:

| 文書 | Status | ゲートの対象 | 完全一致行 |
|---|---|---|---|
| `docs/product/concierge-first-final-spec.md` | **Active** | UI前面化（Concierge画面での方位/吉方位の表示優先度） | `:29,42,109,141` |
| `docs/analytics/recommendation-score-v2-foundation.md` | **Reference**（歴史的設計資料、自ら`v2-current-design.md`を正本と明記） | Score v2本体への組み込み | `:41,242` |

**両ゲートに共通する事実**: いずれも「Direction Audit完了まで」という条件節のみを持ち、**何が完了とみなされるかの明示的な基準（チェックリスト、承認者、成果物の指定）を一切定義していない**（FACT、両文書を全文確認済み）。したがって「Direction Audit」という固有名詞は、当時の執筆者が想定した何らかの検証作業を指す**未定義の将来ゲート**として置かれたものであり、本リポジトリ内に「Direction Audit」という名前の専用手続き文書は存在しない。

**関連する周辺契約（Direction Audit本体ではないが、方位の扱いを規定する既存Active契約）**:

- `docs/core/direction-response-contract.md`（Active）— 方位レスポンスの表示契約
- `docs/product/direction-ranking-design.md`（Active、ヘッダに「正確な計算と加点の正本は`backend/temples/domain/kyusei.py`」と明記）— Ranking契約
- `docs/product/compat-mode-ui-flow.md`（Reference）— UI表示責務
- `docs/ops/direction-fail-safe.md`（Status未確認だが運用契約として機能、前回時間モデル監査で確認済み）— 縮退契約
- `docs/analytics/recommendation-score-v2-current-design.md`（**Active**）— 現行Score本体の正本、`direction_signal`を明記

## 4. Direction Audit Gate

### 4-1. ゲート1（UI前面化、Active）の検証

**現在禁止されている挙動（FACT、`concierge-first-final-spec.md:29,109,141`）**: 吉方位表示の前面化。具体的には、HomeHeroまたはConciergeEntryの主要UIに、誕生日入力・相性・吉方位情報を配置すること（同ドキュメントの「担当しないもの」節、および`compat-mode-ui-flow.md`の「Home Heroでの表示」節と一致）。

**完了済み3監査との突き合わせ**:

| 懸念領域 | 対応する監査 | カバー状況 |
|---|---|---|
| 技術的方位計算能力（bearing/kyusei年盤月盤の実装有無・精度） | Feasibility Audit（`premium-visit-compass-recommendation-feasibility.md` Section 5-6） | **カバー済み**。bearing/kyusei年盤月盤が本番稼働中であること、日盤が未実装であることをコード直読で確認 |
| 時間的精度・日次vs月次の誤解リスク | Time Model Audit（`premium-visit-compass-time-model-contract.md` Section 4-7,14） | **カバー済み**。`visit_date`の日の値が節気月境界を跨がない限り出力に影響しないことを独立検証し、「今日の吉方位」をMISLEADINGと分類 |
| Authority境界・製品責務の明確さ（方位が神社の主理由や神社自体の性質にならないことの保証） | Meaning/Action Boundary Audit（`concierge-compass-meaning-action-authority-boundary.md` Section 7-9） | **カバー済み**。Authority Matrixにより「なぜこの方向」と「なぜこの神社」を分離し、Compass Runtime Authorityが単独で「なぜこの神社がこのユーザーに合うか」を主張できないことを確定 |

**未カバーの懸念**: 上記3領域を横断する形で「Direction Audit」という語が指し示していた可能性のある懸念のうち、本監査シリーズが明示的に扱っていない項目は見当たらない（技術・時間・Authorityの3軸は、方位を製品の前面に出す際に一般的に問われるべき論点を網羅していると判断する）。ただし、これは**INFERENCE**であり、当時のゲート設置者が具体的に何を「Direction Audit」として想定していたかの一次資料（Issue、PR議論等）は本リポジトリのdocs配下からは発見できなかった。

**ゲートは今、満たされたと見なせるか**: 条件付きYES。技術・時間・Authorityの3軸についての懸念は、コード直読を伴う3件の独立監査によって具体的な証拠付きで解消されている。ただし、ゲートの文言自体（「前面化しない」という制約）は`concierge-first-final-spec.md`というActiveな正本文書に残ったままであり、本監査はこの文言を変更する権限を持たない（指示により変更禁止）。したがって「ゲートの背後にある懸念は解消されたが、ゲートの文言のクローズは別途製品判断が必要」という状態を正確に表す**DIRECTION AUDIT COMPLETE WITH CONTRACT CLARIFICATION**をSection 4の結論とする。

### 4-2. ゲート2（Score本体組み込み、Reference）の検証

**発見の経緯**: 本監査で新たに`recommendation-score-v2-foundation.md`を発見した。同文書は「吉方位はDirection Audit完了までスコア本体に入れない」（`:41`）「現在地・方角・吉方位は Direction Audit 完了まで Recommendation Score v2 本体に入れない」（`:242`）と明記する。

**このゲートは現在も有効か**: **実質的に無効化されている（superseded）と判断する**。根拠（FACT）:

1. `recommendation-score-v2-foundation.md`自身のヘッダが「Status: Reference」であり、「現行のスコア式・重みは`docs/analytics/recommendation-score-v2-current-design.md`を正本とする」と明記している。
2. `recommendation-score-v2-current-design.md`（**Status: Active**）を直接確認したところ、`direction_signal`は既に`score_total_ranked = score_total_ranked_base + capped_behavior_contribution + profile_signal + direction_signal`という現行の正本の計算式に明記されている（`:41,67`）。
3. 同じくActive文書内に「element / birthdate / direction は主理由を上書きしない」という明示的なガードレールが既に記載されている（`:217`）。
4. この内容は、前回3監査がコード直読で確認した実装（`concierge_chat_ranking.py`の`direction_signal_score`、最大+0.02、`score_total_ranked`にのみ算入、`score_total`には非算入）と完全に一致する。

つまり、「Direction Audit完了までスコア本体に入れない」という制約は、**それを書いたFoundation文書自身が後にActiveな後継文書によって置き換えられ、かつその後継文書では既に方位がスコア本体に安全なガードレール付きで組み込まれている**という経緯を辿っている。正式な「Direction Audit完了」という宣言文書こそ存在しないが、後継のActive契約が既にこの領域を安全に通過済みであるという事実が、実務上このゲートを無効化している。

**この扱いに伴う留保**: 本監査は`recommendation-score-v2-foundation.md`の文言を変更しない。この文書が今後も「Reference」として保持され、かつ後継のActive文書と矛盾する記述を含んだままである状態は、Compassとは無関係な既存のドキュメント衛生上の課題として、Section 14に記録する。

**両ゲートを同一視しない**: 本監査は、ゲート1（Active、UI前面化）とゲート2（Reference、Score本体組み込み）を意図的に区別して扱った。ゲート1は今もConciergeの表示契約として現役であり、ゲート2は既に別のActive契約に実務上置き換えられている。これらを一つの「Direction Audit」として混同すると、ゲート1のUI前面化制約まで「もう関係ない」と誤解するリスクがあるため、明確に分離して記録する。

## 5. Concierge Boundary

- **Conciergeは相談主導のままか**: YES（FACT）。`docs/product/concierge-modes.md:29`「Need Mode を推薦の主軸とする」、`concierge-first-final-spec.md:21-23`のMVP主導線定義は変更されていない。本監査はこれらの文言を変更しない。
- **Concierge内で方位は補助のままか**: YES（FACT）。`compat-mode-ui-flow.md`の「担当しないもの」節（相談テーマの決定、need_tagsの主判定、推薦理由の主文脈、推薦順位の単独決定を含まない）は現状のまま。
- **Direction Audit完了は自動的にConcierge挙動を変えるか**: **NO**。Section 4-1で確認した通り、本監査シリーズが解消したのは「方位を前面に出す製品を作ってよいか」という懸念であり、「Concierge自体の表示ルールを変えてよいか」という懸念ではない。この2つは別の問いである。
- **ゲートのクリアがConcierge内での方位前面化を自動的に許可しないことの確認**: **確認する**。Concierge内での方位表示ルールは、`concierge-first-final-spec.md`のMVP原則・`compat-mode-ui-flow.md`のHome Hero除外リストという、Direction Audit gateとは別個の、独立して存続するActive契約によって規定されている。これらは本監査の対象外であり、変更を提案しない。
- **方位の前面化はCompassという別Featureの内部でのみ許可されるか**: **YES、本監査が推奨する境界**。Section 4-1の3軸検証はCompassという別製品を前提に行われたものであり、Concierge自体を方位主導の体験に変えることを正当化する証拠ではない。
- **Concierge補助方位とCompass主方位の正確な境界**:

```text
Concierge（変更なし）:
  方位は「補助カード」としてのみ表示（compat-mode-ui-flow.mdの既存ルール）
  スコアへの寄与は最大+0.02（既存、前回監査で確認済み）
  Home Hero・Concierge Entryには一切表示しない

Compass（提案、未実装）:
  方位（+ kyusei月次シグナル）が候補生成の起点そのものになる
  Compass専用画面でのみ前面表示される
  Conciergeの画面・入口には一切影響しない
```

## 6. Compat Mode Boundary

**FACT（`docs/product/compat-mode-ui-flow.md`再読、本監査で再確認）**: Compat Modeが使用する信号は、誕生日・`element4`（西洋占星術由来の4元素）・相性情報・占術由来の補助シグナル・方位に関する補助情報（`:47-54`）。

**Compat ModeがNeed Modeを置き換えてはならないことの確認**: YES（FACT、`concierge-modes.md:48`「Need Mode を置き換えない」、`compat-mode-ui-flow.md:17`「推薦の主導線はNeed Modeとし、Compat Modeは相談テーマや自由入力を上書きしない」）。

**Compat Modeが単独で神社候補を決定してはならないことの確認**: YES（FACT、`compat-mode-ui-flow.md:38`「Compat Modeだけで推薦候補を決定しない」「占術情報のみで推薦を決定しない」）。

**なぜCompassは単に「Compat Modeを主導線化したもの」ではないのか**:

Compat Modeという**計算モジュール群**（`domain/kyusei.py`・`domain/astrology.py`・`direction_reference.py`）と、Compat Modeという**製品責務**（「Concierge内で、Need Modeを補助する立場に限定される」という契約上の役割）は別物である。Compassが再利用するのは前者（計算モジュール）のみであり、後者（製品責務）は再利用しない。もしCompassが後者まで引き継ぐと、「Compat Modeを主導線化することの禁止」という既存契約に矛盾したままの状態を、別の画面名で継続することになる。

**Signal Reuse と Authority Reuse の建築的な違い（本監査の中心的定義）**:

```text
Signal Reuse（計算結果の再利用）:
  kyusei.py の annual_lucky_directions() / planned_visit_lucky_directions()
  direction_reference.py の _bearing() / build_direction_reference()
  astrology.py の sun_sign_and_element()
  → これらは「どんな計算をするか」を定義する純粋関数であり、
    どの製品がいつ呼び出すかに関して製品的な意味を持たない

Authority Reuse（製品責務・意思決定権の再利用）:
  「この信号は誰の許可でこの信号を主要な意思決定根拠にできるか」
  Compat Mode Authority = Concierge内でのみ有効、かつ常に補助限定
  Compass Runtime Authority = Compassという別Product内でのみ有効、かつ主要な起点になってよい
  → これは製品契約上の「誰が」「どこまで」意思決定してよいかの権限であり、
    計算モジュールの実装とは独立して定義される
```

**CompassはCompat Modeの製品責務を継承せずに計算モジュールを再利用できるか**: **YES、これが本監査の推奨する設計**。前回Feasibility監査Section 6・10で確認した通り、`kyusei.py`・`direction_reference.py`・`astrology.py`はいずれも呼び出し元（Concierge/Compat Mode）に対する依存を持たない純粋関数群であり、Compassが新規オーケストレーション層から独立に呼び出すことに技術的障害はない。Compat Modeの製品責務（「Need Modeを置き換えない」）はConciergeという製品の内部規約であり、Compassという別Productには当てはまらない——ただしCompassにはCompass自身の新しいAuthority定義（Section 8）が適用される。

## 7. Compass Promise

タスク提示の2つのコピーを、Section 4-6で確立した境界に照らして最終検証する（前回Meaning/Action Boundary監査Section 11の結論を踏襲・再確認）。

**Concierge: 「今の悩みや願いをもとに、あなたと接点のある神社を見つけます。」**
- 既存契約との整合: **確認済み**。`meaning-layer.md`の非断定原則、`concierge-first-final-spec.md`のMVP主導線定義と一致。

**Compass: 「今月の流れと目的から、向かう方向と参拝候補を見つけます。」**
- 実装済み月次粒度との整合: **確認済み**（Time Model Audit Section 14で「今月の流れ」= SUPPORTED BY CURRENT SIGNAL）。
- 日次精度を含意しないことの確認: **確認済み**。「今月」という語が明示的に月粒度を示しており、「今日」を含まない。
- 結果保証を含意しないことの確認: **確認済み**。「見つけます」の対象が「方向」「候補」という探索的名詞であり、断定的な結果（「叶います」「上がります」等）を含まない。
- 方位だけで神社が決まると誤解させないことの確認: **確認済み**。「目的」（purpose）が並記されており、方向だけでなくpurposeも神社選定に関与することが文面上示されている（Section 8のAuthority Matrixとも整合: 神社選定はRecommendation Authority + Shrine Knowledge Authorityの合成であり、Compass Runtime Authority単独ではない）。
- 最小限の文言修正提案: 前回監査と同様、必須ではないが、詳細画面・カード内で「参考情報です」という既存共通パターン（Section 9の「参考方位」分類）を併記することを推奨する。

## 8. Meaning / Action Contract

**Meaningの操作的定義**: 「なぜこの神社が今の状況とつながるのか」「この神社のどの側面が関連するのか」「その説明を支える根拠は何か」に答える責務。担当: Recommendation Reason（`build_recommendation_reason_v4`）。

**Actionの操作的定義**: 「この期間、どちらへ向かうことを考えてよいか」「その方向にどんな神社候補があるか」「どの候補が現実的な参拝オプションになるか」に答える責務。担当: Compass Runtime Authority由来の方向コンテキスト + 候補生成（新規、未実装）。

**MeaningはConsultation→Recommendation→Knowledgeに主として属することの確認**: YES（Section 3のArchitecture全体フロー: Consultation Interpretation→Meaning Translation→Recommendation、いずれもMeaning生成に接続）。

**Actionは時間/方位コンテキスト→候補探索→参拝候補に主として属することの確認**: YES（Compass Runtime Model、前回Feasibility監査Section 7）。

**Compassは候補選定時にRecommendationのMeaningを利用してよいことの確認**: YES。Section 6のAuthority境界の通り、Compassは独自のMeaning生成ロジックを持たず、既存Recommendation Authority（スコアリング）とShrine Knowledge Authority（Reason生成）をそのまま呼び出す（前回Feasibility監査Section 6・18のPR-C/PR-D区分）。

**ConciergeはCompassなしでも有用であり続けることの確認**: YES（前回Meaning/Action監査Section 6で確認済み。Concierge単体の責務は自己完結し、Compassへの依存点はない）。

**CompassはConciergeを重複させずに有用であり続けることの確認**: YES。Compassの主入力（時間・方位runtime signal・構造化purpose）はConciergeの主入力（相談自由文）と重複しない。共有するのは下流のRecommendation/Reason/Action Suggestionのみであり、上流の起点は明確に分離されている。

## 9. Authority Matrix（確定版）

前回Meaning/Action Boundary監査のAuthority Matrixを、input/output/主張してよいこと/主張してはならないことの4列で正式化する。

| Authority | Input | Output | 主張してよいこと | 主張してはならないこと |
|---|---|---|---|---|
| **Consultation Authority**（`consultation_interpreter.py`） | 相談自由文、補助条件UI選択 | `interpretation_profile`（state/need/direction_profile等9 Field） | 「ユーザーの相談をこう理解した」という状態解釈 | 心理診断、運命の断定、推薦順位の決定 |
| **Compass Runtime Authority**（`kyusei.py` + `direction_reference.py`） | 生年月日、対象日、出発地点、神社座標 | 年盤・月盤の参考方位、実方位との一致/不一致（`direction_reference`） | 「この期間・この地点からは、参考としてこの方向が示される」という方位コンテキスト | なぜこの神社が良いか、神社自体の性質、日次精度の確実性、決定論的な吉凶 |
| **Recommendation Authority**（候補取得+`_attach_breakdown`） | 候補神社集合、Consultation/Compass Runtime由来のpurpose/need信号、Shrine Knowledge | スコア付き順位、`matched_need_tags`等 | 「この候補集合の中でどの神社が最も支持された結びつきを持つか」 | 神社固有の事実の創作、方位単独を主理由に昇格させること |
| **Shrine Knowledge Authority**（`ShrineDeity`/`ShrineHistory`+Evidence Gate） | 神社固有データ、出典 | deity/shrine_history/goriyaku/history_theme（Evidence Gate通過済み） | 神社固有の歴史・祭神・ご利益・根拠情報 | 方位・占術由来の主張を神社の事実として提示すること |
| **Presentation Authority**（Frontend表示Adapter） | 上記4 Authorityの出力 | ユーザー向け画面表示 | 各Authorityの意味を変えずに翻訳・整形すること | 新規Factの生成、Consultation/方位の再解釈、順位の再計算 |

**「なぜこの方向か」を主張してよいのは**: Compass Runtime Authorityのみ。

**「なぜこの神社か」を主張してよいのは**: Recommendation Authority + Shrine Knowledge Authority（Reason生成経由）。

**「なぜこの神社がこのユーザーに合うか」を主張してよいのは**: 単独のAuthorityでは完結せず、Consultation/Compass Runtime → Recommendation → Shrine Knowledgeの合成結果としてのみ成立する。Compass Runtime Authority単独でこの問いに答えることは禁止。

**弱いシグナルが未サポートの主要Authorityへ昇格していないことの確認**: 確認済み（Section 4-2で確認した`direction_signal`最大+0.02という上限、`recommendation-score-v2-current-design.md:217`「element / birthdate / direction は主理由を上書きしない」という明示的ガードレール、`recommendation-reason-contract.md`の方位を主理由に混入させない禁止規定の三重の担保による）。

## 10. Time / Copy Contract

**年盤+月盤が実装済みの時間的基盤であることの確認**: YES（前回Time Model監査Section 3-4で確認済み、`kyusei.py`全行直読による独立検証）。

**日盤がMVP対象外であることの確認**: YES（`docs/ops/direction-fail-safe.md`が日盤・時盤の追加を明示的に禁止）。

**暦月 vs 節気月の文言含意**: `_solar_month_index()`の境界は固定近似日（2/4, 3/6...）でありカレンダー月の1日とは一致しない（前回Time Model監査Section 4）。UI文言で「今月」を使う場合、この技術的実態とのズレは製品判断で許容範囲とするか、内部処理側でのみ扱うかを決める必要がある（Section 14未解決事項として継続）。

**コピー分類（前回Time Model監査Section 14の再確認＋新規追加分）**:

| コピー例 | 分類 |
|---|---|
| 「今日の吉方位」 | **MISLEADING**（日盤なし、日次精度を暗示） |
| 「今月の吉方位」 | **SUPPORTED WITH QUALIFICATION**（粒度は一致するが「吉方位」の断定的響きに注意） |
| 「参考方位」 | **SUPPORTED BY CURRENT SIGNAL**（`compat-mode-ui-flow.md`・`direction-ranking-design.md`双方が推奨する既存の安全な言い換え） |
| 「今月の流れ」 | **SUPPORTED BY CURRENT SIGNAL**（`kyusei.py`自身の`flow_label_ja`語彙とも一致） |

**製品見出し（Primary headline）として許容される表現**: 「今月の流れ」「今月、意識したい方向」等、粒度と一致し断定を避けた平易な表現。

**副次的説明にのみ許容される専門用語**: 九星気学（Optional）、本命星（Secondary）、月盤（Optional）、吉方位（Secondary、要ヘッジ）— いずれも前回Meaning/Action監査Section 8-4の分類を維持し、Primaryにはしない。

**未来予言・結果保証言語の防止**: `meaning-layer.md`の非断定原則（「あなたは○○です」「この神社へ行けば解決します」等の禁止）がProduct全体の思想として適用される。

## 11. Premium Reconciliation

**FACT（`docs/product/premium-experience.md:63-72`再確認）**: 「地図が高機能になる」「検索条件が増える」「近い神社をもっと探せる」「経路案内が便利になる」をPremium訴求の中心表現として明示的に禁止している。

**Compassはこのルールと衝突するか**: 未解決の継続コンフリクト（前回Feasibility監査Section 14から継続）。Compassの表層的な提示（時間・場所・方向）は、パーソナルな月次文脈・継続利用価値を明示しない限り、この禁止表現と類似して見えるリスクが残る。

**Compass Premium価値を「推薦精度の向上」ではなく「継続的な行動文脈」として定義することの確認**: YES、Section 9のAuthority Matrixが示す通り、Recommendation Authority（スコアリング）はConcierge/Compassで完全共通であり、Compassが「より精度の高い推薦」を提供するという主張の技術的根拠は存在しない。Compassの価値は候補生成の起点（時間・方位・purpose）の新規性にある。

**無料Concierge推薦品質が不変であることの確認**: YES（前回3監査すべてでExisting Concierge Impact = ZEROと判定済み）。

**Compassが価値を提供する軸**: 時間（月次文脈の継続性）、方位（探索の入口の新規性）、purpose（明示的選択による行動の具体化）、行動継続性（毎月の再訪動機、前回Time Model監査Section 11-12のpurpose/origin変更による再訪価値）。

**要clarificationなPremium契約文言**: `premium-experience.md`自体に変更は不要だが、Compass訴求文言を確定する際に同ドキュメントとの適合レビューを個別に行うことを推奨する（未解決事項として継続）。

## 12. Astrology Scope

**Conciergeに関連する既存の西洋占星術責務の棚卸し**: `domain/astrology.py`（`sun_sign_and_element`/`element_priority`）、Compat Mode限定（`public_mode == "compat"`時のみ`astro_bonus`最大+0.6が有効化）。

**CompassはWestern Astrologyを技術的に必要とするか**: **NO**。Section 9のAuthority Matrix、および前回3監査の因果パイプライン検証（`kyusei.py`・`direction_reference.py`のいずれの関数シグネチャにも西洋占星術の要素は登場しない）により、Compassの方向コンテキスト生成はkyusei（九星気学）+ bearing（実方位）のみで完結することを確認済み。

**Kyusei + directionのみでCompass MVPとして十分か**: **YES**。Section 4-1・9で確認した通り、Compassの中核価値（方向コンテキスト+神社候補）はkyusei年盤月盤+bearingの組み合わせのみで技術的に完結する。

**「利用可能な信号」と「必要なProduct Authority」の分離**: 西洋占星術は技術的に「利用可能」（Compat Mode経由で既に実装済み）だが、Compassの「Product Authority」（=Compass Runtime Authorityが何を主張してよいか）としては不要である。両者を混同し、「実装されているから使う」という理由だけでCompassに西洋占星術を組み込むことは、タスクが明示的に禁止する「神秘性を高めるためだけの占術追加」に該当するリスクがある。

**推奨**: **KYUSEI/DIRECTION ONLY**。西洋占星術をCompassに含める技術的必然性は本監査では確認できず、含める場合は独立した製品判断（FUTURE OPTIONAL）として扱うべきである。

## 13. Taxonomy Conflict

**既存の`health`taxonomy不整合の追跡**: `docs/product/consultation-theme-taxonomy.md`が`health`を`consultation_axis`の値として文書化する一方、実装（`backend/temples/domain/consultation_axis.py:9-19`）の9値enumには`health`が存在しない。`health`は`need_tags.py`側にのみ実在する（前回Feasibility監査Section 9で発見、本監査で再確認のみ行い、コードの再読は行っていない）。

**これはCompass MVPをブロックするか**: **NO**。Compassのpurposeマッピングは既存`need_tag`層（`health`を含む15固定タグ）を使う設計であり、存在しない`consultation_axis`側の`health`値には依存しない。

**ブロッキングコンフリクトと無関係な既存taxonomy debtの分離**: この不整合はConcierge既存の文書間不整合であり、Compassの実装可否に一切影響しない、無関係な既存debtである。

**分類**: **NON-BLOCKING DEBT**。

## 14. target_date Decision

**MONTHモデルとの整合**: 前回Time Model監査Section 8で確立した通り、`target_date`は既存`visit_date`パターンを踏襲し、Backend内部で節気月粒度へ丸める設計。Product Modelが月次であることと、Runtime契約フィールドが日付型であることは矛盾しない（責務分離: Backend契約は日付を受け取り月粒度で処理し、Frontend表示は月単位の言葉で見せる）。

**将来の日次拡張性**: `target_date`のまま将来day-plate実装時にフィールドの意味を変えずに精度だけを引き上げられる（前回監査で確認済み）。

**現行命名が意味的に妥当であれば不要なSchema変更を避ける**: 既存`visit_date`という前例がある以上、Compassが`target_month`という別名の契約を新設する必然性は本監査でも確認できなかった。

**分類**: **KEEP target_date**。

## 15. Remaining Contract Changes

以下は本監査が発見した、Compassの実装可否そのものをブロックしない、独立した製品/文書メンテナンス項目である。いずれも本監査の範囲外として実行しない。

1. `concierge-first-final-spec.md:29`のゲート文言（「吉方位はDirection Audit完了まで前面化しない」）を、本監査シリーズの完了を踏まえて更新するか、Compassという別Productの文脈で明示的に読み替えるかの製品判断（Section 4-1）。
2. `recommendation-score-v2-foundation.md`（Reference）が、既にActiveな後継文書（`recommendation-score-v2-current-design.md`）と矛盾する古いゲート文言を保持したままである状態の整理（Section 4-2、Compassとは無関係な既存ドキュメント衛生課題）。
3. `consultation-theme-taxonomy.md`と`consultation_axis.py`の`health`不整合の解消要否（Section 13、Non-Blocking Debt、前回監査から継続）。
4. `premium-experience.md`とCompass訴求文言との適合レビュー（Section 11、前回監査から継続）。
5. Compassが西洋占星術を将来含めるかどうかの製品判断（Section 12、FUTURE OPTIONAL）。

## 16. Final Classification

**Primary Classification: CLEAR WITH CONTRACT FOLLOW-UP**

| 項目 | 判定 |
|---|---|
| Direction Audit Status | **DIRECTION AUDIT COMPLETE WITH CONTRACT CLARIFICATION** |
| Concierge Direction Foreground | **AUXILIARY ONLY**（変更なし） |
| Compass Direction Foreground | **ALLOWED WITH CONDITIONS**（Section 4-1の3軸検証済み、ただしSection 9のAuthority境界とSection 10のコピー境界を条件とする） |
| Compat Mode Relationship | Compassは計算モジュール（Signal）を再利用するが、Compat Modeの製品責務（Authority）は継承しない（Section 6） |
| Concierge Product Promise | 「今の悩みや願いをもとに、あなたと接点のある神社を見つけます。」— 既存契約と整合、修正不要（Section 7） |
| Compass Product Promise | 「今月の流れと目的から、向かう方向と参拝候補を見つけます。」— 既存契約と整合、任意の補足推奨のみ（Section 7） |
| Meaning / Action Boundary | Meaning=Recommendation Reason（両製品共有・無改修）、Action=Compass候補生成起点（新規）+既存Action Suggestion v4（両製品共有・無改修）（Section 8） |
| Compass MVP Astrology Scope | **KYUSEI/DIRECTION ONLY**（Section 12） |
| Premium Compatibility | COMPATIBLE WITH CLARIFICATION（Section 11、未解決の継続コンフリクト） |
| Health Taxonomy Conflict | **NON-BLOCKING DEBT**（Section 13） |
| target_date Decision | **KEEP target_date**（Section 14） |
| Production Changes Required | **NONE**（本監査を含む4監査シリーズすべてでDB変更・Ranking変更・Concierge改修は不要と判定） |

**Final Classification: CLEAR WITH CONTRACT FOLLOW-UP**。境界そのものは技術的・契約的に明確であり実装をブロックしないが、Section 15に列挙した5項目の契約文書メンテナンス（特にゲート文言のクローズという製品判断）が実装着手前の望ましいフォローアップとして残る。

---

## 付録: 方法論

本監査は、前回3監査（feasibility・time-model・meaning-action-authority-boundary）の確立済み結論を出発点としつつ、タスク指示（既存正本文書の再読・Direction Audit言及の再走査）に従い、`docs/product/concierge-first-final-spec.md`・`docs/product/compat-mode-ui-flow.md`・`docs/analytics/recommendation-score-v2-foundation.md`・`docs/analytics/recommendation-score-v2-current-design.md`・`docs/analytics/recommendation-score-v3-design.md`を本セッションで新たに直接読み込み、リポジトリ全体を「Direction Audit」で横断検索した。この過程で、前回3監査では未発見だった第2のゲート（Score本体組み込み）を新たに発見し、その現状（Active後継文書による実質的な無効化）を独立に確認した。すべてのFACT主張は、本監査で新たに読んだ正本文書からの直接引用、または前回3監査での直接コード確認のいずれかに基づく。INFERENCE/HYPOTHESIS/UNRESOLVEDは明示的にそう記載している。既存正本文書の文言はいずれも変更していない。

## 関連ドキュメント

- `docs/audit/premium-visit-compass-recommendation-feasibility.md`
- `docs/audit/premium-visit-compass-time-model-contract.md`
- `docs/audit/concierge-compass-meaning-action-authority-boundary.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/compat-mode-ui-flow.md`
- `docs/product/concierge-modes.md`
- `docs/analytics/recommendation-score-v2-foundation.md`
- `docs/analytics/recommendation-score-v2-current-design.md`
- `docs/product/premium-experience.md`
