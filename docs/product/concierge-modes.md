# Concierge Modes

## 目的

本ドキュメントは、KAMI MUSUBI におけるコンシェルジュの推薦入口（Mode）の責務を定義する。

各Modeの役割、入力責務、優先順位を整理し、Recommendation・Meaning Layer・Consultation Interpretationへの接続方針を定義する。

---

## 推薦フロー

```text
User Input
↓
Mode Resolver
↓
Consultation Interpretation
↓
Meaning Translation
↓
Recommendation
↓
Action / Reflection
```

Modeは推薦アルゴリズムではなく、「どの文脈から相談を解釈するか」を決定する入口として扱う。

---

## 基本方針

MVPでは以下の2つを正式な推薦モードとする。

| Mode | 目的 |
|------|------|
| Need Mode | 悩み・状態・願いごとから神社を提案する |
| Compat Mode | 生年月日を補助情報として神社を提案する |

将来的なModeは保持するが、MVPでは推薦の主軸としない。

---

## Mode一覧

| Mode | 主入力 | 役割 | 推薦への影響 |
|------|--------|------|--------------|
| Need Mode | 相談テーマ・状態 | 推薦の主軸 | 主入力 |
| Compat Mode | 生年月日 | 相性情報の補助 | 補助入力 |
| Route Mode | 現在地 | 行きやすさ | 将来拡張 |
| Theme Mode | history_theme | テーマ探索 | 将来拡張 |
| Shrine Search Mode | 神社名・地域名 | 通常検索 | 探索導線 |

---

## Need Mode

### 目的

現在の悩み・状態・願いごとを起点に神社を提案する。

### 主入力

- 相談テーマ
- ご利益タグ
- 補助条件
- エリア
- 位置情報
- 生年月日（任意）

### 基本方針

- Recommendation の中心となるMode
- history_theme を主軸に意味を生成する
- ご利益だけで推薦理由を作らない
- 神社固有の文脈と相談内容を接続する

---

## Compat Mode

### 目的

生年月日から得られる情報を補助シグナルとして利用する。

### 主入力

- 生年月日
- エリア
- 位置情報

### 基本方針

- Recommendation の補助入力として扱う
- Need Mode より優先しない
- 性格・運命・未来を断定しない
- 占術情報だけで推薦を決定しない

---

## Mode優先順位

状態相談が存在する場合は Need Mode を優先する。

```text
相談テーマ
↓
Need Mode
↓
Recommendation

生年月日のみ
↓
Compat Mode
↓
Recommendation
```

優先順位

```text
相談テーマ
＞
ご利益
＞
生年月日
```

---

## Recommendationとの関係

Modeは Recommendation の順位を直接決定しない。

Recommendation Input Profile を生成するための入口として利用する。

```text
User Input
↓
Mode Resolver
↓
Consultation Interpretation
↓
Recommendation Input Profile
↓
Meaning Translation
↓
Recommendation
```

Recommendation順位の決定は Backend を正本とする。

---

## Meaning Layerとの関係

Modeは Meaning Layer の入力を決定する。

Need Mode は状態理解を中心に Meaning Translation を行い、Compat Mode は補助シグナルとして利用する。

Meaning Layer は Recommendation の説明文や Action・Reflection の生成へ接続する。

---

## 責務境界

| ドキュメント | 責務 |
|--------------|------|
| `docs/product/concierge-modes.md` | 推薦Mode・入力責務・優先順位 |
| `docs/product/concierge-first.md` | 体験導線・画面責務 |
| `docs/core/meaning-layer.md` | 意味変換 |
| `docs/core/architecture.md` | 全体構造・責務境界 |

---

## 関連ドキュメント

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/product/concierge-first.md`
- `docs/product/history-theme-taxonomy.md`
- `docs/product/meaning-translation-mapping.md`

---

## 更新ルール

- 推薦ロジックの詳細は本書へ記載しない
- 実装履歴・TODO・チェックリストは本書へ記載しない
- API仕様・Score設計・テスト仕様は専用ドキュメントへ分離する
- Modeの責務または入力体系が変更された場合のみ更新する
- 実装状態の変更だけでは本書を更新しない
