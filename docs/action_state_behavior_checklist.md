# Action State 挙動確認チェックリスト

## Recommendation Payload
- [ ] action_state が recommendation に含まれている
- [ ] visited / reflected / saved など状態が正しい

## 詳細ページ表示
- [ ] 参拝後文言が visited / reflected の場合のみ表示
- [ ] none / detail_viewed / saved の場合は非表示
- [ ] followup prompt の表示条件が正しい

## Analytics / Observation
- [ ] save / detail_view / route_open / visit_done イベントが payload に正しく反映
- [ ] observation debug に action_state が反映されている

## Premium / Free 振り分け
- [ ] Free ユーザーは個人用文脈なし
- [ ] Premium ユーザーは個人文脈・過去履歴との接続あり
