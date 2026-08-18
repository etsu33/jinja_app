> **Status: Audit → Polish PR（本ドキュメント内でPolish READY判定に基づき実装まで実施）**
>
> `docs/audit/compass-full-experience-qa.md`（Phase 6, PR #2480）が記録した唯一の残存P2「目的チップ15個が375pxで初回ビューポートを支配する」の原因を調査し、最小の提示方法変更を決定・実装したドキュメント。Product/Runtime Contractの変更、purpose taxonomyの変更、Recommendationマッピングの変更は一切含まない。

# Compass Purpose UX / First View Polish Audit

## 1. 調査対象の再定義

問題は「Compassに15の目的がある」ことではない。問題は「15個を常に同じ視覚的重みで一度に提示することが、不要な認知負荷と縦方向の圧迫を生んでいるか」である。`compass-full-experience-qa.md` Section 5/7/9で実測済みの通り、375pxでは目的チップが5行にわたり、出発地点・生年月日・CTAへ到達するまでに複数回のスクロールを要していた（430pxでは4行に緩和）。

## 2. Source of Truth

`docs/product/compass-product-contract.md`・`docs/product/compass-mvp-runtime-contract.md`・`docs/audit/compass-full-experience-qa.md`・現行`apps/web/src/features/compass/`実装・`backend/temples/domain/need_tags.py`のtaxonomyを一次情報として使用した。Taxonomy自体は再定義していない。

## 3. Current Purpose Inventory

`apps/web/src/features/compass/compassPurposes.ts`が実際にレンダリングする15値を、`backend/temples/domain/need_tags.py`（`NEED_TAGS`・`NEED_PRIORITY`・`NEED_KEYWORDS`）、`backend/temples/domain/need_to_goriyaku_tag_ids.py`（`NEED_TO_GORIYAKU_IDS`）、`backend/temples/services/concierge_chat_ranking.py`（`NEED_TEXT_WEIGHTS`）を突き合わせて調査した。

| slug | 表示ラベル | need_tag本来の意味 | Recommendationでの実際の使われ方 | 他の可視purposeとの重複 | 広い意図 / 狭い意図 |
|---|---|---|---|---|---|
| love | 恋愛 | 恋愛成就・復縁等 | goriyaku_tag_ids一致 + text weight（"恋愛"等9語） | marriageと`goriyaku_tag_ids`が一部重複（{1,29}が共通） | 広い |
| relationship | 人間関係 | 職場・家族・友人関係全般 | goriyaku_tag_ids一致のみ（text weightなし） | familyと`{27,34}`が重複、marriageと`{1}`が重複 | 広い |
| marriage | 縁結び・結婚 | 結婚・良縁 | goriyaku_tag_ids一致のみ（text weightなし） | loveと`{1,29}`、relationshipと`{27}`が重複 | やや狭い（loveの下位集合的） |
| communication | 対話・発信 | 会話・営業・プレゼン | goriyaku_tag_ids一致のみ（text weightなし） | careerと`{30}`、studyと`{39}`が重複 | 狭い |
| career | 転機・仕事 | 転職・独立・キャリア | goriyaku_tag_ids一致 + text weight（"転職"等10語） | communication/courageと`{30}`が重複 | 広い |
| money | 金運 | 収入・商売繁盛 | goriyaku_tag_ids一致 + text weight（"金運"等9語） | 他purposeとgoriyaku重複なし | 広い |
| study | 学業・合格 | 受験・資格 | goriyaku_tag_ids一致 + text weight（"合格祈願"等8語） | **focusと`goriyaku_tag_ids`が完全一致`{3,4,39}`** | 狭い（明確） |
| health | 健康 | 体調・病気平癒 | goriyaku_tag_ids一致のみ（text weightなし） | **restと`goriyaku_tag_ids`が`{7,8,44,45}`⊂`{7,8,43,44,45}`でほぼ一致** | 広い |
| mental | 不安・心 | 不安・ストレス | goriyaku_tag_ids一致 + text weight（"厄除"等9語） | protectionと`goriyaku_tag_ids`が5/6一致 | 広い |
| protection | 厄除け・守り | 厄除け・お祓い | goriyaku_tag_ids一致のみ（text weightなし） | mentalと`goriyaku_tag_ids`が5/6一致 | 広い（NEED_PRIORITY最上位） |
| courage | 前進・後押し | 決断・開運・挑戦 | goriyaku_tag_ids一致 + text weight（"開運"等8語） | career/communication/mentalと一部`goriyaku_tag_ids`重複 | 広い |
| focus | 集中・継続 | 集中力・習慣 | goriyaku_tag_ids一致のみ（text weightなし） | **studyと`goriyaku_tag_ids`が完全一致** | 狭い（明確） |
| rest | 休息 | 休息・リセット | goriyaku_tag_ids一致 + text weight（"休息"等10語） | healthとほぼ一致（上記） | 広い |
| family | 子宝・家族 | 子宝・安産・育児 | goriyaku_tag_ids一致のみ（text weightなし） | relationshipと`{27,34}`が重複 | 狭い（明確） |
| travel_safe | 移動・安全 | 交通安全・旅行安全 | goriyaku_tag_ids一致のみ（text weightなし） | 他purposeとgoriyaku重複なし | 狭い（明確） |

**事実として記録するが本フェーズでは変更しない発見**:
- `study`と`focus`は`goriyaku_tag_ids`が完全一致（`{3,4,39}`）かつ両方とも`NEED_TEXT_WEIGHTS`に`focus`のエントリが存在しないため、Recommendationスコアリング上ほぼ区別できない状態にある。
- `health`と`rest`も`goriyaku_tag_ids`がほぼ一致している。
- 15個中7個（`relationship`/`marriage`/`communication`/`health`/`protection`/`focus`/`family`）は`NEED_TEXT_WEIGHTS`にエントリが無く、goriyaku一致のみでスコアリングされる。

これらはTaxonomy自体の課題であり、Section 10の指示に従い**変更はしない**。別途Product判断が必要な項目として記録するに留める。

## 4. Presentation Options比較

| # | 名称 | 概要 | 375px初回高さへの効果 | 実装コスト | 既存パターンとの整合 |
|---|---|---|---|---|---|
| A | ALL VISIBLE（現行） | 15個を常に全表示 | 悪化（5行） | ゼロ | - |
| B | PRIMARY + MORE | 上位N個を初期表示、「その他の目的を見る」で残りを展開 | 改善（2〜3行→クリックで復元） | 最小（トグル1つ） | **`ConciergeEntryCard.tsx`の`INITIAL_VISIBLE_EXAMPLES`パターンと同一構造**（`showAllExamples`/`aria-expanded`/「ほかのテーマも見る（他N件）」文言） |
| C | COMPACT SELECT / SHEET | チップの代わりに1行の要約＋Sheetで全15個を選択 | 最良（1行） | 中（新規Sheet導線、`CompassOriginSummary`と同型のパターンをもう1つ追加） | 既存`Sheet`は再利用可能だが、目的選択のような主要な最初の入力をSheet裏に隠すのは「最初の相互作用が不明瞭」になりやすい |
| D | GROUPED PRESENTATION | 意味カテゴリ（例:「関係」「仕事・お金」「こころ」等）で見出し分けして表示 | 改善は限定的（見出し分だけ縦に伸びる） | 中〜高（カテゴリ分類という新しい提示上の判断が必要、Section 3の重複関係を踏まえた分類が難しい） | 新しい視覚パターンを追加することになり、既存コンポーネントの直接再利用ができない |

### 評価基準ごとの比較

| 基準 | A | B | C | D |
|---|---|---|---|---|
| 1. 375px初回高さ | 悪い | 良い | 最良 | 中 |
| 2. 認知負荷 | 高い（15個同時） | 低い（6個+展開） | 最低（1行、ただし1タップ追加） | 中（カテゴリ理解が追加で必要） |
| 3. 選択速度（よくある目的） | 普通 | **速い**（上位6個に主要な広い意図を配置） | 遅い（Sheetを開く1手間） | 普通 |
| 4. 15個全ての発見可能性 | 保証済み | 保証済み（1タップで展開、非表示ではない） | 保証済み（Sheet内） | 保証済み |
| 5. 選択状態の明確さ | 明確（emerald塗り） | 明確（同じ視覚言語を維持） | Sheetを閉じた後の要約表示に依存 | 明確 |
| 6. アクセシビリティ | 良好（`role=radio`） | 良好（`aria-expanded`追加のみ、`radiogroup`の意味は不変） | Sheet内フォーカストラップの追加考慮が必要 | 良好 |
| 7. 既存UIとの整合 | 現行そのもの | **最も整合**（ConciergeEntryCardと同一パターン） | 部分的整合（Sheetは既出だが目的選択への適用は新規） | 整合性なし（新規パターン） |
| 8. 実装複雑度 | ゼロ | **最小** | 中 | 中〜高 |
| 9. Recommendation意味変更リスク | ゼロ | ゼロ（表示順序のみ、値は不変） | ゼロ | カテゴリ分類の恣意性がRecommendation外だが誤解を招くリスク | 
| 10. 将来の保守性 | 変更不要だが問題継続 | 高い（`NEED_PRIORITY`という既存の順序情報をそのまま再利用） | 中（Sheet内リストの保守） | 低い（カテゴリ定義を独自に保守する必要） |

**結論**: Bが小ささ・リスク・既存パターン整合のすべてで最も優れる。Cは「最初の相互作用」を隠しすぎる懸念があり、Dは新しい分類判断（taxonomy変更ではないが、独自のグルーピングという新しい提示上の決定）を必要とする点でSection 10の精神（本フェーズはpresentation architectureのみ）から見て過剰。

## 5. 評価criteria（詳細）は Section 4 の表に統合済み。

## 6. First View Contract

375pxの初回ビューポートで理解できるべきこと（Runtime要件と対比）:

- 「今月の参拝コンパス」であること — **既存で満たす**（現行のまま変更不要）
- Product Promise一文 — **既存で満たす**
- 最初にすべき行動（目的を選ぶこと） — **現行でも見出しから読み取れるが、15個が並ぶことで「まず何をすればいいか」より「何個あるのか」が先に目に入ってしまう**
- 明確な主要インタラクション — 現行では「目的を選ぶ」という単一アクションが、15個の等価な選択肢によって埋没している

15個全てを即座に見せる必要は無い（Runtime要件ではなく提示方法の問題）。Option Bにより、初回ビューポートで「まず6個の代表的な目的から選べる」ことが視覚的に明確になり、「もっと選びたければ展開できる」という発見可能性も保たれる。

## 7. Input Sequence Review

現行順序: purpose → origin → birthdate → CTA。

- **purposeを最初に置くことは妥当** — Conciergeが相談内容から始まるのと対になる、Compassの「目的」という最初の意思表示として自然。変更不要。
- **originを2番目に置くことも妥当** — 3つのRuntime必須入力の中で順序自体に正誤は無いが、目的（何をしたいか）の次に場所（どこから）を聞く流れは自然。変更不要。
- **birthdateの説明文は既に簡潔**（「生年月日（方位計算に使用）」1行）。これ以上の圧縮は理解を損なうリスクの方が大きいため変更しない。
- **progressive disclosureが必要なのはpurposeのみ**。origin・birthdateは各1コントロールで既に軽量（`compass-full-experience-qa.md` Section 9/10で確認済み）。

「Runtimeが要求すること」と「常に画面に出続けなければならないこと」は別である、というSection 7の指摘はpurposeにのみ当てはまる。origin/birthdateは既に最小構成のため対象外とした。

## 8. World-View Requirement

Option Bは新しいトークン・新しい色・新しいアニメーション・zodiac/fortune-telling的要素を一切導入しない。使用する視覚要素はすべて既存チップスタイル（`--kt-radius-pill`・`--kt-color-action-primary`等）とテキストリンク（`ConciergeEntryCard.tsx`と同一クラス構成）のみであり、`VISUAL LANGUAGE ALIGNED`判定を損なわない。

## 9. Purpose / Direction Causality

Option Bは表示順序・表示件数のみを変更し、`onChange(purpose)`のシグナルパス自体には触れない。方向計算（`CompassDirectionRuntime`）とpurposeの独立性は現行実装のまま維持される。「仕事運の方角」等、purposeが方向を決めるかのような新しいコピーは追加しない。

## 10. No Taxonomy Change

`COMPASS_PURPOSES`・`COMPASS_PURPOSE_LABELS_JA`の値・キー・意味はいずれも変更しない。追加するのは「初期表示する6件」を選ぶための**表示専用の並び替え**のみであり、その並び替えも新しい判断基準を発明せず、既存`backend/temples/domain/need_tags.py`の`NEED_PRIORITY`（Concierge側で既に使われている優先順位リスト）をそのまま踏襲する。`NEED_PRIORITY`の上位6件は: `protection, marriage, love, family, study, career`。

Section 3で発見した`study`/`focus`の重複、`health`/`rest`の重複はtaxonomy自体の課題であり、本フェーズでは変更しない（Open Issuesとして記録、Section 15相当）。

## 11. Mobile Comparison（現行 vs 実装後）

実装後、375px/390px/430pxで実ブラウザ確認した結果は本ドキュメントSection 15（Full Experience Recheck）に記録する。ここでは実装前の基準値（`compass-full-experience-qa.md`からの引用）のみ記す。

| 指標 | 現行（A） | Option B想定 |
|---|---|---|
| 初回表示チップ行数（375px） | 5行（15個） | 2行（6個）+ トグルリンク1行 |
| CTA到達までのスクロール | 複数回 | 大幅減少（想定） |
| 15個全ての発見可能性 | 常時可視 | トグル1タップで全展開、非表示ではない |

## 12. Implementation Decision

**PURPOSE UI POLISH READY**

理由: Option Bが評価基準の大半で最良、実装リスクが最小（表示順序とトグル状態のみ）、Recommendation・Runtimeへの影響がゼロ、既存パターン（`ConciergeEntryCard.tsx`のexpand/collapseチップ）をそのまま踏襲でき新しい視覚言語を発明しない。

**最小実装PRの定義**:

- `apps/web/src/features/compass/compassPurposes.ts`: `NEED_PRIORITY`相当の順序で`COMPASS_PURPOSES`を並び替えた新しい定数（例: `COMPASS_PURPOSES_ORDERED`）を追加、または既存配列の並び順自体を`NEED_PRIORITY`準拠に変更（値集合は不変）。上位6件を「primary」として区別できる情報を追加。
- `apps/web/src/features/compass/components/CompassPurposeSelector.tsx`: 初期表示を上位6件に絞り、`ConciergeEntryCard.tsx`と同型の「その他の目的を見る（他9件）」／「目的を閉じる」トグルボタンを追加。`role="radiogroup"`・`aria-checked`はそのまま維持。折りたたみ時も選択済みの値（仮に9件側にあっても）は保持される。
- テストの追加・更新（Section 14参照）。
- バックエンド・API・DB・Migration・Recommendation・Compass Runtimeへの変更は無し。

## 13. Implementation Boundary

変更は`apps/web/src/features/compass/`配下のみに限定する。既存共有コンポーネント（`DetailSection`・`Sheet`・`ShrineCardCompact`・`OriginSelector`）は一切変更しない。新規共有コンポーネントも追加しない（`ConciergeEntryCard.tsx`のパターンをCompass内にローカル実装として再現するのみで、共通コンポーネント化は本フェーズのスコープ外）。

## 14. Test Requirements（実装後に追加したテストで担保）

- 15個すべてが（折りたたみ状態を問わず、展開すれば）選択可能であること
- 選択したpurposeの値（slug）が折りたたみ/展開状態に関わらず不変であること
- 折りたたみ→展開、展開→折りたたみの状態遷移
- 展開前から選択されていた場合の表示（该当なし、初期状態は常に折りたたみ）
- 9件側（展開後のみ見える範囲）の目的を選んだ場合も`onChange`が正しい値で呼ばれること
- アクセシビリティ: `aria-expanded`の値、トグル後も`role="radiogroup"`とその子`role="radio"`の構造が保たれること
- キーボード操作: トグルボタン・チップがフォーカス可能でEnter/Spaceで操作できること（既存チップの延長のため新規のキーボードハンドラは追加しない）
- 既存の送信フロー（`CompassClient`のバリデーション・API呼び出し）が影響を受けないこと
- **Recommendationペイロード不変の回帰確認**: `CompassClient`が`fetch`へ送るbodyの`purpose`フィールドが、表示上折りたたまれているか展開されているかに関わらず、選択した値そのものであること

## 15. Full Experience Recheck

実装後、375px/390px/430pxで実機確認し、初回ビューポート・目的選択・完全な成功フロー・方向結果・Recommendation・Shrine Detail遷移を再検証した。結果は本PRのコミット本文および最終回答に記載する。

## 16. Open Issues（taxonomy関連、本フェーズでは対応しない）

- `study`と`focus`の`goriyaku_tag_ids`完全一致によるRecommendationスコアリング上の無区別。
- `health`と`rest`の`goriyaku_tag_ids`ほぼ一致。
- 15個中7個に`NEED_TEXT_WEIGHTS`が存在しない非対称性。

これらはCompass固有の問題ではなく、Concierge側とも共有される既存taxonomyの特性であり、別途Product判断のもとで扱うべき事項として記録する。
