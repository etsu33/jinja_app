# Concierge First

## 目的

本ドキュメントは、KAMI MUSUBI の主導体験を「神社検索」ではなく、「相談から神社と出会い、現実の行動へつなげる体験」として定義する。

詳細なUI仕様、推薦ロジック、Meaning Layer、実装仕様は各正本ドキュメントへ委譲し、本書では体験全体の原則と責務のみを定義する。

---

## 体験フロー

```text
相談
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

KAMI MUSUBI は Concierge First を採用し、検索ではなく相談から体験を開始する。

---

## 基本原則

- 相談をプロダクトの主入口とする
- 神社検索・地図は補助導線とする
- 補助条件（参拝スタイル・誕生日・ご利益）は推薦を補完する
- 占術・相性・吉方位は補助シグナルとして扱う
- Backend を推薦入力の正本とする
- AIは心理・宗教・人生を断定しない

---

## 入力責務

| 区分 | 内容 |
|------|------|
| 主入力 | 相談テーマ・自由入力 |
| 補助条件 | 参拝スタイル・誕生日・ご利益タグ |
| 補助シグナル | 占星術・九星気学・吉方位・相性 |

相談内容を推薦理由の中心とし、その他の情報は補助的に利用する。

---

## 画面責務

| 画面 | 役割 |
|------|------|
| Top | 相談開始 |
| Concierge | 推薦生成 |
| Explore | 候補探索 |
| Detail | 神社理解 |
| Route | 移動支援 |
| Visit | 参拝記録 |
| Reflection | 振り返り |

### 設計原則

- Concierge が推薦を担当する
- Explore は探索のみを担当する
- Detail は神社情報を正確に伝える
- Reflection は行動後の変化を整理する

---

## 責務境界

| ドキュメント | 役割 |
|--------------|------|
| `docs/product/concierge-first.md` | 体験全体・画面責務 |
| `docs/product/concierge-modes.md` | 推薦モード |
| `docs/core/meaning-layer.md` | 意味変換 |
| `docs/core/architecture.md` | 全体構造 |

---

## 関連ドキュメント

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/product/concierge-modes.md`
- `docs/product/explore-integration-design.md`

---

## 更新ルール

- 本書には詳細仕様・実装手順・TODOを記載しない
- 体験導線・画面責務・設計原則が変更された場合のみ更新する
- 詳細設計は各正本ドキュメントで管理する
