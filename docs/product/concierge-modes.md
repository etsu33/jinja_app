# Concierge Modes

## 目的

本ドキュメントは、KAMI MUSUBI における各コンシェルジュモードの責務と役割を定義する。

推薦ロジックや実装仕様ではなく、「どの入力を受け取り、どのような役割を持つか」の責務のみを扱う。

---

## Mode一覧

| Mode | 主な役割 | 主入力 |
|------|----------|---------|
| Need Mode | 相談内容を起点に推薦する | 相談テーマ・自由入力 |
| Compat Mode | 生年月日を補助情報として利用する | 生年月日 |
| Route Mode | 移動しやすさを補助する | 現在地 |
| Theme Mode | 人生テーマから探索する | history_theme |
| Shrine Search Mode | 神社名・地域名から検索する | 神社名・地域名 |

---

## 基本原則

- Need Mode を推薦の主軸とする
- Compat Mode は補助シグナルとして扱う
- Route・Theme・Shrine Search は探索導線として扱う
- 推薦順位は Backend が決定する
- Mode は推薦アルゴリズムではなく入力文脈を決定する

---

## Mode責務

### Need Mode

- 相談内容を解釈する入口
- Recommendation の主入力となる
- Meaning Layer へ状態情報を渡す

### Compat Mode

- 生年月日情報を補助入力として利用する
- Need Mode を置き換えない
- 占術情報のみで推薦を決定しない

### Route Mode

- 現在地や移動条件を補助する
- 推薦順位ではなく移動体験を支援する

### Theme Mode

- history_theme を起点とした探索を担当する
- 推薦ではなくテーマ別閲覧を支援する

### Shrine Search Mode

- 神社名・地域名による検索を担当する
- Concierge とは独立した探索導線とする

---

## 責務境界

| ドキュメント | 責務 |
|--------------|------|
| `docs/product/concierge-modes.md` | Modeの役割・責務 |
| `docs/product/concierge-first.md` | 体験導線 |
| `docs/core/meaning-layer.md` | 意味変換 |
| `docs/core/architecture.md` | システム全体の責務 |

---

## 関連ドキュメント

- `docs/product/concierge-first.md`
- `docs/core/meaning-layer.md`
- `docs/core/architecture.md`

---

## 更新ルール

- 本書には推薦ロジック・API仕様・実装手順を記載しない
- Modeの責務または種類が変更された場合のみ更新する
- 詳細仕様は各正本ドキュメントで管理する
