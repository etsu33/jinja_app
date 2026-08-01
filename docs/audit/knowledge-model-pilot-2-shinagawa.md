# Knowledge Model Pilot #2 Audit - 品川神社

## 1. 目的

Knowledge Model Foundationで導入した以下の構造が、実在する神社の公開情報を用いた場合でも成立するかを検証する。

- ShrineDeityによる祭神の複数Relation
- ShrineHistoryによる歴史Factの分離
- Sourceと各FactのRelation
- verification_status / confidenceによる検証状態管理
- Django Adminからの登録・編集
- 保存後のSource Relation保持

本Pilotでは品川神社を対象とし、複数Source間の情報粒度の違いを、Fact単位で保持できるかを重点的に確認した。

---

## 2. 検証対象

### Shrine

- 品川神社

### 検証対象データ

- 祭神
- 創始
- 歴史上の祭神奉祀
- Source Relation
- verification_status
- confidence

---

## 3. 検証Source

本Pilotでは以下のSourceを使用した。

### 品川神社公式

品川神社公式サイトに掲載されている「御祭神・御由緒」の情報を参照した。

主に以下の情報を確認した。

- 御祭神
- 文治3年（1187年）の創始
- 元応元年（1319年）の宇賀之売命奉祀
- 文明10年（1478年）の素盞嗚尊奉祀

### 東京都神社庁

東京都神社庁に掲載されている品川神社の情報を参照した。

主に以下の情報を確認した。

- 御祭神
- 文治3年（1187年）の創始・由緒

### Source運用方針

Sourceは神社単位で一括して紐付けるのではなく、各Factが実際に確認できたSourceのみRelationする。

そのため、同一神社について複数Sourceを登録していても、すべてのFactへ一律にRelationしない。

---

## 4. ShrineDeity Relation検証

品川神社の祭神として以下3柱を登録した。

| sort_order | display_name | role | verification_status | confidence |
| --- | --- | --- | --- | --- |
| 0 | 天比理乃咩命 | enshrined | source_confirmed | high |
| 1 | 宇賀之売命 | enshrined | source_confirmed | high |
| 2 | 素盞嗚尊 | enshrined | source_confirmed | high |

3柱を独立したShrineDeity Relationとして保持できることを確認した。

また、各Relationに対してSourceを複数選択でき、保存後の再編集画面でも選択状態が保持されることを確認した。

### 結果

PASS

複数祭神を単一テキストとして保持するのではなく、個別Relationとして管理できることを実データで確認した。

---

## 5. ShrineHistory Fact検証

### 5.1 文治3年（1187年）の創始

#### 登録内容

- Shrine: 品川神社
- History type: `founding`
- Title: `文治3年（1187年）の創始`
- Sort order: `0`
- Verification status: `source_confirmed`
- Confidence: `high`

#### Content

源頼朝公が安房国の洲崎明神から天比理乃咩命を当地に迎え、海上交通安全と祈願成就を祈ったことを創始とする。

#### Sources

- 品川神社公式
- 東京都神社庁

#### Relation QA

保存後に再編集画面を開き、2 Sourceがともに選択状態で保持されていることを確認した。

#### 結果

PASS

1187年の創始Factについて、2つの独立したSourceを1つのFactへRelationできた。

---

### 5.2 元応元年（1319年）の宇賀之売命奉祀

#### 登録内容

- Shrine: 品川神社
- History type: `historical_event`
- Title: `元応元年（1319年）の宇賀之売命奉祀`
- Sort order: `1`
- Verification status: `source_confirmed`
- Confidence: `high`

#### Content

二階堂道蘊公が宇賀之売命を祀った。

#### Sources

- 品川神社公式

#### Source比較結果

今回確認した東京都神社庁の品川神社ページでは、1319年の宇賀之売命奉祀に相当するFactを確認できなかった。

したがって、東京都神社庁SourceをこのFactへRelationせず、品川神社公式のみをRelationした。

これはSource間の「明確な不一致」とは扱わず、**情報粒度・掲載範囲の差**として扱う。

#### Relation QA

保存後に再編集画面を開き、

- 品川神社公式：選択状態
- 東京都神社庁：非選択状態

が保持されていることを確認した。

#### 結果

PASS

同一神社のSourceであっても、Factを確認できないSourceをRelationせずに保持できることを確認した。

---

### 5.3 文明10年（1478年）の素盞嗚尊奉祀

#### 登録内容

- Shrine: 品川神社
- History type: `historical_event`
- Title: `文明10年（1478年）の素盞嗚尊奉祀`
- Sort order: `2`
- Verification status: `source_confirmed`
- Confidence: `high`

#### Content

太田道灌公が素盞嗚尊を祀った。

#### Sources

- 品川神社公式

#### Source比較結果

今回確認した東京都神社庁の品川神社ページでは、1478年の素盞嗚尊奉祀に相当するFactを確認できなかった。

そのため、東京都神社庁SourceはRelationせず、品川神社公式のみをRelationした。

1319年と同様、これはSource間の「明確な不一致」ではなく、**情報粒度・掲載範囲の差**として扱う。

#### Relation QA

保存後に再編集画面を開き、

- 品川神社公式：選択状態
- 東京都神社庁：非選択状態

が保持されていることを確認した。

#### 結果

PASS

---

## 6. Source差異の分類

今回確認したSource差異を以下の4分類で整理した。

| 分類 | 判定 | 内容 |
| --- | --- | --- |
| 一致 | あり | 1187年の創始など、両Sourceで対応するFactを確認できた |
| 追加情報 | あり | 品川神社公式では1319年・1478年の歴史Factを確認できた |
| 表現差 | あり | 1187年の由緒についてSourceごとに説明粒度・表現が異なる |
| 明確な不一致 | 今回は確認せず | 相互に両立しないFactは今回の検証範囲では確認していない |

### 判断

「Source Bに書かれていない」ことと「Source BがSource Aを否定している」ことは分離する必要がある。

今回の1319年・1478年は前者であり、明確な不一致として扱わない。

---

## 7. History Type分類検証

今回の実データから以下の分類を使用した。

### `founding`

神社の創始そのものを表すFact。

今回：

- 文治3年（1187年）の創始

### `historical_event`

創始後に発生した、時系列上独立して扱える歴史Fact。

今回：

- 元応元年（1319年）の宇賀之売命奉祀
- 文明10年（1478年）の素盞嗚尊奉祀

### `official_origin`

今回の品川神社Factでは使用していない。

Pilot #2の範囲では、1187年を`founding`として扱い、創始後の奉祀を`historical_event`として分離する構造で矛盾は確認されなかった。

### `tradition`

今回の登録対象Factでは使用していない。

伝承・伝説等と、歴史上の出来事としてSourceが記述しているFactとの境界については、別Pilotで追加検証が必要。

---

## 8. Source Relation QA

今回以下を確認した。

| Fact / Relation | Source | 保存後保持 |
| --- | --- | --- |
| ShrineDeity: 天比理乃咩命 | 複数Source | PASS |
| ShrineDeity: 宇賀之売命 | 複数Source | PASS |
| ShrineDeity: 素盞嗚尊 | 複数Source | PASS |
| 1187年 founding | 品川神社公式 + 東京都神社庁 | PASS |
| 1319年 historical_event | 品川神社公式のみ | PASS |
| 1478年 historical_event | 品川神社公式のみ | PASS |

Django AdminでRelationを設定後、再編集画面を開いてもSource選択状態が保持されることを確認した。

---

## 9. Pilot #2で確認できたこと

Pilot #2では以下を実データで確認した。

1. 複数祭神を独立Relationとして保持できる
2. ShrineHistoryをFact単位で分割できる
3. 創始と創始後の歴史Factを分離できる
4. 1 Factに複数SourceをRelationできる
5. Sourceに存在しないFactへSourceを無理にRelationする必要がない
6. Sourceごとの情報粒度の違いをRelation構造で表現できる
7. Django AdminでRelationを設定・保存できる
8. 再編集後もRelationが保持される
9. verification_status / confidenceをFact単位で保持できる

特に重要なのは、Sourceを「神社全体の出典」として扱うのではなく、**Fact単位の根拠としてRelationできたこと**である。

---

## 10. Admin UXで確認した改善候補

Pilot #2のAdmin操作中に、以下の改善候補を確認した。

- ShrineDeity / ShrineHistoryのSources選択候補には、対象Shrineと直接関係しないShrineKnowledgeSourceも表示される
- 現行のShrineKnowledgeSourceはShrineへの直接Relationを持たないため、Admin上では他神社向けSourceも選択候補となる
- StandaloneのShrineDeity / ShrineHistory AdminではSources Relationを設定・再編集できる
- Shrine AdminのInlineではDeity / History自体の追加・編集はできるが、Sources Relationの追加操作はできない
- 現状はSourceを手動で識別して選択する必要があり、Source数増加時には他神社Sourceの誤選択リスクが高まる可能性がある

本Pilotでは正しいSourceを選択してRelationを保存できたためBlockingとはしない。

Admin上のSource候補絞り込み、InlineでのSource編集、cross-shrine Source選択時のValidationについては、Knowledge Modelのデータ構造とは分離して後続のAdmin UX改善候補として扱う。

## 11. 未検証事項

Pilot #2では以下は未検証とする。

- Source同士が明確に矛盾するケース
- `tradition`に分類すべき伝承Fact
- `official_origin`と`founding`の境界が曖昧なケース
- 年代が推定・不明確なFact
- `period_text`を必要とするFact
- `event_date`を確定日として保持できるFact
- low / medium confidenceを必要とするFact
- 多数のSourceが存在する場合の運用
- 大量のShrineHistoryを持つ神社でのAdmin操作性
- 推薦ロジック・Serializer・APIからの利用方法

これらは後続Pilotで検証する。

---

## 12. 結論

Pilot #2 品川神社では、Knowledge Model Foundationの主要目的である、

**「神社情報を大きな説明文として保存するのではなく、Factを分離し、それぞれのFactに根拠SourceをRelationする」**

という構造が実データでも成立することを確認した。

特に1319年・1478年では、品川神社公式には存在するが東京都神社庁では今回確認できなかった情報を、Source Relationを分離することで無理なく表現できた。

したがってPilot #2の範囲では、

- ShrineDeity Relation
- ShrineHistory Fact分離
- Source Relation
- verification_status
- confidence
- Django AdminでのRelation保持

についてPASSとする。

ただし、Source間の明確な矛盾、伝承、推定年代等については未検証であり、Knowledge Model全体の妥当性を本Pilotのみで確定するものではない。
