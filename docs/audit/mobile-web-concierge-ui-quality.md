# Mobile / Web Concierge UI 品質監査

## 目的

Web と Mobile のコンシェルジュ結果表示を比較し、推薦理由・行動提案・根拠表示の差分を明確にする。

この監査では、UIの好みではなく、以下の品質観点で差分を確認する。

- ユーザーが「なぜこの神社なのか」を理解できるか
- 表示文言が事実・解釈・提案に分かれているか
- 神社固有情報が推薦理由に反映されているか
- 行動提案が相談内容と神社情報に接続しているか
- Web と Mobile で同じ推薦品質を維持できているか

## 背景

Recommendation Reason v4 では、以下の品質指標を追加した。

- `shrine_data_rate`
- `consultation_reflection_rate`
- `evidence_rate`
- `action_grounding_rate`
- `fallback_reason_rate`
- `is_ai_inference_only`

Web側では `recommendation_quality` イベントとして PostHog へ送信できる状態になっている。

一方で、Mobile UI と Web UI の見え方・文言・並びが大きく異なっており、ユーザー体験としては推薦の説得力が落ちている可能性がある。

そのため、次の実装に入る前に、表示品質の監査を行う。

## 監査対象

### Web

主な確認対象候補：

- `apps/web/src/app/concierge/ConciergeClientFull.tsx`
- `apps/web/src/features/concierge/buildPayloadFromUnified.ts`
- `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`
- `apps/web/src/features/concierge/components/ConciergeTopRecommendationHero.tsx`
- `apps/web/src/lib/api/concierge/types.ts`
- `apps/web/src/lib/api/concierge/normalize.ts`

### Mobile

主な確認対象候補：

- `apps/mobile/app/concierge`
- `apps/mobile/app/shrines`
- `apps/mobile/components`
- `apps/mobile/components/services`
- `apps/mobile/lib`
- `apps/mobile/types`

実際のファイルは以下で確認する。

```bash
find apps/mobile/app apps/mobile/components apps/mobile/lib apps/mobile/types -path "*concierge*" -o -path "*shrine*" | sort | head -160
```

## 監査観点

### 1. 表示項目差分

Web と Mobile で、以下の項目が同じ粒度で表示されているか確認する。

- 神社名
- 推薦順位
- 推薦理由
- 神社固有情報
- ご利益
- 相談内容の反映
- 行動提案
- 参拝前の問い
- 保存導線
- 詳細遷移導線
- ルート導線
- premium preview / paywall 導線

### 2. 文言差分

以下を比較する。

- Web と Mobile で推薦理由の表現が一致しているか
- Mobile だけ抽象表現が強くなっていないか
- 「寄り添う」「後押しする」など、根拠の薄い文言に寄っていないか
- 神社固有情報より雰囲気コピーが前面に出ていないか
- 行動提案が毎回同じ文言になっていないか

### 3. 表示順の差分

推薦結果の説得力に直結するため、表示順を確認する。

推奨する基本順序：

1. 相談内容の要約
2. 推薦された神社
3. 神社固有の根拠
4. 相談内容との接続
5. 次に取りやすい行動
6. 参拝前の問い
7. 保存・詳細・ルート導線

### 4. 事実 / 解釈 / 提案の分離

以下が混ざっていないか確認する。

| 種別 | 内容 | 例 |
|---|---|---|
| 事実 | DB由来の神社情報 | 祭神、由緒、場所、ご利益 |
| 解釈 | 相談内容との接続 | 仕事の迷いに対し、整理・決断の文脈で合う |
| 提案 | 次の行動 | 詳細を見る、保存する、問いを持って参拝する |

### 5. 神社固有情報の薄さ

以下の状態を抽出する。

- どの神社でも使えそうな文になっている
- `history_theme` の抽象ラベルだけで説明している
- deity / shrine_history / place_context が表示に出ていない
- ご利益だけで推薦理由を作っている
- ユーザーの相談内容との接続が弱い

### 6. Mobile側の古いロジック確認

Mobileが以下を使っていないか確認する。

- 古い `reason`
- 古い `explanation`
- 古い `action_suggestion`
- Web側で使っている `recommendation_reason_v4` / `action_suggestion_v4_preview` を受け取っていない箇所
- `recommendation_reason_quality` を型として保持していない箇所

## 比較表

| 観点 | Web | Mobile | 差分 | 修正優先度 |
|---|---|---|---|---|
| 相談内容の要約 | 相談内容サマリーを上部表示し、相談→推薦の流れを構成 | 相談内容は表示するが、推薦との接続が弱い | Mobileは相談内容が推薦理由へ十分につながって見えない | 中 |
| 神社固有情報 | trustMetadata・historyTheme・神社の文脈を段階的に表示 | 神社名・地域中心で、固有情報の露出が少ない | Mobileは神社固有情報による説得力が不足 | 高 |
| 推薦理由 | reasonVm / reasonFacts 起点 | reason fallback 起点 | Mobileは抽象fallbackが強い | 高 |
| 行動提案 | action_suggestion_v4_preview 表示 + click計測 | action_suggestion_v4_preview 表示のみ | Mobileは計測・CTAが弱い | 中 |
| 参拝前の問い | 未確認 | 未確認 | 未確認 | 未定 |
| 保存導線 | 未確認 | 未確認 | 未確認 | 未定 |
| 詳細導線 | 未確認 | 未確認 | 未確認 | 未定 |
| ルート導線 | 未確認 | 未確認 | 未確認 | 未定 |
| 根拠表示 | 未確認 | 未確認 | 未確認 | 未定 |
| premium導線 | 未確認 | 未確認 | 未確認 | 未定 |
| 神社詳細 | Concierge文脈をthreadから参照 | shrine単体API + fallback | Mobileは相談文脈が詳細に引き継がれていない可能性 | 高 |
| 比較条件 | Local Mobileはlocalhost backend | Web本番はproduction backend | backend/DB/匿名IDが異なるため、推薦内容の直接比較は不可 | 高 |
| 表示密度 | Mobileは1カードに情報が集中 | Webはカード＋補助セクションで分割 | Mobileは文脈・根拠・提案が詰まりやすい | 中 |
| 推薦内容 | MobileとWebで候補神社が一致しない | 同一入力でも環境差で結果が変わる | UI比較前にpayload条件を揃える必要あり | 高 |
| 送信payload | Webはquery中心の可能性 | MobileはextraCondition / birthdate / profileContextを常時構築 | 同一入力でも推薦結果が変わる可能性 | 高 |
| 条件レイヤー | Webは補助条件を後付け | Mobileは画面内条件をpayloadへ混ぜる | UI比較前に送信条件を揃える必要あり | 高 |
| profile_context | Web側は要確認 | MobileはuserProfile / derivedProfile / directionProfileを送信 | 占術・方位系シグナルが推薦に影響する可能性 | 中 |

### 責務整理（監査結果）

今回の監査で、WebとMobileは同じ役割ではなく、責務が異なることが分かった。

| 領域 | 正本 | 理由 | Mobileの役割 |
|---|---|---|---|
| 検索・推薦エンジン | Backend / Web | 推薦アルゴリズム・Score・検索品質を管理するため | 推薦結果を表示する |
| 相談解釈 | Backend / Web | Recommendation v4・相談解釈・品質改善を集約するため | 解釈結果を体験として見せる |
| 推薦理由 | Backend / Web | recommendation_reason_v4・reasonFacts・品質指標を管理するため | 分かりやすく表示する |
| 行動提案 | Backend / Web | action_suggestion_v4 による行動設計を管理するため | CTA・導線として見せる |
| 条件レイヤー | Mobile | UXとして入力しやすい構成になっているため | 条件入力・再提案体験を提供する |
| 誕生日・参拝スタイル | Mobile | KAMI MUSUBI独自の個人化体験を構成するため | 条件入力として保持する |
| 九星・五行・ライフパス・方位 | Mobile | 意味レイヤーを補助するシグナルとして扱うため | 補助情報・補助シグナルとして扱う |
| 表示UI | Mobile | モバイル体験として最適化するため | Web品質を維持しつつ情報を圧縮する |

## 修正方針案

### 方針A: Webを正本にしてMobileを追従

Web側の表示構造を正本とし、Mobileは同じ payload / 同じ表示順 / 同じ文言思想に寄せる。

メリット：

- Webで検証済みの品質をMobileへ展開できる
- 表示仕様の二重管理を減らせる
- analyticsとの整合性を取りやすい

注意点：

- Mobileの画面サイズに合わせて情報量を圧縮する必要がある
- そのまま移植すると重くなる可能性がある

### 方針B: Mobile専用の表示ルールを作る

Mobile向けに短く、順序を再設計する。

メリット：

- 画面体験は作りやすい
- モバイルファーストの導線にできる

注意点：

- WebとMobileで品質差が出やすい
- 文言・ロジックが二重化しやすい
- 推薦根拠が薄くなる危険がある

### 暫定判断

まずは **方針A: Webを正本にしてMobileを追従** を優先する。

ただし、Mobileでは以下のように情報を圧縮する。

1. 相談内容の要約
2. 神社固有根拠を1〜2行
3. 相談との接続を1行
4. 次の行動を1つ
5. 詳細で補足表示

## 次PR候補

監査後、次のPRでは実装対象を1つに絞る。

候補：

1. Mobileコンシェルジュ結果カードの表示順修正
2. Mobile推薦理由の文言を Web reason_v4 に寄せる
3. Mobile行動提案を action_suggestion_v4_preview に寄せる
4. Mobileに recommendation_reason_quality 型を追加
5. MobileとWebの共通表示モデルを整理

## TODO

```markdown
# Setup
- [x] develop最新化
- [x] audit/mobile-web-concierge-ui-quality 作成
- [x] docs/audit/mobile-web-concierge-ui-quality.md 作成

# Audit
- [x] Webのコンシェルジュ結果UIを確認
- [x] Mobileのコンシェルジュ結果UIを確認
- [x] Web / Mobile の表示項目差分を一覧化
- [x] Web / Mobile の文言差分を一覧化
- [x] Mobile localを起動
- [x] Web本番を確認
- [x] Mobile / Web のAPI向き先を確認
- [ ] 推薦理由の表示順を比較
- [ ] 行動提案の表示順を比較
- [ ] 「事実 / 推測 / 提案」が混ざっている箇所を抽出
- [ ] 神社固有情報が薄い文言を抽出
- [ ] モバイル側で古いreason/actionロジックを使っていないか確認
- [ ] 条件が推薦理由へどう反映されたかを表示する設計を整理
- [ ] recommendation_reason_v4 と条件レイヤーの接続方針を定義

# Finish
- [ ] 修正方針をdocsに記録
- [ ] 次PRの実装対象を1つに絞る
- [ ] commit
- [ ] push
- [ ] PR作成
```

## 完了条件

この監査PRの完了条件は以下。

- Web / Mobile の表示差分がdocsに記録されている
- 説得力を落としている要因が特定されている
- Mobile側の古いロジック利用有無が確認されている
- 次の実装PRが1つに絞られている

## 現時点の仮説

- MobileはWebよりも古い表示構造を使っている可能性が高い
- Mobileでは神社固有情報より抽象コピーが前面に出ている可能性がある
- 推薦理由と行動提案の接続が弱く、`action_grounding_rate` の低下に関係している可能性がある
- Webを正本にしてMobileを追従させる方が、短期的には安全

## 進捗

進捗率：87％

分析基盤は通過済み。次は表示品質・説得力・Mobile/Web整合性の監査フェーズ。


## 設計判断（条件レイヤー）

今回の監査では、Mobile側が保持している条件レイヤーについて検討した。

### 判断

- 誕生日・参拝スタイル・九星/五行/ライフパス・方位は削らない
- 推薦の主軸は相談内容と神社固有情報に置く
- 占術・方位系は推薦順位を補助するシグナルとして扱う
- MobileはKAMI MUSUBIらしい世界観を表現できている一方、推薦理由の表示は抽象fallbackに寄りやすい
- 次PRでは条件レイヤー自体を削除するのではなく、「どの条件が推薦に反映されたか」を表示側で補強する

### 理由

現在のMobileでは条件情報はpayloadに含まれているが、推薦理由の文面では条件との接続が十分に可視化されていない。

そのため、ユーザーから見ると「入力した条件が推薦に使われた」という納得感が弱くなる可能性がある。

推薦品質を高めるためには、条件入力を減らすのではなく、

- 条件
- 神社固有情報
- 相談内容

この3つの接続を推薦理由として表現することを優先する。


※ 条件レイヤーは推薦順位を補助するための入力であり、推薦理由の主役ではない。
推薦理由の中心は、相談内容と神社固有情報の接続とする。


### 補足

誕生日・参拝スタイル・九星・五行・方位などの条件は、
KAMI MUSUBI独自の「意味レイヤー」を構成する入力として保持する。

これらは推薦順位や候補の絞り込みを補助するためのシグナルであり、
単独で推薦理由を説明する根拠にはしない。

推薦理由は、

- 相談内容
- 神社固有情報
- 条件レイヤー（補助）

の順で構成する。
