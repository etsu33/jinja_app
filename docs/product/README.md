

# Product Documents

## 目的

このディレクトリは、KAMI MUSUBIのプロダクト体験・意味レイヤ・推薦理由・行動設計に関する正本ドキュメントを管理する。

実装判断で迷った場合は、まずこのREADMEから関連ドキュメントを確認する。

```text
ユーザー入力
↓
推薦モード
↓
人生テーマ
↓
相談状態 / ご利益との接続
↓
神社推薦
↓
行動
↓
振り返り
↓
変化記録
```

---

## 読む順番

### 1. concierge-modes.md

推薦の入口を定義する。

```text
ユーザー入力
↓
Need Mode / Compat Mode
↓
history_theme
```

読む目的:

```markdown
- 相談がどの入口から入るかを理解する
- Need Mode と Compat Mode の責務を分ける
- 生年月日は補助情報であり、状態相談が主軸であることを確認する
```

---

### 2. history-theme-taxonomy.md

人生テーマ（history_theme）の正本。

読む目的:

```markdown
- 守り / 静寂 / 再出発 / 復興 / 勝負 / 学び / 縁 の定義を確認する
- history_theme を推薦理由・分析・履歴保存の軸として扱う
- 将来拡張候補を確認する
```

---

### 3. state-history-theme-mapping.md

相談状態から history_theme へ変換する対応表。

```text
相談状態
↓
history_theme
```

読む目的:

```markdown
- 不安 / 疲れ / 転職 / 金銭不安 / 人間関係などをどのテーマに接続するか確認する
- 推薦時に、ご利益よりも相談状態を優先する方針を確認する
- 履歴保存で history_theme を使う理由を確認する
```

---

### 4. goriyaku-history-theme-mapping.md

ご利益から history_theme へ変換する対応表。

```text
ご利益
↓
history_theme
```

読む目的:

```markdown
- 金運 / 仕事運 / 縁結び / 厄除けなどの入口を人生テーマへ接続する
- ご利益を結果保証ではなく、状態整理の入口として扱う
- 金運を 守り / 勝負 / 再出発 に分岐させる方針を確認する
```

---

### 5. history-theme-action-mapping.md

history_themeを行動・夜の振り返り・変化記録へ接続する対応表。

```text
history_theme
↓
行動テーマ
↓
visit_done
↓
reflection
```

読む目的:

```markdown
- 推薦後にユーザーが取る小さな行動を確認する
- 夜の振り返り質問を確認する
- visit_done / reflection_saved との接続を確認する
- 継続利用と変化記録の土台を確認する
```

---

## ドキュメント間の関係

```text
concierge-modes.md
  ↓
history-theme-taxonomy.md
  ↓
state-history-theme-mapping.md
  ↓
goriyaku-history-theme-mapping.md
  ↓
history-theme-action-mapping.md
```

より正確には、以下の関係で扱う。

```text
User Input
├─ query / 状態
│   └─ state-history-theme-mapping.md
│
├─ ご利益
│   └─ goriyaku-history-theme-mapping.md
│
├─ birthdate
│   └─ concierge-modes.md の Compat Mode
│
└─ location
    └─ concierge-modes.md の将来 Route Mode

↓

history-theme-taxonomy.md

↓

history-theme-action-mapping.md
```

---

## 各ドキュメントの責務

| ドキュメント | 責務 | 主な問い |
|---|---|---|
| concierge-modes.md | 推薦入口の定義 | ユーザーはどの入口から入ったか |
| history-theme-taxonomy.md | 人生テーマの正本 | このhistory_themeは何を意味するか |
| state-history-theme-mapping.md | 相談状態の意味変換 | この悩みはどのthemeか |
| goriyaku-history-theme-mapping.md | ご利益の意味変換 | このご利益はどのthemeへ接続するか |
| history-theme-action-mapping.md | 行動・振り返りへの接続 | このthemeから何をするか |

---

## 設計原則

```markdown
- ご利益は入口として扱う
- history_themeは意味レイヤーとして扱う
- 神社は行動先として扱う
- 生年月日は補助情報として扱う
- 吉方位や現在地は将来の補助導線として扱う
- 推薦理由では結果保証をしない
- 行動提案は小さく、任意のものにする
- Premium価値は文章量ではなく整理ブロック数で表現する
```

---

## 実装判断の優先順位

1. 状態相談がある場合は Need Mode を優先する
2. ご利益は状態解釈の補助として使う
3. 生年月日は相性補助として使う
4. location / route は行動補助として使う
5. history_theme は分析・履歴保存の正本にする

---

## 関連する分析指標

```markdown
- concierge_result_impression
- shrine_detail_transition
- route_open
- visit_done
- reflection_prompt_view
- reflection_saved
- premium_preview_click
- save_prompt_view
```

分析では `historyTheme` を軸にする。

```text
historyTheme
↓
詳細遷移
↓
経路表示
↓
参拝完了
↓
振り返り保存
↓
再相談
```

---

## 今後追加予定のドキュメント

```markdown
- shrine-history-theme-mapping.md
- reflection-storage.md
- visit-done-flow.md
- night-reflection-experience.md
```

---

## TODO

```markdown
- [x] 意味レイヤ設計群を一覧化
- [x] 読む順番を定義
- [x] concierge-modes / taxonomy / state mapping / goriyaku mapping / action mapping を紐付け
```
