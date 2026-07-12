# Concierge First

## 目的

本ドキュメントは、KAMI MUSUBI の主導体験を「神社検索」ではなく、「相談テーマから神社と出会い、現実の行動へつなげる体験」として定義する。

画面構成、入力責務、体験導線を整理し、Recommendation や Meaning Layer の詳細仕様は各正本ドキュメントへ委譲する。

---

## 体験フロー

```text
相談テーマ
↓
状態整理
↓
Recommendation
↓
Detail
↓
Route
↓
Visit
↓
Reflection
```

KAMI MUSUBI は Concierge First を採用し、神社検索ではなく「相談」から体験を開始する。

---

## 基本原則

- 相談テーマをプロダクトの主入力とする
- 神社検索・地図は補助導線として扱う
- 占術・相性・吉方位は補助シグナルとして扱う
- AIは心理・宗教・人生を断定しない
- Recommendation Input Profile の生成は Backend を正本とする
- 表示文言の最終決定は Composer が担当する

---

## 入力責務

### 主入力

- 相談テーマ

### 補助条件

- 参拝スタイル
- 誕生日
- ご利益タグ

### 補助シグナル

- 占星術
- 九星気学
- 吉方位
- 相性

相談テーマを推薦理由の中心とし、補助条件・補助シグナルは推薦を補完するために利用する。

---

## 画面責務

| 画面 | 責務 |
|------|------|
| Top | 相談開始 |
| Concierge | 相談入力・推薦理由の提示 |
| Explore | 候補探索・比較・地図表示 |
| Detail | 神社情報の理解 |
| Route | 現地への移動支援 |
| Visit | 参拝行動の記録 |
| Reflection | 行動後の振り返り |

### 設計原則

- Explore は候補探索を担当し、Recommendation Logic や Meaning Layer を持たない
- Detail は神社理解を担当し、過度なパーソナライズを行わない
- Recommendation の生成は Concierge が担当する

---

## 責務境界

| ドキュメント | 責務 |
|--------------|------|
| `docs/product/concierge-first.md` | 体験導線・画面責務・入力責務 |
| `docs/product/concierge-modes.md` | 推薦モードと入力解釈 |
| `docs/core/meaning-layer.md` | Meaning Layer と意味変換 |
| `docs/core/architecture.md` | システム全体の責務境界 |

---

## 関連ドキュメント

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/product/concierge-modes.md`
- `docs/product/explore-integration-design.md`
- `docs/shrine-detail-layer.md`
- `docs/core/roadmap.md`

---

## 更新ルール

- 詳細仕様や実装履歴は本書へ記載しない
- API仕様・実装手順・テストケース・TODOは専用ドキュメントへ分離する
- 体験導線・画面責務・入力責務が変更された場合のみ更新する
- 実装状態の細かな変更では更新しない
- Concierge First の設計原則が変更された場合のみ本書を更新する
