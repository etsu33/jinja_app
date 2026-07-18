> **Status: Reference**
>
> 本ドキュメントは、historyTheme別Dashboardの見方に関する設計背景を記録した参照資料である。
>
> 正確なEvent名・PayloadおよびKPI計算式は、関連するAnalytics契約文書および実装コードを最終的な正本とする。

# history_theme 別 Dashboard 設計

## 目的
history_theme ごとに、表示・詳細遷移・ルート起動・保存・Premium導線の差を確認する。

## Event Properties
- historyTheme
- shrineId
- source
- cardId
- visibility
- accessLevel
- resultSetId
- recommendationRank
- mode
- flow
- hasBirthdate

## KPI
- Impression数
- Detail CTR = shrine_detail_transition / concierge_result_impression
- Route CVR = route_open / shrine_detail_transition
- Premium Preview CTR = premium_preview_click / premium_preview_view
- Save Prompt CTR = save_prompt_click / save_prompt_view

## 見る単位
- historyTheme別
- accessLevel別
- recommendationRank別
- mode別
