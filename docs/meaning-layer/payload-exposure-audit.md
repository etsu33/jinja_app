

# Meaning Layer Payload Exposure Audit

## 入口別 payload 差分

| 入口 | API / payload | goriyaku | sajin | description | history_theme | element | meaning生成 | 備考 |
|---|---|---:|---:|---:|---:|---:|---|---|
| 神社詳細 | ShrineDetailSerializer | ○ | × | × | × | × | frontend | 情報不足 |
| 神社一覧 | ShrineListSerializer | × | × | × | × | × | なし | list用途 |
| Concierge候補 | concierge candidate | ○ | 未確認 | ○ | ○ | 未確認 | backend/frontend混在 | 最も情報が多い可能性 |
| Map | nearby/search payload | 未確認 | × | 未確認 | × | × | なし | 場所導線 |
| Ranking | ranking payload | 未確認 | × | 未確認 | × | × | なし | 人気導線 |
| Favorite | favorite shrine payload | 未確認 | 未確認 | 未確認 | 未確認 | 未確認 | なし | 保存後導線 |

---

## 現状整理

### 共通問題

- Shrine model に存在する field が API ごとに露出差分を持つ
- frontend 型に存在する field と実API payload が一致していない
- Meaning Layer の責務が frontend 側に一部寄っている
- `buildShrineExplanation.ts` が payload 不足を補完している
- `history_theme` は recommendation 系 payload にのみ存在する可能性がある

### 特に危険な差分

| field | model | frontend型 | ShrineDetailSerializer | concierge payload |
|---|---|---|---|---|
| goriyaku | ○ | ○ | ○ | ○ |
| sajin | ○ | ○ | × | 未確認 |
| description | ○ | ○ | × | ○ |
| history_theme | ○ | × | × | ○ |
| element | ○ | 型未確認 | × | 未確認 |

---

## Meaning Layer の責務境界

### 意味生成に寄せるもの

- consultationSummary
- shrineMeaning
- actionMeaning
- heroMeaningCopy
- history_theme 由来の接続文
- goriyaku 由来の行動意味
- sajin 由来の象徴接続

### 実データ表示に留めるもの

- name_jp
- address
- latitude / longitude
- goriyaku
- goriyaku_tags
- sajin
- description
- kyusei
- location

### 注意

- `sajin` は祭神として表示する
- `sajin` を由緒として扱わない
- `description` をそのまま Meaning Layer の本文にしない
- `history_theme` は歴史本文ではなく接続タグとして扱う

---

## 関連ドキュメント

- `docs/meaning-layer/shrine-detail-audit.md`
  - 神社詳細画面の表示方針
  - 場所意味生成候補
  - Wikipedia化回避
  - `sajin` / `description` / `history_theme` の扱い

---
## 次フェーズ候補

- [ ] concierge candidate payload の field 完全監査
- [ ] favorite payload の field 監査
- [ ] ranking payload の field 監査
- [ ] map payload の field 監査
- [ ] Meaning Layer v2 payload 草案
- [ ] 共通 ShrineMeaningPayload の定義
- [ ] serializer ごとの差分定義
- [ ] frontend buildShrineExplanation の責務縮小
- [ ] backend meaning source に寄せる
- [ ] UI層を表示責務へ寄せる
- [x] 実装変更はまだしない
