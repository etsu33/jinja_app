> **Status: Reference**
>
> 本ドキュメントは Compat Mode のUI導線と表示責務を補足する Reference 文書である。
>
> Mode全体の責務は `docs/product/concierge-modes.md`、
> 補助条件UIは `docs/product/concierge-filter-area.md`、
> Meaning変換は `docs/product/meaning-translation-mapping.md` を正本とする。

# Compat Mode UI Flow

## 目的

Concierge FirstにおけるCompat ModeのUI導線と表示責務を定義する。

Compat Modeは、誕生日・`element4`・相性情報・占術・方位情報などを、相談内容に対する補助シグナルとして扱う。

推薦の主導線はNeed Modeとし、Compat Modeは相談テーマや自由入力を上書きしない。

---

## 基本方針

```text
Need Mode
相談テーマ / 自由入力 / need_tags / matched_need_tags
↓
推薦理由の中心

Compat Mode
誕生日 / element4 / 相性情報 / 方位情報
↓
推薦理由の補足
```

- Need Modeを推薦の主導線とする
- Compat Modeは補助条件として扱う
- 誕生日入力は任意とする
- Compat Modeだけで推薦候補を決定しない
- 相性・占術・方位を断定的に表示しない
- 吉方位は計算根拠が確認できる場合のみ補助情報として扱う
- Backendを推薦判定の正本とする

---

## Compat Modeの責務

### 担当するもの

- 誕生日入力
- element4
- 相性に関する補助情報
- 占術由来の補助シグナル
- 方位に関する補助情報
- 推薦理由の補足文脈

### 担当しないもの

- 相談テーマの決定
- need_tagsの主判定
- 推薦理由の主文脈
- 推薦順位の単独決定
- ユーザーの性格・運命・未来の断定
- 参拝すべき神社や方角の断定

---

## 誕生日入力

誕生日は、相性や傾向を補足する任意入力として扱う。

### UI上の扱い

- Home Heroには配置しない
- Concierge Entryの主入力にしない
- Concierge Filter内に配置する
- 未入力でも推薦へ進める
- 補助情報として利用することを明示する

### 利用目的

- element4算出の入力
- 相性情報の補助
- hasBirthdateの判定
- Compat Modeの補助シグナル

### 表示文言

```text
誕生日（任意）
提案の補助として使います
```

### 表示原則

- 性格診断として見せない
- 運命や未来を断定しない
- 誕生日情報だけで神社を決定しない
- 相談テーマより強く表示しない

---

## element4

element4は、誕生日から得られる相性補助ラベルとして扱う。

### 役割

- 相性情報の補助
- Compat Modeの説明材料
- 推薦候補間の補助シグナル

### 表示原則

- ユーザーの本質や人格を表すものとして扱わない
- 固定的なタイプ診断として表示しない
- 相談内容より優先しない
- 推薦理由の主語にしない

### 使用しない表現

- あなたはこのタイプです
- この属性だから、この神社へ行くべきです
- あなたの性格にはこの神社が正解です

### 使用する表現

- 誕生日情報から見た補助的な傾向です
- 相性情報を整理するための参考として利用します
- 相談内容を補足する情報として扱います

---

## 相性情報

相性情報は、Need Modeで整理された相談内容に対し、神社候補を補足的に説明するために使用する。

### UI上の扱い

- Concierge Filter内に配置する
- 推薦結果の主理由にしない
- Meaning Cardでは補足情報として表示する
- ユーザーの相談内容と矛盾する候補を強制しない

### 表示文言

```text
相性から見た補助情報
誕生日情報をもとに、相談内容を補足する参考情報を表示しています。
```

---

## 方位情報

方位情報は、現在地・神社位置・計算根拠が確認できる場合のみ補助情報として扱う。

### 表示原則

- 推薦の主理由にしない
- 相性情報と混同しない
- 吉凶を断定しない
- 参拝を強制しない
- 計算根拠が確認できない場合は表示しない

### 使用しない表現

- 今日はこの方角が吉です
- 吉方位なので、この神社へ行くべきです
- この方角へ行けば運気が上がります

### 使用する表現

- 方位情報は補助的な参考として扱います
- 現在地と神社位置にもとづく参考情報です
- 相談内容との一致を優先して提案しています

---

## Need Modeとの責務境界

| 項目 | Need Mode | Compat Mode |
|---|---|---|
| 主入力 | 相談テーマ・自由入力 | 誕生日 |
| 主データ | need_tags・consultation_axis | element4・相性情報 |
| 推薦理由 | 主文脈 | 補足文脈 |
| UI位置 | Home Hero・Concierge Entry | Concierge Filter |
| スコアへの影響 | 主軸 | 補助シグナル |
| 表示トーン | 相談内容から整理する | 補助情報として参照する |

### 境界ルール

- Need Modeを主導線とする
- Compat Modeは相談内容を上書きしない
- Compat Mode由来の情報を推薦理由の主語にしない
- 相性・占術・方位だけで推薦順位を決定しない
- Compat Mode由来の情報は補足表示に留める

---

## Home Heroでの表示

Home HeroではCompat Modeの入力項目を表示しない。

### 表示するもの

- 相談テーマ
- 自由入力
- コンシェルジュ開始CTA
- 条件追加導線

### 表示しないもの

- 誕生日入力
- element4
- 相性情報
- 方位情報
- 占術説明

Home Heroは相談開始の入口であり、相性診断や占術の入口として扱わない。

---

## Concierge Entryでの表示

Concierge EntryではCompat Modeを主入力として扱わない。

### 表示するもの

- 相談内容
- 自由入力
- 補助条件への導線
- 推薦生成CTA

Compat Modeへの導線は以下とする。

```text
＋ 条件を追加する
```

誕生日や相性情報は、Concierge Filterを開いた先で扱う。

---

## Concierge Filterでの表示

Compat Modeの入力と補助情報はConcierge Filterが担当する。

```text
Concierge Entry
↓
条件を追加する
↓
Concierge Filter
├─ 誕生日
├─ 相性に関する補助情報
└─ その他の補助条件
```

補助条件の画面構成と責務は `docs/product/concierge-filter-area.md` を参照する。

---

## Meaning Cardでの表示

Meaning Cardでは、Need Mode由来の推薦理由を主表示とし、Compat Mode由来の情報を補足表示とする。

### 表示順

```text
1. 相談内容との一致
2. 神社側の意味文脈
3. 次に取りやすい行動
4. 補足情報
   - 誕生日由来の相性情報
   - 参拝スタイルとの一致
   - 根拠が確認できる場合の方位情報
```

### 表示原則

- 相性情報だけで推薦理由を完結させない
- 占術情報を確定事項として表示しない
- Need Modeの推薦理由より強く表示しない
- 方位情報と相性情報を分離する

---

## Recommendationとの接続

Compat Modeは、Recommendationの補助入力を提供する。

### 補助入力

- birthdate
- hasBirthdate
- element4
- suggestedTags
- selected_goriyaku_tag_ids
- direction_bonus

### ルール

- query・need_tags・matched_need_tagsを主軸とする
- Compat Modeの入力は主入力を上書きしない
- 補助シグナルだけで順位を決定しない
- 推薦順位の判定はBackendを正本とする
- Frontendは相性・占術・方位の判定ロジックを重複実装しない

---

## UI文言

### 使用しない表現

- あなたはこのタイプです
- この神社が運命的に合っています
- 吉方位なので行くべきです
- 誕生日から見ると、これが正解です
- この神社へ行けば運気が上がります

### 使用する表現

- 誕生日情報は、相性を見る補助として使います
- 相談内容との一致を優先して提案しています
- 相性情報は補足として参考にできます
- 方位情報は根拠が確認できる場合のみ参考として表示します

---

## 責務境界

### Frontend

- 誕生日入力を受け付ける
- 補助情報を表示する
- Compat Modeの情報をPayloadへ渡す
- Need Modeより控えめに表示する

### Backend

- 誕生日由来の補助情報を生成する
- Compat Modeの入力を推薦へ反映する
- 相性・占術・方位情報の利用可否を判定する
- 推薦順位と推薦理由への影響を決定する

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/need-mode-ui-flow.md`
- `docs/product/concierge-filter-area.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/home-hero-final-wireframe.md`
- `docs/product/concierge-entry-final-wireframe.md`

---

## 更新ルール

- 本書はCompat ModeのUI導線と表示責務のみを管理する。
- 推薦ロジック・占術ロジック・方位計算・API契約は各正本で管理する。
- Need ModeとCompat Modeの責務境界を重複定義しない。
- Compat ModeのUI導線または表示責務が変更された場合のみ更新する。
- TODO・PR計画・実装進捗・監査途中の判断は本書へ記載しない。
