> **Status: Archive**
>
> 本ドキュメントは、神社詳細画面のMeaning Layer実装前に行った監査記録である。
>
> 記載内容は監査時点のスナップショットであり、現行仕様判断には使用しない。
>
> 現在のMeaning LayerおよびShrine Meaning実装契約は以下を参照する。
>
> - `docs/core/meaning-layer.md`
> - `docs/core/meaning-layer-connection.md`
> - `docs/core/architecture.md`
> - `docs/meaning-layer/shrine-meaning-payload-v2.md`
> - `docs/meaning-layer/backend-meaning-composer.md`
> - `backend/temples/services/shrine_meaning_composer.py`
> - `backend/temples/api/views/shrine_meaning.py`
> - `apps/web/src/lib/shrineMeaning/payloadV2.ts`

# 神社詳細 Meaning Layer 監査

## 目的

神社詳細画面のMeaning Layer実装前に、神社情報をどのように意味づけへ利用するか、事実情報と生成文をどのように分離するかを整理した監査記録である。

本書は、後続のShrine Meaning PayloadおよびBackend Meaning Composer設計へ至った判断根拠を保存する。

---

## 監査時点の基本方針

神社詳細のMeaning Layerでは、歴史・御祭神・ご利益・土地性を単独で主役にしない。

表示と意味づけの優先順は、以下として整理された。

```text
状態
↓
意味
↓
行動
↓
歴史的文脈による補強
↓
御祭神・ご利益・神社情報による補足
```

神社の事実情報は、ユーザーの状態や行動を断定するためではなく、Meaningを補強する材料として扱う。

---

## `history_theme`の扱い

### 監査時点の候補

- 再出発
- 静寂
- 復興
- 勝負
- 縁
- 学び
- 守り

この一覧は監査時点の候補であり、現在の分類契約を示すものではない。

現行の`history_theme`定義は、以下を参照する。

- `docs/product/history-theme-taxonomy.md`
- Backendの関連定義およびテスト

### 意味上の扱い

- 歴史本文ではなく、意味接続のための文脈として扱う
- 神社をどのように受け取るかを補助する
- タグ単体から歴史説明を生成しない
- ユーザーの状態を断定するために使用しない

### 監査時点の注意点

- Backend ModelにFieldが存在していても、APIごとの露出状況は一様ではなかった
- 本文情報を伴わずに歴史説明へ変換すると、一般的な解説文へ寄りやすかった
- 分類名と表示文を混同しない必要があった

---

## `description`の扱い

`description`は神社の特徴を示す事実情報または生成材料として扱う。

### 方針

- そのままMeaning本文として前面表示しない
- 必要に応じて要約・正規化する
- 神社紹介ではなく、相談文脈との接続材料として利用する
- 事実情報と生成された意味づけを分離する

### 注意点

`description`を中心に据えると、Meaning Layerではなく一般的な神社案内や観光説明へ寄りやすい。

---

## `sajin`の扱い

`sajin`は御祭神に関する事実情報として扱う。

### 方針

- 御祭神の名称または象徴接続の材料として扱う
- 由緒本文とは分離する
- 御祭神情報だけからユーザーへの意味を断定しない
- 生成文へ利用する場合も補助的な扱いに留める

### 注意点

- `sajin`は由緒Fieldではない
- 「御祭神・由緒」と一括表示すると、存在しない由緒情報を示しているように見える
- 由緒本文がない場合は、由緒説明として補完しない

---

## `goriyaku`の扱い

`goriyaku`は、ご利益の事実情報および行動意味を生成する補助材料として扱う。

### 方針

- 願望成就や効果保証の説明にしない
- ユーザーの相談状態や次の行動との接続に利用する
- ご利益名の列挙だけでMeaning本文を構成しない
- 宗教的な正解や結果を示さない

### 注意点

ご利益をそのまま前面表示すると、神社体験が祈願メニューの選択へ寄りやすい。

Meaning Layerでは、願いの分類ではなく、ユーザーが次に取れる行動や整理の補助へ変換する。

---

## `element`の扱い

`element`は、神社の雰囲気や属性を補助する材料として扱う。

### 方針

- Meaning生成の補助シグナルとして扱う
- 神社またはユーザーの固定的な性質を示すものとして扱わない
- 相談内容や事実情報より優先しない
- 占術的な断定へ使用しない

### 注意点

`element`は補助情報であり、神社選定や相性判断の正本にはしない。

---

## `place_tags`の扱い

`place_tags`は、土地性・空間性・場所の特徴を示す補助材料として扱う。

### 方針

- なぜその場所を訪れる意味があるかを補強する
- `history_theme`、`description`、`sajin`、`goriyaku`などと組み合わせて利用する
- 単独で深い意味づけを生成しない
- 実在する事実情報と生成文を明確に分離する

### 監査時点の留意事項

`place_tags`の保存場所や正式な契約は、監査時点では確定していなかった。

現行の保存場所・Payload契約はコードを正本とする。

---

## Meaning Layerが一般解説へ寄りやすい箇所

監査時点では、以下の構造が一般的な神社解説や観光情報へ寄りやすいと判断された。

- `sajin`を御祭神と由緒の両方として扱う
- `description`をそのまま本文へ転用する
- `goriyaku`を願望成就や結果保証として説明する
- `history_theme`を歴史的事実のように表示する
- 補足欄がご利益・御祭神・相性情報の列挙だけになる
- 神社情報の説明量が、相談・意味・行動より前面に出る

---

## 当時整理した責務境界

### 事実情報

以下は、神社に関する事実情報またはMeaning生成材料として扱う。

- 神社名
- 所在地
- 緯度・経度
- `description`
- `sajin`
- `goriyaku`
- `history_theme`
- `element`
- `place_tags`

### Generated Meaning

以下は、Backend Meaning Composerが事実情報と相談文脈から生成する。

- 相談内容との接続
- 神社を提示する意味
- 参拝や保存を行動として置く意味
- `history_theme`による補助文脈
- 御祭神・ご利益による補足
- 詳細画面冒頭の短い意味コピー

### Frontend表示

Frontendは、生成済みのMeaning Payloadを表示する。

Frontend側で同じMeaning本文を再生成しない。

---

## 後続設計への接続

本監査の内容は、以下の設計と実装へ引き継がれた。

```text
神社詳細Meaning監査
↓
Payload露出差分の整理
↓
ShrineMeaningPayloadV2
↓
Backend Meaning Composer
↓
Shrine Meaning専用Endpoint
↓
Frontend表示
```

現在の詳細な契約は、以下を参照する。

- `docs/meaning-layer/shrine-meaning-payload-v2.md`
- `docs/meaning-layer/backend-meaning-composer.md`

---

## 現行仕様との責務境界

### 本書が保持するもの

- 神社詳細Meaning Layer実装前の監査内容
- 事実情報と生成文を分離する判断根拠
- 神社情報が一般解説へ寄りやすい問題の記録
- 後続のPayload・Composer設計へ至った背景

### 本書が扱わないもの

- 現在のPayload Field
- 現在のEndpoint Contract
- 現在のDisplay Block
- 現在の`history_theme`分類
- 現在のFrontend表示
- Free / Premium境界
- API・Serializerの現在仕様
- 実装計画
- 開発タスク

---

## 関連ドキュメント

### 現行の責務・思想

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`

### 現行実装を補足するReference

- `docs/meaning-layer/shrine-meaning-payload-v2.md`
- `docs/meaning-layer/backend-meaning-composer.md`

### 現行のfield-level契約

- `backend/temples/services/shrine_meaning_composer.py`
- `backend/temples/api/views/shrine_meaning.py`
- `apps/web/src/lib/shrineMeaning/payloadV2.ts`

---

## 更新ルール

- 本書は実装前監査の履歴として保持する
- 現行仕様の変更に合わせて更新しない
- 当時の監査内容に重大な事実誤認が確認された場合のみ修正する
- TODO、PR候補、実装計画、作業進捗は記載しない
