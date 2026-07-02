

# Mobile Shrine Detail Web Parity Audit

## 目的

Web神社詳細画面とMobile神社詳細画面の情報構造を比較し、Mobileに取り込むべき要素を整理する。

## 判断

MobileはWeb詳細をそのまま移植しない。

Mobileの見た目・導線・空気感を正とし、Web/Backendの意味構造を短いカードとして取り込む。

## 基準

- 相談文と神社固有情報を主軸にする
- 誕生日・九星・五行・方位は補助シグナルとして扱う
- 占術要素は前面に出さず、必要な場合のみ選定補足として扱う
- Webの情報量をそのまま移植せず、Mobileではカードごとに短文化する

## 現在地

### Web詳細画面

- 今回の相談の整理
- 神社との意味の接続
- context_reason
- personal_meaning
- recommendation_meta

### Mobile詳細画面

- RECOMMENDATION
- 選定のポイント
- EXPLANATION
- NEXT ACTION
- 神社について

## Mobile詳細の理想構成

1. この神社が候補に入った理由
2. 選定のポイント
3. 今回の相談の整理
4. 神社との意味の接続
5. 参拝前にできること
6. 神社について

## 役割分担

| 領域 | 正本 | Mobileでの出し方 |
|---|---|---|
| 相談解釈 | Web / Backend | 今回の相談の整理として短く表示 |
| 推薦理由 | Backend reason v4 | 最上部の推薦理由カード |
| 根拠 | reasonFacts | 選定のポイント |
| 神社固有情報 | Backend shrine data | 神社について |
| 行動提案 | action suggestion v4 | 参拝前にできること |
| 誕生日・九星・五行・方位 | Backend補助シグナル | 条件レイヤーまたは選定補足に控えめ表示 |

## 実装方針

Mobileでは、すべてを説明するのではなく、納得に必要な順番で見せる。

Webの詳細情報は、Mobileでは以下の2カードに圧縮して取り込む。

1. 今回の相談の整理
2. 神社との意味の接続

この2つを追加することで、見た目はMobile、納得感はWebに寄せる。

## 次PR候補

# Mobile Shrine Detail Context Sections

- [ ] develop最新化
- [ ] feature/mobile-shrine-detail-context-sections 作成
- [ ] consultationSummary 相当をMobile詳細へ追加できるか確認
- [ ] shrineMeaning / actionMeaning 相当をMobile詳細へ追加できるか確認
- [ ] context がある場合のみ表示
- [ ] context がない場合は既存表示を維持
- [ ] 追加カードは最大2枚まで
- [ ] typecheck
- [ ] PR作成
