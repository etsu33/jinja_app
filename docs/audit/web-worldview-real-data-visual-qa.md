# Web Worldview Real-data Visual QA Gate

## 1. Purpose

PR #2968 / #2974 で確立した KAMI MUSUBI Web Worldview
（Deep Ink Navy + restrained shrine-gold）が、実データ・認証済み状態・各種ステータス表示でも
破綻せず成立していることを確認する。

本監査は **実装ではなく観測と分類を先に行う Gate** とする。

Mother Ship decision:

> Semantic State Polish より先に Real-data Visual QA を行う。
> 状態色・Premium・selection・saved・disabled 等の再設計は、
> 実データ表示で問題が再現された箇所だけを根拠付きで後続 PR に切り出す。

理由:
- #2974 は Worldview 基盤を全 user-facing route へ展開したが、実データ表示を確認できない route / state が残った。
- 状態色には semantic responsibility があり、見た目だけで一括置換すると意味境界を壊す。
- 先に実データ状態を観測すれば、Worldview regression と既存 semantic-state 問題を分離できる。

## 2. Baseline

- Base branch: `develop`
- Baseline merge: PR #2974
- Baseline commit: `c2ed75e22d768b7916a410b5524b42b839b5f3a5`
- Web Worldview Foundation: PR #2968
- App-wide rollout: PR #2974

この監査中は Worldview Token / Backdrop / Frame の設計を変更しない。

## 3. Scope

### Primary real-data targets

1. Concierge
   - 相談入力後
   - 推薦結果
   - Top Recommendation Hero
   - Other Recommendations
   - Premium preview / Premium state
   - disabled / selection / notice states

2. Shrine Detail
   - 実在神社の詳細
   - Hero
   - Fact / Meaning
   - Judge / Proposal / Reflection
   - Deep Dive
   - Save / Favorite
   - Goshuin section

3. Goshuin
   - 一覧あり
   - 空状態
   - 新規登録
   - 公開プロフィール表示

4. MyPage / Favorites
   - 認証済み通常状態
   - 空状態
   - データあり
   - 履歴詳細
   - settings

5. Map
   - map tile loaded
   - shrine marker / panel
   - current-location related UI
   - sheet / overlay / sticky UI

6. Ranking / Populars
   - データあり
   - top-ranked state
   - card states

7. Billing / Premium
   - current plan
   - upgrade
   - manage
   - success / cancel
   - CTA hierarchy

### Secondary targets

- Auth
- Shrine submission
- Consultation history
- Public user pages
- Terms / Privacy
- 404 / error boundaries

Secondary target は regression が見つかった場合だけ深掘りする。

## 4. Viewport Matrix

最低限:

- 375 px
- 390 px
- 430 px
- 1280 px

実データ確認では 390 px を主観測幅とし、
問題が見つかった画面だけ 375 / 430 / 1280 へ横展開して確認する。

## 5. Visual QA Contract

各対象 state で以下を確認する。

- Header / page / Footer に色の継ぎ目がない
- page ground が Deep Ink Navy のまま
- WorldviewBackdrop が 1 画面 1 個
- Gold Path が本文の可読性を邪魔しない
- 文字コントラストが崩れていない
- white / light neutral の accidental surface が残っていない
- Forest green の neutral surface が再出現していない
- semantic color が意味を維持している
- disabled が disabled と認識できる
- selected / saved が neutral card と区別できる
- success / warning / error が相互に区別できる
- Premium が通常 UI と区別できる
- focus ring が確認できる
- sticky / fixed UI が backdrop より前面
- dialog / sheet / modal / overlay が正常
- 画像・地図・御朱印画像が Worldview 装飾に負けない
- 横スクロールが発生しない
- 実データの長文で overflow / clipping が起きない

## 6. Finding Classification

発見事項は必ず次のいずれかに分類する。

### A. WORLDVIEW_REGRESSION

#2974 によって発生した回帰。

例:
- Navy 化による文字不可視
- Backdrop の重複
- Header / Footer seam
- token migration による contrast regression

対応:
- 本監査 PR では記録のみ。
- 修正は follow-up fix PR。

### B. PRE_EXISTING_SEMANTIC_STATE

#2974 より前から存在した状態色 / semantic UI の問題。

例:
- light emerald surface + ivory text
- Forest 由来 disabled / saved / selection color
- semantic state の contrast 不足

対応:
- Semantic State Polish 候補へ送る。

### C. CONTENT_DATA_STRESS

実データの長さ・件数・画像比率で露呈した問題。

例:
- 長い神社名
- 長文 explanation
- 多数 tag
- 画像欠損

対応:
- 内容に応じて専用 UI fix へ分離。

### D. FUNCTIONAL_NON_VISUAL

見た目ではなく挙動の問題。

例:
- 認証 redirect
- API error
- map loading failure
- CTA navigation

対応:
- 本監査から分離し、該当機能 track へ送る。

### E. PASS

実データ state でも問題なし。

## 7. Evidence Record

各対象ごとに以下を記録する。

| Route / State | Auth | Data | 390px | Other widths | Finding | Classification | Follow-up |
|---|---|---|---|---|---|---|---|
| /concierge result | no | real | PASS (390x844) | 455px provisional PASS | Navy ground / header continuity / card hierarchy / long-form text / gold CTA remain readable; no horizontal overflow observed | PASS | none |
| /shrines/[id] | no | real | PASS (390x844) | 455px provisional PASS | Concierge→Shrine Detail continuity preserved; cards, history text, meaning sections remain readable | PASS | semantic-state follow-up only |
| /shrines/[id]/goshuins | no | real | TODO | TODO if needed | TBD | TBD | TBD |
| /mypage | yes | real | TODO | TODO if needed | TBD | TBD | TBD |
| /favorites | yes | real | TODO | TODO if needed | TBD | TBD | TBD |
| /goshuin/new | yes | real | TODO | TODO if needed | TBD | TBD | TBD |
| /map | maybe | real | TODO | TODO if needed | TBD | TBD | TBD |
| /populars | no | real | TODO | TODO if needed | TBD | TBD | TBD |
| /ranking | no | real | TODO | TODO if needed | TBD | TBD | TBD |
| /billing | yes | real | TODO | TODO if needed | TBD | TBD | TBD |
| /billing/manage | yes | real | TODO | TODO if needed | TBD | TBD | TBD |

Screenshot 自体は repository へ commit しない。
PR 本文または GitHub attachment / QA note で evidence を参照する。


### 7.1 Concierge / Shrine Detail — 390px formal observation (2026-09-24)

Input used:

> 最近、仕事について少し迷っています。今後の方向性を整理したくて、落ち着いて考えられる神社に行きたいです。人が多すぎず、静かに参拝できる場所が希望です。

Evidence:
- user-provided browser screenshots
- Chrome responsive viewport: **390 x 844**
- flow: Home input → `/concierge?tid=9` → `/shrines/59?ctx=concierge&tid=9`
- earlier 455px screenshots are treated as provisional corroborating evidence only

Formal findings:

| Area / State | Finding | Classification | Follow-up |
|---|---|---|---|
| Home input at 390px | Header controls fit, input surface remains within viewport, Gold Path stays subordinate, no visible horizontal overflow | PASS | none |
| Concierge result / top recommendation | Deep Ink Navy ground, surface hierarchy, title, reference info and recommendation copy remain readable at 390px | PASS | none |
| Concierge emerald semantic labels | Emerald labels remain readable but visually sit outside the Navy + shrine-gold neutral language | PRE_EXISTING_SEMANTIC_STATE | Semantic State Polish candidate |
| Long-form concierge copy | Line length and wrapping remain readable; no clipping or overflow observed in supplied evidence | PASS | none |
| Shrine Detail / real shrine data | Shrine title, address, deity chips, history cards and meaning sections remain readable at 390px; route continuity is preserved | PASS | none |
| Premium / login deeper-meaning block | Dark green surface and gold text remain readable but visually stand apart from the canonical Navy neutral system | PRE_EXISTING_SEMANTIC_STATE | Semantic State Polish candidate |
| Header / page continuity | No Forest / white seam observed in supplied 390px evidence | PASS | none |
| Gold Path readability | Decorative line remains low-contrast and does not visibly cross text at a disruptive intensity | PASS | none |
| Horizontal layout | No visible horizontal scrolling or viewport escape in supplied evidence | PASS | none |

Formal classification for this pass:

```text
WORLDVIEW_REGRESSION            = 0 observed
PRE_EXISTING_SEMANTIC_STATE     = 2 observed patterns
CONTENT_DATA_STRESS             = 0 observed
FUNCTIONAL_NON_VISUAL           = 0 observed in this pass
PASS                            = Concierge / Shrine Detail core Worldview
```

The two semantic-state patterns are **not blockers for PR #2974's Worldview rollout**.
They are candidates for a later Semantic State Polish PR and must not be changed inside this audit PR.

Not covered by this evidence:
- Concierge loading state
- explicit disabled state
- selected/saved state
- authenticated Premium state
- Footer end-of-page seam
- 375 / 430 / 1280 expansion for these real-data states

Per the viewport policy, extra widths are required only where a problem is found.
The semantic-state findings are color-language issues rather than 390px layout failures, so no responsive expansion is required for the core Concierge/Shrine layout at this point.

## 8. No-change Areas

本監査 PR では変更しない。

- Worldview Token 実値
- WorldviewBackdrop geometry
- WorldviewFrame architecture
- Recommendation / ranking logic
- Concierge interpretation logic
- Backend
- Django / DB / migration
- API contract
- Analytics
- Authentication behavior
- Billing behavior
- Map provider behavior
- Mobile app
- semantic-state color values
- CTA hierarchy
- 404 copy

問題を見つけても、この PR に修正を混ぜない。

## 9. STOP Rules

以下の場合は推測で進めず STOP して記録する。

- 認証済み state を安全に作れない
- Production data の再現に write が必要
- 課金操作が実決済を発生させる
- 本番アカウント / secret の追加が必要
- Production DB を直接編集する必要がある
- 外部 provider の有料 action が必要
- observed issue が visual か functional か判定不能

## 10. Done Criteria

- Primary target をすべて確認または NOT VERIFIED と明記
- 各 finding を A〜E に分類
- Worldview regression と pre-existing semantic issue を分離
- Semantic State Polish に送る対象を確定
- 実装修正を混ぜない
- Mother Ship 向けの次 PR 分割案を作る
- 本 PR は audit 記録のみで close / merge 可能な状態にする

## 11. Next Gate

本監査完了後、Mother Ship が以下を確定する。

1. WORLDVIEW_REGRESSION fix PR の要否
2. Semantic State Polish の対象 Token / Component
3. CTA hierarchy の要否
4. 実データ content-stress fix の分割
5. 追加 QA が必要な route

Semantic State Polish は、この監査の evidence を正本として開始する。
