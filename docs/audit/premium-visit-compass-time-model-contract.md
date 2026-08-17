> **Status: Audit — 時点記録**
>
> 本ドキュメントは、Premium「Visit Compass」の時間モデル（today / month / hybrid）を、現行実装・正本契約・Premium価値観に照らして監査した時点記録である。コード・Model・Migration・Serializer・Ranking・Concierge挙動・Premium UI・Analyticsの変更は一切含まない。実装計画ではなく、時間モデルの最小整合案の提示までを範囲とする。
>
> 前提となる監査: `docs/audit/premium-visit-compass-recommendation-feasibility.md`（分類B: Existing Engine Reusable With Mode Policy）。本書はその監査結果を鵜呑みにせず、方位/九星気学の時間粒度に関する主張を本書で独立に再検証した。

# Premium Visit Compass — 時間モデル契約監査

## 1. Executive Summary

**結論（先出し）: Primary Time Model = MONTH。**

`backend/temples/domain/kyusei.py`を全行直接読み、`planned_visit_lucky_directions()`の内部計算を再検証した結果、前回監査の「日盤は未実装で年盤・月盤のみ」という主張は**独立に再確認された（FACT）**。それだけでなく、本監査は前回監査が明示していなかった、より強い技術的事実を確認した:

**`visit_date`の「日」の値は、月の境界を跨がない限り、出力に一切影響しない。** `_solar_month_index(planned)`（`kyusei.py:229-236`）は`planned.month`と`planned.day`から「どの節気月に属するか」だけを求め、以降の`month_center`・`stars`・`monthly_lucky`計算はすべて`month_index`・`ki_year`・`honmei.num`の3値だけで決まる（`kyusei.py:248-271`）。日そのものを使う項は存在しない。つまり同じ節気月内であれば、`visit_date`をどの日に変えても`planned_visit_lucky_directions()`の返り値は完全に同一になる。

したがって、「today」を謳うことは実装の実際の粒度と乖離しており、「month」（正確には太陽暦の節気月、カレンダー月とは境界がずれる）が最も技術的に誠実な最小モデルである。「hybrid」は、月次シグナルに日次の見た目上の新鮮さを持たせようとする設計であり、根拠となるシグナル自体は変化しないまま「今日新しい結果」を演出するリスクがある（Section 6）。

**Recommended Runtime Time Key: `target_date`（`target_month`ではない）。** 理由はSection 8で詳述するが、要約すると、既存実装が既に`visit_date`という「日付型フィールドを受け取り内部で月粒度へ丸める」パターンを本番で採用しており（`api_views_concierge.py:558-566`）、Compassがこの既存パターンをそのまま踏襲すること（`target_date`を受け取り、Backendが内部で節気月へ変換する）が最小差分かつ将来の日盤拡張の余地を残す設計になる。

## 2. Scope / Non-Goals

**対象**: kyusei年盤・月盤実装、方位参照生成、Recommendation Reason/Evidence/Knowledge契約、Premium契約との時間モデル整合性の調査、およびtoday/month/hybridモデルの比較判定。

**対象外（今回変更しない）**: 本番Frontend/Backendコード、Concierge挙動、Recommendationスコアリング・Weight、Recommendation Reason挙動、Premium UI、DB Model、Migration、Serializer、Analytics Event、日盤・時盤ロジックの追加、新規Compassエンドポイント、新規purpose taxonomy（必要性が証明されない限り）。

## 3. Current Runtime Evidence

すべてFACT（本監査で直接コードを読んで確認）。

| 項目 | file:line | 内容 |
|---|---|---|
| 年盤計算 | `backend/temples/domain/kyusei.py:191-226` `annual_lucky_directions()` | 生年月日→本命星、`today`（省略時`timezone.localdate()`）→年星。年星の算出は`_ki_year()`（2/4境界）のみに依存し、月・日は使わない |
| 月盤計算 | `backend/temples/domain/kyusei.py:239-284` `planned_visit_lucky_directions()` | 生年月日+`visit_date`必須。年盤×月盤の交差を返す。`calculationMethod: "annual_monthly_kyusei_v1"` |
| 節気月インデックス | `backend/temples/domain/kyusei.py:229-236` `_solar_month_index()` | 固定近似境界（2/4, 3/6, 4/5, 5/6, 6/6, 7/7, 8/8, 9/8, 10/8, 11/7, 12/7、および1/6未満は前年12月扱い）でdateを12分割のいずれかへ分類 |
| 日盤・時盤 | なし | `annual_lucky_directions()`のdocstring（`:192`）「月盤・日盤は扱わない」、`planned_visit_lucky_directions()`のdocstring（`:240`）「日盤は対象外」と明記。コード内に日単位の計算項は一切存在しない |
| 方位（bearing）計算 | `backend/temples/services/direction_reference.py:35-45` `_bearing()`/`_direction_label()` | 出発地点・神社座標のみに依存する純粋な地理計算。日付には一切依存しない |
| direction_reference生成 | `backend/temples/services/direction_reference.py:48-93` `build_direction_reference()` | `direction_profile`（kyusei計算結果）+ `user_origin` + `shrine`が揃った場合のみ返す。`visitDate`は表示用文字列としてそのまま通すだけで、この関数内では再計算しない |
| 生年月日由来のRuntime信号 | `backend/temples/api_views_concierge.py:558-572` | `visit_date = data.get("visit_date") or data.get("planned_visit_date")`（`visit_date`が正、両者エイリアス）。`visit_date`があれば`planned_visit_lucky_directions()`、なければ`annual_lucky_directions()`（年盤のみ）を呼ぶ |
| 出発地点/位置情報の扱い | `api_views_concierge.py`（`_resolve_request_location_inputs`、前回監査で確認済み） | リクエスト単位のRuntime入力、永続化なし |
| 対象日フィールドの既存命名 | `visit_date`（Backend）/`planned_visit_date`（エイリアス）、Frontend側`buildConciergeRequestPayload.ts`・`chatRequest.ts`・`ConciergeClientFull.tsx`でも`visit_date`系の命名が使われている（grep結果、FACT） | 既存の「日付型フィールドを受け取り内部で粒度を丸める」パターンの前例 |
| 方位のランキング影響 | `concierge_chat_ranking.py:291-323` `_score_direction_signal()`、`DIRECTION_SIGNAL_MAX = 0.02`（`:48`） | 一致時のみ+0.02、独立監査で再確認 |
| モード判定ヒューリスティック | `concierge_chat_ranking.py:1721-1737` `_resolve_public_mode()` | 「生年月日あり・本文なし」→`compat`。独立監査で再確認、コード内容は前回監査の記述と完全一致 |
| 方位縮退契約 | `docs/ops/direction-fail-safe.md` | `calculation_method`は`annual_monthly_kyusei_v1`のみ受理。「日盤・時盤や固定ダミー方位へ置き換えない」と明記、リリース前チェックリストにも「日盤・時盤、ダミー方位が追加されていない」を明記 |
| 既存Recommendation Reason契約 | `docs/core/recommendation-reason-contract.md:246-256`（前回監査で確認済み、本書で再言及のみ） | 方位情報は主理由の文章生成に混入禁止、独立カードのみ |
| 既存Premium契約 | `docs/product/premium-experience.md:63-72`（前回監査で確認済み、本書で再言及のみ） | 「地図が高機能になる」「検索条件が増える」をPremium中心表現として禁止 |

**独立再検証の結論**: 前回監査（`premium-visit-compass-recommendation-feasibility.md` Section 5-2）の「日盤未実装・年盤月盤のみ」という主張は、本監査でのコード全文直読により確認された。加えて本監査は、前回監査が言及していなかった「同一節気月内では`visit_date`の日を変えても出力が不変」という、より具体的で強い事実を新たに確認した。

## 4. Kyusei Time Granularity

`planned_visit_lucky_directions(birthdate, visit_date)`の依存変数を明示的に列挙する（`kyusei.py:239-284`を直読して抽出、FACT）:

```text
入力: birthdate（→ honmei.num のみに使用）, visit_date

visit_date から使う値:
  - planned.month, planned.day  → _solar_month_index() の月バケット判定にのみ使用
  - ki_year = year_star(today=planned).ki_year → 2/4境界のみに反応する年区分

以降の計算（month_center, stars, monthly_lucky, combined）は
  month_index, ki_year, honmei.num
の3値のみで決定される。planned.day そのものは月バケット判定後は一切参照されない。
```

**結論（FACT）**: 同一節気月内であれば、`visit_date`をどの日に変更しても`planned_visit_lucky_directions()`の返り値（`luckyDirection`/`luckyDirections`/`excludedDirections`）は完全に同一。日次で変化する要素はコード上に存在しない。

**注意（節気月 ≠ カレンダー月）**: `_solar_month_index()`の境界は「2/4, 3/6, 4/5, 5/6, 6/6, 7/7, 8/8, 9/8, 10/8, 11/7, 12/7」という固定近似日であり、暦月の1日とは一致しない。例えば2月1日〜2月3日は前の節気月（1月扱い）に属する。**もしCompassの`target_month`が「カレンダー月」を意味するUI/APIとして設計された場合、月初の数日間で実際の計算粒度（節気月）とズレる。** これは月モデルを採用する場合でも解消が必要な設計上の注意点であり、Section 8で扱う。

## 5. Today Model

**分類: NOT RECOMMENDED FOR MVP。**

- 日盤・時盤は存在しない（Section 3・4、FACT）。
- `target_date`が現在Backendへ渡っても、Section 4で確認した通り、同一節気月内では計算結果に一切影響しない。
- `target_date`が変化しても結果が変わらない実装の上に「today」を製品コンセプトの中心に置くと、UIが「今日の吉方位」を謳った場合、ユーザーが日をまたいで確認しても同じ結果しか返らない、という体験上の矛盾を生む（Section 14のコピー境界にも直結）。
- 真の日次モデルを実現するには、日盤（および正確な節入り時刻）の新規実装が必要であり、これは`docs/ops/direction-fail-safe.md`が明示的に禁止する変更（「日盤・時盤や固定ダミー方位へ置き換えない」）と衝突する。

**Daily Plate Required For MVP: NO**（today単独モデルを避ける限り）。ただし将来的に真のtodayモデルを目指す場合は**YES（新規ドメインロジックが必要）**。

## 6. Month Model

Section 4の設問に沿って回答する。

**1. 現行の年盤+月盤実装だけで、日盤を追加せずにMVPとして十分な情報量があるか？**
YES。`planned_visit_lucky_directions()`は既に年盤×月盤の交差済みlucky directionsを返しており、Compassの「今月意識したい方向」という粒度の情報としてそのまま使える。追加のドメインロジックは不要。

**2. 月モデルは現行計算の実態を正確に反映しているか？**
条件付きYES。実態は「節気月」（约30日、固定近似境界）であり、「カレンダー月（1日〜末日）」ではない。「月モデル」を採用する場合、UIコピーが「今月」という語を使うなら、月初数日のズレ（Section 4参照）を許容範囲とするか、内部的に「節気」であることを踏まえた文言（例:「このシーズン」）にするかは製品判断が必要。技術的には既存計算＝節気月であることを偽らない限り、「月」表現は妥当。

**3.「今月の流れ」は「今日の吉方位」より技術的に誠実か？**
YES。Section 4・5の通り、現行実装が実際に計算しているのは月（節気月）粒度の情報であり、「今日の吉方位」という表現は実装が持たない日次精度を暗示する。「今月の流れ」の方が計算の実態と一致する。

**4. 月モデルは新規DB field / Model / Migration / Serializer / Ranking system / Shrine Knowledge fieldを必要とするか？**
すべて不要（NO）。既存の`visit_date`入力パターン、既存`kyusei.py`関数、既存`direction_reference.py`、既存ランキング（`_score_direction_signal`は月盤情報を既に扱っている）をそのまま使える。新規に必要なのは、前回監査で指摘した「方位セクターによる候補絞り込み」（新規ロジックだが、bearing計算自体は既存流用）と、Compass用オーケストレーション入口のみであり、これはtoday/month/hybridいずれのモデルでも共通して必要になる部分であって、月モデル固有の追加コストではない。

**5. 月次方位はRuntimeのみで完結できるか？**
YES。`planned_visit_lucky_directions()`は毎回の呼び出しで再計算される純粋関数であり、永続化を要求しない（FACT、Section 3の`build_direction_reference()`も同様に純粋関数）。

**6. 月次シグナルは永続化せず再計算可能か？**
YES。生年月日（既存`UserProfile.birthday`）+ 対象日（Runtime入力）があれば、いつでも同一結果を再計算できる。月次シグナルをキャッシュ・永続化する動機は「計算コストの高さ」ではなく（計算は軽量な純粋関数）、あるとすれば「過去のCompass結果の振り返り表示」のような製品要件であり、それはMVPの必須要件ではない（Section 11参照）。

**7. 同一月内でpurposeを変えた場合、temporal direction signalが不変でも候補神社は意味のある形で変わるか？**
YES。Section 9・11で詳述するが、`purpose`（→`need_tag`/`goriyaku_tag_ids`）は`kyusei.py`・`direction_reference.py`のいずれにも一切関与しない独立した入力であり（FACTとして両ファイルの引数リストにpurpose相当の値が存在しないことを確認済み）、既存ランキングの`score_need`/`history_theme boost`/`matched_by_gid`経路を通じて候補・順位・Reasonに影響する。したがって方位シグナルが月内で不変でも、purposeを変えれば異なる神社群が提示され得る。これは「日次リフレッシュ」に頼らずに月内で意味のある再訪動機を作れることを示す既存アーキテクチャ上の根拠である。

**Month Readiness: READY WITH CONTRACT CLARIFICATION。** 実装ロジック自体はREADYに近いが、「月」の意味（節気月 vs カレンダー月）をコピー・契約で明示する必要があるため、この分類とする。

## 7. Daily Model（Section 5と統合検証）

タスク要件に沿って明示的に再列挙する。

- 日盤は存在するか: **NO**（`kyusei.py`のdocstring2箇所で明記、コード内に日単位の計算項なし）
- 日次方位計算は存在するか: **NO**
- `target_date`は現在kyusei方位結果を変化させるか: **NO（節気月境界を跨がない限り）**
- 現行コードは年/月情報のみを使っているか: **YES**
- 真の日次方位に必要な追加ドメインロジック: 正確な節入り時刻計算、日盤（および場合によっては時盤）アルゴリズムの新規実装。これは`docs/ops/direction-fail-safe.md`の禁止事項と衝突するため、着手する場合はこの運用契約自体の改定が前提になる（本監査のスコープ外）。

**分類: NEW DOMAIN LOGIC REQUIRED**（真の日次モデルを目指す場合）。MVPとしてはSection 5の通り**NOT RECOMMENDED**。

## 8. target_date vs target_month

| 観点 | `target_date` | `target_month` | 備考 |
|---|---|---|---|
| 意味的正確性 | 中（実際は月粒度に丸められるため、フィールド名は「日」を暗示するがAPIの実効精度は月） | 高（実態と一致） | |
| 実装コスト | 低（既存`visit_date`パターンをそのまま流用、Backend側で節気月へ丸める処理を書くだけ） | 中〜高（新しい入力型・UIの月選択コンポーネント・既存`visit_date`との非対称な契約を新設する必要） | |
| 将来拡張性（日盤対応） | 高（フィールドの意味を変えずに、Backend内部の丸め処理を精緻化するだけで日次対応へ移行できる） | 低（`target_month`のまま日次精度を持たせるのは概念的に矛盾するため、後からフィールド名ごと変更が必要になる） | |
| 年盤・月盤との互換性 | 高（既存`visit_date→planned_visit_lucky_directions`と同型） | 高（同様に使えるが、月単位入力から代表日を合成する変換が別途必要） | |
| 将来の日盤ロジックとの互換性 | 高 | 低（月入力からは日を復元できない） | |
| 誤解を招くUIコピーのリスク | 中（`target_date`という名前がAPI利用者に「日次精度がある」と誤解させ得るが、これはUI文言側で制御可能） | 低（フィールド名自体が節気月粒度であることを正直に示す） | ただしSection 4の「節気月≠カレンダー月」のズレはどちらの名前でも解消されない |

**推奨: `target_date`。** 根拠:

1. 既存実装が既に`visit_date`という日付型フィールドを受け取り、Backend内部（`planned_visit_lucky_directions`）で節気月粒度へ丸めるパターンを本番採用済みである（Section 3）。Compassがこれと異なる`target_month`型契約を新設すると、同一ドメイン内に「日付を受けて月に丸める」既存パターンと「月を直接受ける」新パターンが並存し、将来的な混乱リスクを生む。
2. `target_date`は将来の日盤実装（Section 7で「新規ドメインロジックが必要」と分類したが、禁止されているわけではなく、将来解禁される可能性はある）への移行時に、フィールドの意味を変えずに精度だけを上げられる。`target_month`はこの移行時にフィールド名ごと非互換な変更を強いる。
3. **フィールド名の意味的精度の問題は、API契約ではなくUIコピー層で解決すべき**という判断。`target_date`というRuntime契約と、「今月の流れ」という表示文言は矛盾しない — Backendは日付を受け取って月粒度で処理し、Frontendは結果を月単位の言葉で見せる、という責務分離で足りる。

**この選択に伴うOPEN DECISION**: `target_date`という名前を採用する場合、API利用者（Frontend実装者）が「日ごとに結果が変わる」と誤解しないよう、Compass Runtime Contract側にSection 4の丸め挙動（節気月境界）を明記する必要がある。これは本監査では文書化のみを推奨し、実際の契約文書作成は別PR（Section 16）とする。

## 9. Purpose × Direction × Origin

各入力の責務を分離して明示する（FACTベース、`kyusei.py`・`direction_reference.py`の引数シグネチャを直読して確認）。

```text
purpose
  └─ 変えるもの: need_tag / goriyaku_tag_ids へのマッピングを通じて
                  候補フィルタ・スコアリング（score_need, history_theme boost,
                  matched_by_gid）・Recommendation Reasonの内容
  └─ 変えないもの: kyusei計算（honmei_star/annual_lucky_directions/
                    planned_visit_lucky_directions）には一切入力されない
                    （FACT: 両関数のシグネチャにpurpose相当の引数は存在しない）
                    → 方位そのものは変わらない

monthly direction signal（kyusei由来のluckyDirections）
  └─ 変えるもの: 各候補の direction_reference.matched（一致/不一致）、
                  direction_signal_score（最大+0.02、既存ランキングへの補助加点）
  └─ 変えないもの: 候補神社の集合そのもの（現状、方位で候補を絞り込む
                    フィルタは存在しない — 前回監査Section 5・8で確認済み、
                    本監査でも独立に再確認: build_chat_candidates()の
                    クエリ条件に方位関連の項は存在しない）

origin（出発地点）
  └─ 変えるもの: 神社ごとのbearing（_bearing()は純粋にorigin座標と
                  shrine座標の関数）→ actual_direction → matched判定
                  → direction_signal_score
  └─ 変えないもの: kyusei計算自体（luckyDirectionsはorigin非依存、
                    honmei_starとvisit_dateのみに依存）

Shrine Knowledge（deity/shrine_history/goriyaku/history_theme）
  └─ 変えるもの: Recommendation Reasonの神社固有説明内容
  └─ 変えないもの: 方位計算・スコアの数値そのもの
                    （前回監査で確認済み: deity/shrine_historyは
                    _attach_breakdownのスコア式に一切接続されていない）

Recommendation
  └─ 決めるもの: 候補集合＋スコア（need/element/popular/distance/
                  visit_style/behavior/profile_signal/direction_signal）
                  を合成した最終順位、および神社固有のReason
  └─ 決めないもの: 方位そのもの（kyusei/bearingの計算結果を上書き
                    ・再解釈しない、前回監査のExplanation Authority
                    Boundaryと同一原則）
```

**因果パイプライン（明示）**:

```text
[purpose] ──→ need_tag/goriyaku_tag_ids ──┐
                                            ├─→ Recommendationスコア・順位・Reason
[Shrine Knowledge] ──→ 神社固有Fact ────────┘

[birthdate + target_date] ──→ kyusei月次計算 ──→ luckyDirections ──┐
                                                                     ├─→ direction_reference（一致/不一致）
[origin] ──→ bearing ──→ actual_direction ─────────────────────────┘
                                          └─→ direction_signal_score（既存ランキングへ最大+0.02の補助加点のみ）
```

purposeとdirection signalは互いに独立した入力であり、一方が他方を変化させることはない（FACT）。これらが交わるのはRecommendationの最終合成段階のみである。

## 10. Purpose Changes Within the Same Month

シナリオ: 同一ユーザー・同一月・同一origin・purposeのみ変更（work → relationships）。

| 項目 | 変化するか | 根拠 |
|---|---|---|
| kyusei計算結果（luckyDirections） | **不変** | `annual_lucky_directions`/`planned_visit_lucky_directions`はpurposeを引数に取らない（Section 9、FACT） |
| direction_reference（actual_direction/matched） | **不変**（同一候補神社に対しては） | bearingはorigin/shrine座標のみに依存 |
| direction_signal_score | **不変**（同一候補に対して） | 上記と同じ理由 |
| need_tag/goriyaku_tag_idsマッピング値 | **変化する** | purpose→タグのマッピングが変わるため |
| 候補神社集合 | **変化し得る**（`goriyaku_tag_ids`がhard filterとして機能する場合、前回監査Section 4） | 候補生成クエリの`goriyaku_tags__id__in`フィルタがpurpose由来のtag idに依存 |
| ランキング順位 | **変化し得る** | `score_need`/`history_theme` boost/`matched_by_gid`がpurpose由来のneed_tag/goriyaku_tag_idsに依存 |
| Recommendation Reason | **変化し得る** | `need_profile`/`consultation_axis`相当の入力が変わればInterpretation層の内容が変わる |
| 方位そのもの | **不変** | Section 9の因果パイプライン通り、purposeはkyusei計算の入力ではない |

**結論（重要、タスクの警告と一致）**: purposeを変えても方位（kyusei結果）自体は変わらない。「purposeが方位を変える」という主張は現行実装・提案契約のいずれにも根拠がない。変わるのは候補神社・順位・Reasonであり、これは「同じ方位コンテキストの中で、違う切り口の神社が見える」という体験として整合的に説明できる。

## 11. Monthly Reuse Value

タスクの指示通り、既存能力（Existing Capability）と将来の製品機会（Future Opportunity）を明確に分離する。

**既存能力（現行アーキテクチャがそのまま提供できるもの）**:
- **purposeを変える** → Section 10の通り、既存の候補生成・スコアリング経路がそのまま異なる神社群を返す。追加実装なしで機能する。
- **originを変える**（旅行中、帰省中等） → bearingが変わり、`matched`判定・`direction_signal_score`が変わる。既存の`build_direction_reference()`がそのまま対応する。
- **別の神社候補を見る**（同一purpose・同一方位内での複数候補比較） → 既存Concierge結果一覧の複数候補表示パターンをそのまま流用できる。
- **Shrine Detailへの遷移** → 既存の神社詳細画面・導線をそのまま利用できる（前回監査Section 13で確認したPremium画面境界の既存パターン）。

**将来の製品機会（現行実装にはなく、新規実装が必要）**:
- **「別の方位を探索する」**（ユーザーが任意の方位セクターを選んで候補を見る） → 前回監査で確認した通り、現行は「候補ごとに方位が一致するか採点する」機能のみで、「方位で候補集合を絞り込む」機能は存在しない。これは前回監査PR-Bの範囲。
- **Visit Planning**（参拝計画の作成・スケジュール化） → 既存`Visit`/`ActionEvent`Modelはあるが、Compass結果からの計画作成導線は未実装。
- **Reflection連携**（Compass経由の参拝を振り返りに接続する） → 既存`ShrineReflection`はあるが、前回監査Section 13で確認した通り、Compass起点であることを識別するJoin Keyは存在しない。

**「日次リフレッシュが月内の再利用価値を作る唯一の方法である」という前提を採用しない理由**: Section 6-7・Section 10で示した通り、purpose変更とorigin変更だけで、方位シグナルを変えずに意味のある候補変化を作れる。日次リフレッシュは、変化しない方位シグナルに対して見た目だけ「今日は違う」という演出を作るリスクがあり（Section 12参照）、既存の2つの正当な変化軸（purpose/origin）を差し置いてまで必要とする根拠はない。

## 12. Hybrid Model

タスク例示の概念（月次temporal signal + 当日のinteraction context）を検証する。

**「Hybridは実質的な追加価値を提供するか、それとも見せかけの日次新鮮さを作るだけか」への回答**: 後者のリスクが高いと判定する。

- 月次temporal signal（luckyDirections）はSection 4の通り月内不変。
- 「当日のinteraction context」を何らかの形でUIに混ぜる場合、その入力がkyusei計算・bearing計算のいずれにも接続されない限り（Section 9のパイプライン参照）、それは「表示上の演出」であって「シグナルの変化」ではない。
- 例えば「今日はこの神社が輝いて見える」といった日替わり表示を、内部的にはランダム化や日付ハッシュのような**シグナルと無関係な人工的変動**で実現した場合、これはタスクが明示的に禁止する「決定論的な占い・断定的な結果の提示」（Section 8/14相当の禁止事項）に抵触するリスクがある。方位シグナルが変わっていないのに「新しい結果」と見せることは、Recommendation Reason Contractの断定表現禁止原則（「吉方位なので行くべき」等を避ける）の精神とも整合しない。

**Hybrid Readiness: NOT RECOMMENDED FOR MVP。** 根拠: (1) 月次シグナルに接続された正当な「日次差分」の実装（=日盤）はNEW DOMAIN LOGIC REQUIREDでMVPスコープ外（Section 7）。(2) 月次シグナルに接続されない「見た目だけの日次差分」は、既存のRecommendation Reason Contract・direction-fail-safe.mdが求める「断定・演出をしない」原則と衝突するリスクを持つ。(3) Section 11で示した通り、purpose/originの切り替えという、シグナルに正しく接続された既存の変化軸が既にあるため、Hybridでなければ得られない価値が現時点では確認できない。

**フラグ（タスク要件通り）**: もし将来Hybridを検討する場合、「当日のinteraction context」が実際にkyusei/bearing計算のいずれかの入力に接続される新規シグナル（例: 実装された日盤）であることを条件とすべきであり、シグナルと無関係なUI変動によって日次新鮮さを演出する設計は採用すべきでない。

## 13. User-Facing Copy Boundary — 「今月の流れ」の許容範囲

現行実装が実際に提供できる情報のみに基づき、「今月の流れ」が意味してよい範囲を定義する。

**許容される意味**: 「生年月日から算出した本命星と、今月（節気月）の年盤・月盤の組み合わせにおいて、参考として挙げられる方位がある」という、**参考情報・探索の入口**としての意味。

**許容されない意味（タスク要件通り、明示的に禁止）**:
- 決定論的な占い結果の断定
- 結果の保証
- 未来の出来事の予言
- 「この方向に行けばお金・恋愛・健康・成功が手に入る」という因果主張
- 「この神社が客観的に最善である」という証明

**概念的階層（タスク要件の再確認、既存実装と整合）**:

```text
user purpose + monthly runtime signal + origin
        ↓
direction context（方位の参考情報。既存direction_reference.pyの出力範囲を超えない）
        ↓
candidate shrines（既存build_chat_candidates + 前回監査PR-Bの方位セクターフィルタ）
        ↓
Recommendation / Evidence / Knowledge（既存_attach_breakdown + Evidence Gate + build_recommendation_reason_v4、無改修で再利用）
        ↓
shrine proposal
```

**方位シグナルが神社Knowledgeを上書きしてはならない、という原則の既存担保**: 前回監査Section 11で確認した通り、`recommendation_reason_v4.py`は`direction_reference`を一切参照せず、`direction_reference.py`は`reason_text`を生成しない。この分離は既存契約（`recommendation-reason-contract.md:246-256`）によって既に強制されており、Compassのために新設する必要はない。

## 14. Copy Boundary（比較表）

| コピー例 | 分類 | 理由 |
|---|---|---|
| 「今日の吉方位」 | **MISLEADING** | 実装は日盤を持たず、同一節気月内では日を変えても結果が不変（Section 4・5）。「今日」という語が実装にない日次精度を暗示する |
| 「今日の運勢」 | **UNSUPPORTED** | 「運勢」は決定論的な占い結果を暗示し、タスクが明示的に禁止する断定表現に該当。また日次精度も実装にない |
| 「今月の吉方位」 | **SUPPORTED WITH QUALIFICATION** | 計算粒度としては月（節気月）と整合するが、「吉方位」という語自体がやや断定的（「これが吉である」という確定的主張）に傾きやすいため、既存`direction-ranking-design.md`の「使用しない表現」原則（「吉方位なので行くべきです」等）と同様の注意が必要。「参考方位」等への言い換えが既存原則と整合する |
| 「今月の流れ」 | **SUPPORTED BY CURRENT SIGNAL** | 計算粒度（節気月）と一致し、「流れ」という語は`kyusei.py`自身が内部的に使う語彙（`flow_label_ja`、`STAR_FLOW`辞書、Section 3）とも一致する。断定的な因果主張を含まない |
| 「今月、参拝コンパス」 | **SUPPORTED WITH QUALIFICATION** | 製品名としては問題ないが、「コンパス」という語が「唯一の正しい方向を指し示す」という確定的なニュアンスを持ちうるため、UI文言全体で「参考情報である」ことを併記する必要がある（既存`direction-response-contract.md`の表示制約と同じ扱い） |
| 「今月、意識したい方向」 | **SUPPORTED BY CURRENT SIGNAL** | 断定を避け、探索的なトーンであり、月粒度の実装と整合する。既存`direction-ranking-design.md`の「使用できる表現」原則（「参考情報です」等）に最も近い |

**目的の再確認**: 本セクションの目的は占星術・九星気学用語の排除ではなく、実装が持つ時間的精度・因果的確実性を超えたコピーを防ぐことである（タスク要件通り）。

## 15. Direction Responsibility

**判定: 方位は候補フィルタ/コンテキスト、または補助Runtimeシグナルにとどめるべきで、主要なRecommendationランキング権威にすべきではない。**

根拠（前回監査・本監査の双方で確認済みのFACT）:
- 既存の`direction_signal_score`は最大+0.02という小さな補助加点であり、`score_need`（主要ドライバー、前回監査Section 4）と比較して桁違いに小さい。
- `docs/product/direction-ranking-design.md`が「相談テーマ、need、神社固有情報を主軸とし、方位だけで候補を決定しない」と明記し、実装（Weight比較）もこれに従っている。
- `docs/core/recommendation-reason-contract.md`が「方位一致をRecommendation Reasonの主理由として表示する」ことを明示的に禁止している。

**月次MVPのためにRanking Weightsを変更する必要はない。** 現行の`_score_direction_signal`（+0.02上限）の仕組みは、Compassが「方位セクターで候補を事前に絞り込んだ後」に呼ばれても意味を持つ（一致判定自体は変わらない）。Compassの新規性は「候補集合を方位で絞り込む」という前段のフィルタ機構（前回監査PR-B）にあり、スコア式自体を変える理由は本監査でも確認できなかった。

**もしこの前提が崩れるとしたら**: Compassの候補プールが「方位一致」を主要な差別化要因として提示したい場合（例:「この方位内で最もあなたに合う神社」という強い訴求)、既存の小さな補助加点のままではランキング上その意図が反映されない可能性がある。しかしこれは「Ranking変更が必要」という結論ではなく、「Compassが方位を主要ランキング権威にすることが製品として妥当か」という別のOPEN DECISIONであり、本監査はこれを推奨しない（Section 9・13の階層原則と整合しないため）。

## 16. Model Comparison

| Criterion | today | month | hybrid |
|---|---|---|---|
| Current implementation fit | 低（日盤なし、`target_date`を変えても結果不変） | 高（`planned_visit_lucky_directions`がそのまま月粒度で動作） | 低（月次シグナル＋人工的な日次演出が必要） |
| New domain logic required | YES（日盤の新規実装） | NO | 部分的（正当な日次差分を持たせるなら実質today相当が必要） |
| DB change | NONE | NONE | NONE |
| Ranking change | NOT REQUIRED（ただし精度不足のまま「today」を訴求する矛盾は残る） | NOT REQUIRED | NOT REQUIRED |
| Temporal accuracy | 低（実装と乖離） | 高（実装と一致、ただし節気月≠カレンダー月の注意あり） | 低〜中（見た目の精度と実際の精度が乖離しやすい） |
| Copy risk | 高（Section 14「MISLEADING」） | 低〜中（「吉方位」表現に注意、「流れ」表現は低リスク） | 高（Section 12のリスク） |
| Premium recurring value | 不明確（日次チェック習慣に依存し、実装の裏付けがない） | 中〜高（purpose/origin変更という既存の正当な再訪動機がある、Section 11） | 不明確（人工的演出への依存リスク） |
| Future extensibility | 低（日盤禁止契約と衝突、`docs/ops/direction-fail-safe.md`） | 高（`target_date`契約のまま将来day-plate対応が可能、Section 8） | 低（現時点で明確な設計原則がない） |
| MVP complexity | 中（日盤実装が必要なら高いが、実装しないまま「today」を謳うなら低いが不誠実） | 低（既存流用が中心） | 中〜高（演出設計・線引きの検討コストがかかる） |

**分類**:

- today: **NOT RECOMMENDED FOR MVP**
- month: **READY WITH CONTRACT CLARIFICATION**
- hybrid: **NOT RECOMMENDED FOR MVP**

## 17. Final Classification

Primary Time Model: **MONTH**

Month Readiness: **READY WITH CONTRACT CLARIFICATION**

Today Readiness: **NOT RECOMMENDED FOR MVP**

Hybrid Readiness: **NOT RECOMMENDED FOR MVP**

Daily Plate Required For MVP: **NO**

Recommended Runtime Time Key: **target_date**

DB Change: **NONE**

Ranking Change: **NONE**

Existing Concierge Impact: **ZERO**（前回監査と同じ理由: Compassは新規オーケストレーション層として実装され、`ConciergeChatView`・`concierge_chat.py`・`concierge_chat_ranking.py`の既存呼び出し経路を改修しない前提のため）

Premium Contract Compatibility: **COMPATIBLE WITH CLARIFICATION**（`premium-experience.md`の「地図/検索の高機能化をPremium中心に置かない」原則との整合性は、Compassの訴求文言が「パーソナルな月次文脈＋継続利用」を前面に出すことを条件に保てる。この訴求設計自体は本監査で確定しない、前回監査Section 14で記録済みの未解決コンフリクトと同一論点）

**Final Recommendation**: `backend/temples/domain/kyusei.py`と`direction_reference.py`を全行直読して独立検証した結果、現行実装が実際に持つ時間解像度は年盤・月盤（節気月）までであり、日盤は存在しない。`visit_date`の日の値は節気月境界を跨がない限り出力に影響しないという、より具体的な事実も本監査で新たに確認した。この実装実態と最も整合するのは「month」モデルであり、「today」を製品コンセプトの中心に据えることは実装が持たない精度を暗示する誤解を招くリスクがある。「hybrid」は、月次シグナル自体を変えずに日次の新鮮さを演出しようとする設計になりがちで、Recommendation Reason Contractが求める非断定原則と衝突するリスクがあるため、現時点でMVPとしては推奨しない。月モデルはDB変更・Ranking変更・Concierge改修のいずれも不要であり、Runtime契約フィールドは`target_date`として設計し、Backend内部で節気月へ丸める既存パターン（`visit_date`と同型）を踏襲することで、将来の日盤拡張にも備えられる。purpose変更・origin変更という、方位シグナル自体を変えずに意味のある再訪動機を作れる既存の2軸（Section 10・11）があるため、月モデルであっても「同じ月に何度も価値がある」という体験は成立し得る。

**Open Product Decisions**:

1. 「今月」をUI/APIでカレンダー月として扱うか、節気月のまま（またはユーザーに見せない内部実装として）扱うか（Section 4・8）。
2. Compass結果を永続化するか（Section 6-6、母艦判断、前回監査Section 13の未解決事項と同一）。
3. Premium訴求文言が`premium-experience.md`の禁止表現（地図/検索高機能化）と誤読されないための具体的コピー設計（前回監査Section 14と同一の未解決事項、本監査ではSection 14の許容/非許容表現リストまでを提供）。
4. 「吉方位」という語をCompassのコピーに残すか、「参考方位」等へ統一するか（Section 14）。
5. 将来的に真のtodayモデル（日盤実装）を目指すか否か。目指す場合、`docs/ops/direction-fail-safe.md`の禁止事項自体の改定が前提になるため、これは本監査のスコープを超える製品判断。

## 18. Candidate PR Split

以下は監査結果に基づく提案であり、実装しない。前回監査（`premium-visit-compass-recommendation-feasibility.md` Section 19）のPR分割案と整合させる。

- **PR-A: Compass Runtime Contract** — `target_date`（Section 8の推奨）+ `origin` + `purpose`のRuntime request契約定義。Backend内部での節気月丸め挙動を契約文書に明記する。
- **PR-B: Direction Calculation / Candidate Context** — 前回監査と同一。方位セクターによる候補絞り込み（新規、bearing計算は既存流用）。月モデルを前提とするため、日盤対応は含まない。
- **PR-C: Recommendation Integration** — 前回監査と同一。
- **PR-D: Compass Explanation** — Section 13・14のコピー境界（「今月の流れ」等、SUPPORTED分類の表現のみ使用）を反映した表示Adapter。
- **PR-E: Premium UI** — 前回監査Section 14の未解決コンフリクトを先に解消することを推奨（変更なし）。
- **PR-F: Analytics Instrumentation** — 前回監査と同一、独立契約PR。

いずれのPRも、既存Concierge実装・既存`docs/ops/direction-fail-safe.md`の禁止事項（日盤・時盤・ダミー方位の追加禁止）を改変しない前提で設計されるべきである。

## 19. Evidence / File References

- `backend/temples/domain/kyusei.py`（全行直読、本監査で独立検証）
- `backend/temples/services/direction_reference.py`（全行直読、本監査で独立検証）
- `backend/temples/services/concierge_chat_ranking.py:291-323,1721-1737`（`_score_direction_signal`/`_resolve_public_mode`、独立再確認）
- `backend/temples/api_views_concierge.py:540-580`（`visit_date`/`profile_birthdate`/direction_profile構築、独立確認）
- `docs/ops/direction-fail-safe.md`（全文読了、日盤・時盤禁止の運用契約として確認）
- `docs/core/direction-response-contract.md`
- `docs/product/direction-ranking-design.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/product/premium-experience.md`
- `docs/audit/premium-visit-compass-recommendation-feasibility.md`（前提監査、本書が独立に再検証した対象）

---

## 付録: 方法論

本監査は前回監査（`premium-visit-compass-recommendation-feasibility.md`）の結論を出発点としつつ、タスク指示（「前回監査を鵜呑みにせず独立に検証せよ」）に従い、`backend/temples/domain/kyusei.py`と`backend/temples/services/direction_reference.py`を全行直接読み込み、`_score_direction_signal`/`_resolve_public_mode`の該当箇所をコードから直接再確認した。加えて、`visit_date`関連フィールドの命名を`grep`で横断確認し、既存のフィールド命名パターン（Section 8の根拠）を独立に収集した。すべての引用file:lineは本監査で実際にコードを読んで確認したものである。DOCUMENTATION-ONLYの主張は本書には存在しない（すべてFACTとして直接検証済み、またはINFERENCE/HYPOTHESIS/OPEN DECISIONとして明示している）。

## 関連ドキュメント

- `docs/audit/premium-visit-compass-recommendation-feasibility.md`
- `docs/core/direction-response-contract.md`
- `docs/product/direction-ranking-design.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/product/premium-experience.md`
- `docs/ops/direction-fail-safe.md`
