# Mobile Web Parity Audit

## 目的

Mobile版をWeb版と同じ思想の体験へ近づけるため、コンシェルジュ文言・詳細画面・参拝後導線の差分を整理する。

## Web版の特徴

### Concierge

Web版には以下の導線がある。

- 誕生日・ご利益・参拝スタイルを相談テーマの補助条件として扱う
- 条件に合わせて再提案できる
- 近い神社を地図で見る導線がある
- 相談条件の表示がある

### Shrine Detail

Web版には以下がある。

- 推薦理由
- 提案
- 意味
- ご利益の詳細表示
- action_state による表示分岐
- 参拝済み記録
- 参拝後の振り返り
- reflection保存

## Mobile版の現状

### Concierge

Mobile版には以下がある。

- 今の相談とのつながり
- 推薦理由
- 今の相談から結ばれた神社
- ご縁を結び直しています
- 条件を変える時だけ、追加で相談する

評価:
- 文言の世界観はMobile版の方がKamimusubiらしい
- ただし、条件追加・再提案・参拝スタイルの構造はWeb版より弱い

### Shrine Detail

Mobile版には以下がある。

- 神社名
- 所在地
- ご利益タグ
- 参拝前のヒント
- 神社について
- お気に入り
- 地図で経路確認

不足:
- なぜこの神社なのか
- 今の相談とのつながり
- action suggestion
- 参拝済み記録
- 参拝後の振り返り
- reflection保存

## 差分整理

### Mobileに優先して追加すべきもの

1. Shrine Detail v2
   - explanationカード
   - recommendation reason
   - action suggestion
   - visit_done
   - reflection

2. Concierge condition layer
   - 相談条件表示
   - 参拝スタイル表示
   - 条件変更の再提案導線

3. Home inline style cleanup
   - UX差分ではなく保守性改善として後回し

## Shrine Detail v2 TODO

- [ ] APIレスポンスから explanation.summary を受け取る
- [ ] explanation.reasons をMobile詳細で表示する
- [ ] 「なぜこの神社なのか」カードを追加する
- [ ] action_suggestions を表示する
- [ ] visit_done CTAを追加する
- [ ] visit_done後に参拝後カードを表示する
- [ ] reflection入力導線を追加する
- [ ] reflection保存APIと接続する

## 判断

Mobile版をWeb版に近づけるには、まずHome UIではなく Shrine Detail v2 を優先する。

理由:
- Web版との差が最も大きいのは詳細画面のMeaning Layer
- コンシェルジュ文言はMobile版も悪くない
- Homeのinline style整理は保守性改善であり、体験差分の本丸ではない
