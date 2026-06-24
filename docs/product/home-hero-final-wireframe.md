
# HomeHero Final Wireframe

## HomeHeroの役割

HomeHeroは「神社を探す場所」ではなく、
「今の相談から神社と出会う入口」とする。

目的は以下の3つ。

- ユーザーが相談テーマを選ぶ
- コンシェルジュ体験へ自然に遷移する
- 神社検索アプリではなく相談体験であることを伝える

HomeHeroで推薦を完結させない。

推薦体験の開始地点として扱う。

---

## HomeHeroに残す要素

### 残す

- Heroタイトル
- Heroサブコピー
- 相談テーマチップ
- 自由入力 textarea
- 条件追加導線
- コンシェルジュ開始CTA

### 残さない

- 誕生日入力
- ご利益選択
- 参拝スタイル選択
- 詳細条件入力
- 神社検索UI

これらはすべて Concierge Filter へ集約する。

---

## HomeHeroConsultationInputとの責務境界

### HomeHero

役割:

- 相談を始める
- テーマを選ぶ
- コンシェルジュへ送客する

### Concierge

役割:

- Need推定
- 条件調整
- 推薦生成
- 推薦理由表示

HomeHeroは入口。

推薦ロジックは持たない。

---

## 相談テーマチップ最終一覧

第一候補。

- 仕事
- 人間関係
- お金
- 挑戦
- 休息
- 健康
- 学び
- 将来

補足:

- 自由入力は維持
- チップは入力補助として扱う
- テーマ固定を強制しない

---

## 条件追加導線の文言

表示:

「＋ 条件を追加する」

補足:

「誕生日・ご利益・参拝スタイルなどの条件を追加できます」

条件は主役ではない。

相談テーマより目立たせない。

---

## Home→Concierge遷移仕様

### 通常

Home
↓
/concierge?theme=...

### 条件追加

Home
↓
/concierge?theme=...&openFilter=1

### テーマ未入力

Home
↓
/concierge

### 条件追加のみ

Home
↓
/concierge?openFilter=1

---

## 次PR候補

### PR1

HomeHero最終UI整理

- テーマチップを最終版へ更新
- 文言整理
- Hero余白整理

### PR2

Filter統合作業

- 誕生日をFilterへ集約
- ご利益をFilterへ集約
- 参拝スタイルをFilterへ集約

### PR3

Home / Concierge入力統一

- 共通Input定義
- 共通テーマ一覧定義
- 共通型定義

---

## この段階の完成定義

- Homeは相談開始に特化
- 条件入力はFilterへ集約
- HomeとConciergeの責務が重複しない
- Concierge First方針と整合する