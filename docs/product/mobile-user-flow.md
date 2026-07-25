> **Status: Active**
>
> 本ドキュメントは、Mobile／Expo Webにおける主要ユーザー導線(主導線・サブ導線・共通合流地点・地図の段階公開方針)を管理する正本文書である。
>
> Routeの物理構造、Navigation実装、画面コンポーネントおよびテストの最終的な正本は、`apps/mobile/`配下の現行コードおよびテストである。本書は導線の優先関係と責務境界のみを管理し、実装の詳細を重複管理しない。
>
> 本書は`docs/audit/mobile-user-flow-inventory.md`(監査記録)を根拠として作成された。監査文書はAuditであり、現行仕様判断の正本ではない。本書との間で記載が食い違う場合は、より新しい実装・テストの確認結果を優先する。

# Mobile User Flow

## 1. Status

Active。Mobile／Expo Webの主要ユーザー導線に関する体験方針の正本として、実装判断に使用してよい。

## 2. 目的

Mobile／Expo Webにおける現行のユーザー導線を、実装判断に使える仕様として固定する。

固定する対象は以下である。

- 主導線・サブ導線・共通合流地点の優先関係
- 地図(Web／Native)の責務と段階公開方針
- 一覧・人気神社の責務
- 記録から再相談への将来接続方針
- Premium・認証との責務境界
- 初期公開範囲とDeferred範囲の分離

本書は、コード変更・UI変更・Route変更・Analytics変更・機能削除の実行を目的としない。

## 3. 対象範囲

- `apps/mobile`(Expo Router、Native／Expo Web両対応)の主要ユーザー導線
- Home、Concierge、Search(一覧・地図・人気神社)、神社詳細、記録・Reflection、Premium、認証、の各画面が担う責務の優先関係

## 4. 対象外

- `apps/web`(Next.js)の画面別導線(別サーフェスであり、本書の対象外。`docs/audit/mobile-user-flow-inventory.md` 6.5節を参照)
- Route定義、Navigation実装、コンポーネント構造の物理仕様(`apps/mobile/app/`配下のコードおよびテストを参照)
- Analyticsのイベント名・Payload・KPI(`docs/analytics/`配下を参照)
- Recommendationのスコアリング・API契約の詳細(`docs/core/concierge-spec.md`を参照)
- Billing・Paywallの判定ロジック(`docs/product/billing-paywall.md`を参照)
- 具体的な実装スケジュール、PR計画

## 5. 基本方針

- KAMI MUSUBIの中心体験は、神社検索ではなく「相談から神社と出会う体験」である。
- 神社詳細は、複数の入口を持つ単一の共通合流地点として扱う。独立した主導線としては扱わない。
- 地図は、KAMI MUSUBIの主導線ではなく探索補助機能として扱う。地図が利用できない状態でも、主要フローを完遂できることを必須条件とする。
- Web地図とNative地図は、費用構造・provider構造が異なるため、同一の判断で扱わない。
- 延期(Deferred)は削除を意味しない。

## 6. 全体導線

```text
Home(相談条件入力)
├─ 主導線: 相談 → コンシェルジュ結果 → 神社詳細
└─ サブ導線: 神社を探す → 神社一覧 → 神社詳細
                                  ↓
                            (共通合流地点)
                                  ↓
                神社詳細: 経路確認・保存・参拝記録
                                  ↓
                        記録・振り返り(将来: 再相談へ接続)
```

主導線・サブ導線はいずれも神社詳細で合流する。神社詳細から先は、経路確認・保存・参拝記録・振り返りという共通の体験に接続する。

## 7. 主導線

**方針として固定する。**

```text
相談条件入力
↓
この相談からご縁を見る
↓
コンシェルジュ結果
↓
神社詳細
```

- 神社詳細は独立した優先順位ではなく、主導線の到達先である。
- コンシェルジュ結果から神社詳細へ進む際は、推薦理由等の追加コンテキストを保持する。
- 相談から神社と出会う体験を、KAMI MUSUBIの中心とする。

**事実(監査根拠)**: `docs/audit/mobile-user-flow-inventory.md` 10節・11節の確認によれば、Home画面(`apps/mobile/app/index.tsx`)の主CTA「この相談からご縁を見る」は、DOM順・視覚的重み(塗りつぶし背景)の両方でサブCTAより優先度が高い。コンシェルジュ結果画面(`apps/mobile/app/concierge/index.tsx`)から神社詳細への遷移のみが、推薦理由等4項目の追加コンテキストparamsを渡す(同文書14節)。この事実は、本書が主導線として固定する優先関係と一致している。

## 8. サブ導線

**方針として固定する。**

```text
Home
↓
神社を探す
↓
神社一覧
↓
神社詳細
```

- 自分で神社を探したいユーザー向けの補助導線である。
- コンシェルジュの代替ではなく、別の入口として扱う。
- 一覧からも、主導線と同じ神社詳細Routeへ合流する。

**事実(監査根拠)**: Home画面のサブCTA「神社を地図・一覧から探す」は`/search`へ遷移し(`docs/audit/mobile-user-flow-inventory.md` 10節)、Search画面内の一覧・地図いずれの経路からも`/shrines/${id}`という主導線と同一のRoute形状へ到達する(同文書14節)。

## 9. 神社詳細の責務

- 主導線とサブ導線の共通合流地点として扱う。
- 神社の公開情報、推薦文脈、経路確認、保存、参拝・記録への接続を担当する。
- 入口ごとの文脈差(コンシェルジュ経由か、一覧・地図経由か)は許容する。
- Routeは共通とする。
- 神社詳細自体を、Home上の独立した主導線として扱わない。

**事実(監査根拠)**: `docs/audit/mobile-user-flow-inventory.md` 14節によれば、神社詳細(`apps/mobile/app/shrines/[id].tsx`)へ到達する経路は7つ確認されており、いずれも同一のRoute形状(`/shrines/${id}`)へ到達する。一方で、Analytics上の`source`は経路によらず`"mobile_shrine_detail"`という固定値が送信されており、入口ごとの識別はできない。この識別不能な状態を本書の方針で解消することは意図しない。識別の要否は20節(未確定事項)で扱う。

## 10. 一覧の責務

- 自分で神社を探すユーザーの主要探索UIとして扱う。
- 座標欠損神社を除外しない。
- 地図が利用できない場合でも、神社選択と神社詳細への遷移を維持する。
- 神社名、所在地、必要最小限の判断材料を表示する。
- 深い推薦理由はコンシェルジュ側へ集約し、一覧では扱わない。
- 内部タグや過度な解釈を一覧へ持ち込まない。

**事実(監査根拠)**: `apps/mobile/lib/shrineMap.ts`の`toShrineMapPoints`は、id・nameが揃っていれば座標が欠損・不正でも項目を除外せず一覧に残す設計が実装済みである(`docs/audit/mobile-user-flow-inventory.md` 12.3節)。Web版・Native版いずれも、地図が利用できない・座標がない場合でも一覧からの選択・詳細遷移は維持される(同文書12.4節・12.6節)。

## 11. Web地図の責務

**方針として固定する。**

- Web地図は、初期公開MVPの必須機能から外す。
- `EXPO_PUBLIC_WEB_MAP_STYLE_URL`未設定で運用可能とする。
- 未設定時は一覧導線を維持する。
- MapLibre実装は削除しない。
- 外部provider契約、利用量、domain制限、QAが整った時点で、再有効化できる構造を維持する。
- Web地図は主導線ではなく、探索補助機能として扱う。
- 地図を使わなくても主要フロー(相談→コンシェルジュ結果→神社詳細、および一覧→神社詳細)を完遂できることを必須条件とする。

**事実(監査根拠)**: `apps/mobile/components/search/ShrineSearchMap.web.tsx`は、`EXPO_PUBLIC_WEB_MAP_STYLE_URL`が未設定の場合Mapを初期化せず、「地図を読み込めないため一覧を表示しています。」を表示して一覧導線を維持する実装が既に完了している(`docs/audit/web-map-tile-provider-selection.md`、`docs/audit/mobile-user-flow-inventory.md` 12.4節・13節)。本書はこの既存実装の挙動を前提として、未設定運用を初期公開時点の方針として明記するものであり、新たな実装は行わない。

**未確定事項**: 現行の「地図を読み込めないため一覧を表示しています。」という文言は、provider通信失敗時のfallback文言をそのまま流用したものである。初期公開において意図的にWeb地図を無効化する運用(11節の方針)を採る場合、この文言を「provider障害」を示唆しない通常の一覧UI向け文言へ変更するかどうかは、本書では判断しない。判断・実装は別PRで行う。

## 12. Native地図の扱い

**未確定事項として分離する。本書ではNative地図の削除・非表示を決定しない。**

- Native地図は`react-native-maps`を使用しており、WebのMapLibre GL JS＋MapTiler構成とは設定・費用構造が異なる(`docs/audit/mobile-user-flow-inventory.md` 13節)。
- react-native-mapsはiOS/Androidそれぞれの地図SDKに委譲する構成であり、実機配布時に必要となる地図SDK・APIキー・利用条件・費用がWeb地図と同一かどうかは、本書では断定しない。これらは別途確認する。
- Web地図を初期公開から外す判断と、Native地図を非表示にする判断を同一に扱わない。
- Native地図の表示継続、優先度、画面配置は、別PRで判断する。

## 13. 人気神社の責務

- 人気神社は主導線ではない。
- 一覧探索を補助する発見導線として扱う。
- 人気の算出根拠が未確定、または固定データに基づく場合、主UIより先に配置することを前提としない。
- 表示継続、配置、ランキング実装(`/ranking`)との統合は、別PRで判断する。
- 本書では削除を決定しない。
- 初期公開での位置づけは`Secondary`または`Candidate for defer`とする。

**事実(監査根拠)**: `docs/audit/mobile-user-flow-inventory.md` 12.5節によれば、Search画面内の「人気の神社」セクションは固定データ(`SHRINES`)由来であり、動的な人気度算出ロジックとの接続は確認できていない。また`/ranking`画面は実装済みだが、現在到達可能な入口が存在しない孤立画面である(同文書19節・20.1節)。

## 14. 記録・Reflection・再相談

**将来の体験循環として、方針にのみ含める。今回のPRではCTA・Route・保存仕様を実装しない。**

```text
相談
↓
神社詳細
↓
参拝
↓
記録・振り返り
↓
必要に応じて再相談
```

- 現行実装では、参拝記録・振り返り保存から新しい相談(コンシェルジュ)への直接導線は未実装である。
- この循環は、将来のProduct方針として本書に含める。
- 実装(CTA・Route・保存仕様)は別PRへ分離する。

**事実(監査根拠)**: `docs/audit/mobile-user-flow-inventory.md` 15.3節によれば、`apps/mobile/app/shrines/[id].tsx`内の`onVisitDone`・`onSaveReflection`はいずれも保存後の画面遷移を行わず、`"concierge"`という文字列は同ファイル内に1件も存在しない。記録・履歴系9画面のいずれにも`/concierge`または`/`への遷移コードは存在しない。

**文書間の関係**: `docs/product/visit-reflection-flow.md`(Active)は「次回相談との接続」を体験原則として既に定義しており(同文書「次回相談との接続」節)、本書の記述と方向性は一致している。ただし同文書は「正確な画面、CTA、Routeは実装とテストを正本とする」と明記しており、実装状況の確認は`docs/audit/mobile-user-flow-inventory.md`が担う。本書はこの2文書の記述を重複させず、優先関係の確認のみを行う。

## 15. Premiumとの責務境界

- Premiumは、地図の高機能化を主価値にしない。
- Premiumは、パーソナル理由、履歴、比較、継続理解、保存・記録拡張を担う。
- 一覧、基本的な神社詳細、外部経路案内は、地図providerとの契約状況とは別の責務である。
- Web地図の再有効化を、Premium契約条件として自動的に扱わない。
- 課金境界の変更は、別のProduct文書・別PRで判断する。

**事実(監査根拠)**: `docs/product/premium-experience.md`(Active)は既に「Map / Search を主価値にしない」「地図が高機能になる」を「置かない Premium 表現」として明記している。`docs/audit/mobile-user-flow-inventory.md` 16節の確認によれば、`apps/mobile/app/concierge/index.tsx`・Search画面・地図コンポーネントいずれにもPremiumゲーティングのコードは存在しない(grep 0件)。既存文書の方針と実装は一致している(MATCHES)。本書はこの既存の一致を踏襲し、新たな境界を定義しない。

## 16. 認証との責務境界

- 主導線(相談条件入力→コンシェルジュ結果→神社詳細)は、認証を必須としない。
- サブ導線(神社を探す→一覧→神社詳細)も、認証を必須としない。
- 保存・記録に関わる操作(お気に入り、参拝記録、振り返り保存、ご縁の歩み閲覧)の一部は認証を要求する。認証を要求する具体的な操作の範囲は、実装(`apps/mobile/components/common/AuthPrompt.tsx`とその呼び出し元)を正本とする。
- ログイン後の復帰先(returnTo)を主導線・サブ導線の設計要件とはしない。現状の挙動・改善要否は20節(未確定事項)で扱う。

**事実(監査根拠)**: `docs/audit/mobile-user-flow-inventory.md` 17節によれば、コンシェルジュ推薦フロー自体は認証不要(`AllowAny`)であり、認証要求は共通コンポーネント`AuthPrompt`経由の5箇所(`/records`のジャーニーカード、`/journey`、`/premium`、`/shrines/[id]`の3操作)に限定される。ログイン成功後は常に`/mypage`へ固定遷移し、呼び出し元へ戻る仕組みは実装されていない。

## 17. 初期公開範囲

初期公開に含める候補は以下である。

- Home相談条件入力
- コンシェルジュ
- コンシェルジュ結果
- 神社一覧
- 神社詳細
- 外部地図による経路確認
- 基本的な保存・参拝・記録
- Web地図未設定時の一覧利用

## 18. Deferred

以下は`Deferred`または`Candidate for defer`として整理する。**延期は削除を意味しない。**

- Web地図の本番provider有効化
- MapTiler契約
- 地図の本番相当QA
- Native地図の再配置判断
- 人気神社の算出ロジック改善
- 孤立画面(参拝履歴・振り返り履歴・相談履歴・最近見た神社・ランキング)の導線接続
- ランキング画面
- 最近見た神社
- 記録から再相談への実装
- Searchフィルター(`q`/`filters`)の接続、または削除判断

## 19. 現行実装との差分

以下は、`docs/audit/mobile-user-flow-inventory.md`が確認した「現行実装が本書の方針と異なる、または未達である点」である。本書はこれらの差分を即座に解消することを求めない。差分の解消は別PRで判断する。

| 差分 | 事実 | 本書との関係 |
| --- | --- | --- |
| 神社詳細のAnalytics source識別 | 7経路すべてが`source: "mobile_shrine_detail"`固定(監査14節) | 本書は神社詳細を共通合流地点として定義しているが、入口別の識別要否は未確定事項とする |
| Searchのフィルター機能 | Home→Search間で`q`/`filters`が渡されず、実装済みのフィルタリングロジックが使われていない(監査12.8節) | 本書は一覧の責務を定義するのみで、この差分の解消(接続または削除)はDeferredとする |
| 記録→再相談の接続 | 参拝・振り返り保存後に相談へ戻る導線が未実装(監査15.3節) | 本書は14節で将来循環として方針化するが、実装は別PRとする |
| Home画面の入力範囲 | `docs/product/concierge-first-final-spec.md`が「HomeHeroが担当しないもの」とする誕生日・ご利益・参拝スタイル詳細を、Home画面が`ConditionFieldsCard`として直接保持している(監査11.5節) | 本書はHome/Concierge間の入力配分そのものを再定義しないが、既存文書との不一致として認識する(20節) |
| 孤立画面 | `/visit-history`・`/reflection-history`・`/consultation-history`・`/recently-viewed`・`/ranking`は到達経路0件(監査19節・20.1節) | 18節でDeferredとする |
| Mobileの位置づけに関する文書間の不一致 | root`README.md`の「Mobile休眠運用」記述と、`docs/core/roadmap.md`の「Mobile本番配布準備」という記述、および実際の活発な開発履歴が一致していない(監査6.6節) | 本書はMobileを実装対象として扱う前提で書かれている。この前提の妥当性自体は20節の未確定事項とする |

## 20. 未確定事項

以下は本書では判断せず、別PRまたは母艦判断へ差し戻す。

- Native地図の表示継続・優先度・画面配置、および実機配布時に必要な地図SDK・APIキー・利用条件・費用の確認(12節)
- Web地図未設定時の一覧UI文言(「地図を読み込めないため一覧を表示しています。」)を、意図的な無効化向けの文言へ変更するか(11節)
- 人気神社の算出ロジックと`/ranking`実装との統合方針(13節)
- 5つの孤立画面(参拝履歴・振り返り履歴・相談履歴・最近見た神社・ランキング)を、導線接続の対象とするか削除対象とするか(18節)
- Search画面のAnalytics計装(Search/地図/Home CTAのイベントが現状0件であり、案の効果検証ができない状態にある。`docs/audit/mobile-user-flow-inventory.md` 18.2節・25節)
- 記録から再相談への具体的なCTA・Route・保存仕様(14節)
- 神社詳細への入口別Analytics識別の要否(9節)
- ログイン後のreturnTo機構の要否(16節)
- root`README.md`の「Mobile休眠運用」記述と、Mobileの実際の開発状況・`docs/core/roadmap.md`の記述との間にある文書間の不一致をどう扱うか(19節、`docs/audit/mobile-user-flow-inventory.md` 6.6節・25節)
- `docs/product/concierge-first-final-spec.md`に記載されたHome→Concierge遷移パラメータ設計(`theme`/`openFilter`)と、実装済みの遷移パラメータのどちらを正とするか(19節、監査11.5節)

## 21. 関連ドキュメント

本書と既存文書の責務は重複させない。

- `docs/product/concierge-first-final-spec.md` — Concierge Firstの入力・画面責務(HomeHero/ConciergeEntry/Filterの担当・非担当)を管理する正本。本書はConcierge First内部の画面責務を再定義しない。
- `docs/product/mobile-user-flow.md`(本書) — Mobile／Expo Web全体の導線と、各入口(Home/Concierge/Search/神社詳細/記録/Premium/認証)の優先関係を管理する正本。
- `docs/product/visit-reflection-flow.md` — 参拝・記録・振り返りの詳細体験(Visit/Reflectionの意味責務、次回相談との接続原則)を管理する正本。本書は14節でこの文書の方針と現行実装の差分のみを確認する。
- `docs/product/premium-experience.md` — Free／Premiumの体験価値境界を管理する正本。本書は15節でこの文書の方針と実装の一致を確認するのみで、境界自体は再定義しない。
- `docs/audit/mobile-user-flow-inventory.md` — 監査時点(コミット`0610dfd9`)の事実記録。正本ではない。本書が「事実(監査根拠)」として引用する一次情報源。
- `docs/core/roadmap.md` — 開発フェーズ全体の正本。Mobileの開発フェーズ上の位置づけは同文書を参照する。
- `docs/core/concierge-spec.md` — Concierge API契約の正本。

## 22. 更新ルール

- 本書はMobile／Expo Webの主導線・サブ導線・共通合流地点・地図の段階公開方針を管理する。
- 主導線・サブ導線の優先関係、または神社詳細の共通合流地点としての扱いが変更された場合は、本書を更新する。
- Web地図・Native地図の段階公開方針が変更された場合(例: `EXPO_PUBLIC_WEB_MAP_STYLE_URL`の本番設定、Native地図の再配置決定)は、本書を更新する。
- Premium・認証との責務境界そのものが変更された場合は、本書と`docs/product/premium-experience.md`・`docs/core/authentication-flow.md`との整合を確認する。
- Route、Navigation、コンポーネント構造、Analyticsイベント名・Payload、API契約は本書で重複管理しない。
- 実装が本書の方針から乖離した場合は、19節(現行実装との差分)を更新し、乖離の解消要否を20節(未確定事項)または別Audit文書へ送る。
- TODO、PR計画、実装進捗、作業履歴は本書へ記載しない。
