> **Status: Active**
>
> 本ドキュメントは、KAMI MUSUBIの開発フェーズ、実装順序、各フェーズのゴールおよび完了条件を管理する現行ロードマップである。
>
> 個別タスク、実装履歴およびPR単位の進捗は、GitHub Issue、Pull Requestおよび関連文書を正本とする。


# KAMI MUSUBI 開発ロードマップ

## 目的

本ドキュメントは、KAMI MUSUBIの現在地、今後の開発順序、各フェーズの完了条件を定義する。

個別タスク、実装履歴、API契約、テスト項目は本書へ記載せず、GitHub Issue、Pull Request、各正本ドキュメントへ分離する。

---

## 現在地

KAMI MUSUBIは、Concierge Firstを起点として、推薦、神社詳細、経路確認、参拝、振り返りまでを接続する主要基盤を実装済みである。

現在は、完成した基盤を利用しながら、Recommendation品質、神社データ品質、Premium価値および継続利用を検証・改善する段階にある。

```text
相談
↓
推薦
↓
神社理解
↓
経路確認
↓
参拝
↓
振り返り
↓
継続利用
```

### 基盤実装済み

以下の主要基盤は実装済みである。

- Concierge First
- 相談テーマを主入力とする導線
- Explore List / Map基盤
- 神社詳細画面
- Recommendation Reason
- Action Suggestion
- Recommendation Snapshot
- Favorite / Visit / Reflectionモデル
- Visitと推薦Threadの接続
- Reflection保存
- Journey Timeline
- Behavior Funnelの基礎
- Score v3 shadow observation
- Shrine Submissionの受付・審査基盤
- Next.js BFF / JWT認証基盤
- Web / MobileのPremium導線
- Billing状態取得基盤
- Web / MobileのAnalytics送信基盤

### 基盤実装済み・検証継続

以下は基盤実装済みであるが、本番データおよび継続利用による検証を続ける。

- Premium価値の理解度
- Premium導線表示率
- Premium導線クリック率
- 課金転換率
- 継続率
- Visit登録率
- Reflection保存率
- Journey Timeline再閲覧率
- Recommendationから詳細・経路・参拝への遷移率
- Recommendation Scoreと行動結果の関係
- Web / Mobile間の主要体験差

### 現在の主フェーズ

現在の主フェーズは、Recommendation品質改善とShrine Data Qualityである。

特に以下を優先する。

- Recommendation Readinessの定義統一
- Coverageの定義統一
- Fact / Meaning / Runtime / Governanceの責務分離
- 神社固有情報を利用したRecommendation Reason
- Action / Reflectionとの一貫性
- 神社データの出典・検証・利用可能性
- Readiness条件とBackend実装の接続

PremiumおよびAnalyticsは独立した一時的フェーズとして終了させず、Recommendation品質、継続利用および収益性を確認する横断的な検証基盤として運用する。

---

## 開発原則

優先順位は以下とする。

1. 既存機能を壊さない
2. 仕様と実装を一致させる
3. ユーザー行動を計測できる状態にする
4. 継続利用につながる体験を完成させる
5. 課金機能を接続する
6. 拡張機能を追加する

以下は主役にしない。

- 地図機能単体
- 占術・方位単体
- 人気順だけの推薦
- 長い説明文だけの体験
- データ根拠のないAI解釈

---

## Phase 1: Visit Flow統合

### ゴール

推薦された神社を見て終わる状態から、実際の参拝行動へ接続する。

### 対象

- 神社詳細から経路確認への導線
- 保存状態の表示
- 参拝済み登録
- Visitと推薦Threadの接続
- Journey Timelineへの反映
- route_open / visitの計測

### 完了条件

```text
Recommendation
↓
Detail
↓
Route
↓
Visit
```

の一連の操作が、同じ神社・同じ推薦文脈として追跡できる。

---

## Phase 2: Reflection Timeline

### ゴール

参拝後の体験を保存し、ユーザーが過去の相談・参拝・変化を振り返れる状態にする。

### 対象

- Reflection Prompt
- 回答保存
- mood_before / mood_after
- Visitとの関連付け
- Journey Timeline表示
- 過去の相談・推薦・参拝・振り返りの接続

### 完了条件

ユーザーが以下を時系列で確認できる。

```text
相談内容
↓
推薦された神社
↓
参拝行動
↓
振り返り
```

Reflectionは診断や正解提示ではなく、ユーザー自身の言語化を支援する。

---

## Phase 3: Premium導線

### ゴール

無料体験を壊さず、継続利用と記録価値を中心にPremium体験を成立させる。

### Premiumの中心価値

- より深いパーソナル理由
- 相談履歴の継続分析
- Visit / Reflection履歴の拡張
- 保存件数や記録機能の拡張
- 過去との比較
- 継続的な振り返り支援

### Premiumの中心にしないもの

- 地図表示
- 神社検索
- 基本的な経路案内
- 占術結果だけの表示
- 単純な検索件数増加

### 完了条件

無料ユーザーが基本体験を完了でき、Premiumユーザーには継続利用による追加価値が明確に提供される。

---

## Phase 4: Analytics整備

### ゴール

推薦品質と収益導線を、印象ではなく行動データで改善できる状態にする。

### 主要ファネル

```text
consultation_started
↓
recommendation_viewed
↓
detail_view
↓
save
↓
route_open
↓
visit
↓
reflection_saved
```

### 主要指標

- 相談完了率
- 推薦から詳細への遷移率
- 保存率
- 経路確認率
- 参拝登録率
- Reflection保存率
- 再訪率
- Premium導線表示率
- Premium導線クリック率
- 課金転換率
- 継続率

### 完了条件

各ファネルの件数・CVR・離脱点を確認でき、改善施策の前後比較ができる。

---

## Phase 5: Recommendation品質改善

### ゴール

相談内容と神社固有情報の接続を強化し、どの神社にも当てはまる推薦文を減らす。

### 対象

- Fact / Meaning / Consultation / Recommendationの責務分離
- Recommendation Readiness
- Coverage
- deity / shrine_historyの整備
- culture_translationの運用
- Recommendation Reasonの固有性
- Action / Reflectionとの一貫性

### Score v3

Score v3はshadow modeで観測を続ける。

active化は、推薦ログと行動ファネルの実測を確認した後に検討する。

### 完了条件

- 推薦理由に神社固有情報が含まれる
- FactとMeaningが混在しない
- Actionが推薦理由と矛盾しない
- Reflectionが相談・推薦・参拝に接続する
- Readiness不足の神社を識別できる

---

## Phase 6: Shrine Data Quality

### ゴール

推薦品質を支える神社データを、継続的に追加・検証・更新できる状態にする。

### 対象

- Shrine Profile
- 祭神
- 由緒
- ご利益
- history_theme
- place_context
- Trust provenance
- Coverage
- Recommendation Readiness
- Shrine Submission Review

### 完了条件

神社データについて以下を判別できる。

- 登録済みか
- 値が入力済みか
- 出典確認済みか
- 推薦に利用可能か

---

## Phase 7: Release Readiness

### ゴール

Web版を一般ユーザーへ公開し、安全に運用できる状態にする。

### 対象

- 本番環境設定
- CI
- エラー監視
- Rate Limit
- 外部APIコスト制御
- 利用規約
- プライバシーポリシー
- 画像アップロード検証
- バックアップ
- Rollback手順
- 課金状態の監査

### 完了条件

- main / developのCIが安定している
- 本番環境で主要導線が動作する
- 課金事故を防止できる
- 障害時に切り戻せる
- 利用データを安全に扱える

---

## Phase 8: Mobile展開

### ゴール

Web版で検証済みの体験をモバイルへ展開する。

### 前提条件

- Web版の主要ファネルが完成している
- 継続利用の兆候が確認できる
- Premium価値が検証できている
- Web / Mobileでbackend正本を共有できる

### 方針

Mobile独自の推薦・意味判定ロジックは持たない。

以下はbackendを正本とする。

- Consultation Interpretation
- Meaning Translation
- Recommendation
- Action
- Reflection
- Billing State

---

## 現在の実装順序

### 主フェーズ

```text
Recommendation品質改善
↓
Shrine Data Quality
↓
Release Readiness
↓
Mobile本番配布準備
```

### 横断的な検証

以下は基盤実装済みとし、主フェーズと並行して継続的に検証・改善する。

- Visit Flow
- Reflection Timeline
- Premium導線
- Analytics
- Recommendationから参拝までの行動ファネル
- Premium転換率および継続率
- Web / Mobile間の主要体験差

Phase 1〜4は独立した新規実装フェーズとしては完了している。

ただし、各基盤の品質、利用率、CVRおよび継続価値の検証は完了扱いにせず、後続フェーズでも継続する。

---

## 文書管理ルール

本書には以下を記載しない。

- PR単位の細かなチェックリスト
- 完了済み実装の詳細履歴
- APIレスポンスの具体的なschema
- Migration番号
- テストケース一覧
- 一時的なブランチ名
- 調査用コマンド
- 一時的な外部API移行案

個別情報は以下へ分離する。

- タスク: GitHub Issue / Pull Request
- システム構造・横断契約: `docs/core/`
- 体験・機能設計: `docs/product/`
- 神社データ・意味・コピー原則: `docs/knowledge/`
- Analytics: `docs/analytics/`
- 監査: `docs/audit/`
- インフラ: `docs/infra/`
- 実装履歴: Git履歴 / Pull Request

本書は、フェーズ、順序、ゴール、完了条件が変わる場合のみ更新する。
