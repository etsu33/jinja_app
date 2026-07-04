# Reason Facts Coverage After Classification Policy

## 目的

地域氏神型の分類方針追加後に、Recommendation Reason v4 の神社データ Coverage を再監査する。

---

## 実行結果

### 対象

- 神社数: 105

### 不足件数

| 項目 | 件数 |
|---|---:|
| no_history_theme | 7 |
| no_goriyaku | 7 |
| no_goriyaku_tags | 7 |

### shrine_data_count

前回監査から変更なし。

| shrine_data_count | 神社数 |
|------------------:|-------:|
| 1 | 7 |
| 3 | 98 |

---

## 不足対象

### 実運用データ

- 長太稲荷神社
- 給田六所神社

### evidence不足

Recommendation Reason v4 では `goriyaku_tags` を evidence として利用するため、evidence 不足対象も以下の2社である。

- 長太稲荷神社
- 給田六所神社

### テストデータ

- 承認テスト神社
- admin承認テスト神社
- 重複検証神社
- 重複検証神社
- 重複検証神社（別宮）

---

## 判断

今回のPRでは、地域氏神型の分類方針を docs に追加したが、DB実データはまだ更新していない。

そのため、Coverage件数は前回監査から変化していない。

shrine_data_count の分布も前回監査から変化はなく、神社固有情報不足の対象は実運用データでは2社のみであることを再確認した。

---

## 次の判断

- 給田六所神社は、地域氏神型として DB 補完候補
- 長太稲荷神社は、現時点では根拠不足のため保留継続候補
- テストデータは改善対象外
