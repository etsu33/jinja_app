> **Status: Active**
>
> 本ドキュメントは、Journey Timeline の現行体験仕様を管理する正本文書である。
>
> 正確なEvent生成、API契約、Serializer、Timeline構築、表示順および物理実装は、関連する実装コードおよびテストを最終的な正本とする。

# Journey Timeline Design

## 概要

Journey Timeline は、KAMI MUSUBI における「ご縁の歩み」を記録する体験レイヤーである。

本プロダクトは神社を推薦して終了するサービスではない。

相談し、

神社の提案を受け、

参拝し、

感じたことを残し、

再び相談する。

Journey Timeline は、その一連の体験を一本の時間軸として接続する。

Timeline の目的は履歴管理ではない。

ユーザー自身が

「どんな悩みから始まり」

「なぜその神社が提案され」

「実際に参拝し」

「どのような変化があったのか」

を自然に振り返れることを目的とする。

---

## Journey Timeline の役割

Journey Timeline は以下を一つの体験として扱う。

相談

↓

神社提案

↓

参拝

↓

振り返り

↓

次回相談

この循環を繰り返すことで、

KAMI MUSUBI は神社検索アプリではなく、

人生の伴走アプリとして体験を積み重ねる。

---

## Design Principles

Journey Timeline は以下の原則で設計する。

・相談からご縁が育つ流れを一本で扱う

・Event と State を明確に分離する

・途中で終了することを正常系とする

・Timeline は出来事だけを表示する

・状態はTimelineとは独立して管理する

・実装ではなく体験を仕様として定義する

---

## Information Architecture

記録

├ ご縁の歩み（Journey Timeline）

└ 保存した神社（Favorite）

Journey Timeline は「出来事」を扱う。

保存した神社は「現在の状態」を扱う。

両者は役割を分離する。

---

## Event と State

Journey Timeline は Event のみを表示する。

現在のMVPで扱う Event は以下とする。

・相談した

・神社が提案された

・参拝した

・振り返りを書いた

State は現在の状態を保持する。

例

・お気に入り

・保存済み

・将来的な公開設定

State は Timeline 上へ履歴として並べない。

必要に応じて各カードの補助表示として扱う。

---

## Journey Event

現行MVPで扱う Event は以下とする。

consultation_created

相談を開始したことを表す。

ユーザーが入力した最初の相談内容を保持する。

---

recommendation_shown

AI が神社を提案したことを表す。

Journey Timeline では、

・提案神社

・提案理由

・History Theme

・ご利益

・Action Suggestion

を補足情報として表示する。

Recommendation Reason や Action Suggestion は

Journey Event 自体ではなく、

Recommendation Event の補足情報として扱う。

---

visit_completed

神社へ参拝した事実を表す。

Visit は「行った」という出来事であり、

評価や感想は含まない。

参拝メモが存在する場合は補助表示する。

---

reflection_created

参拝後に振り返りを書いたことを表す。

Reflection は

・本文

・History Theme

・気分の変化

を保持する。

Reflectionは、Visitに接続できる体験情報として扱う。

Visitとの関連を確認できないReflectionは、単独のReflection Eventとして表示できる。

---

## Visit と Reflection の関係

Visit は

「神社へ行った」

という事実である。

Reflection は

「その参拝が自分にどのような意味を持ったか」

を記録する。

Journey Timeline では、

Visit を一つの体験の起点として扱う。

Reflection が存在する場合は、

Visit と Reflection を一つの体験単位として表示する。

これにより、

「行った」

「感じた」

が分断されず、

一つの参拝体験として読み返せる。

Journey Timeline は

Visit が存在し、

Reflection が存在しない状態も正常系とする。

後日 Reflection が追加された場合は、

その Visit に接続された体験として表示する。

未接続の Reflection が存在する場合は、

単独の Reflection Event として表示する。

関連付け方法、

時間判定、

距離判定、

ペアリングアルゴリズムなどの物理実装は

Backend Service および Mobile 実装の責務とする。

---

## Timeline UI

Journey Timeline は、発生日時を基準とした時系列で表示する。

現行MVPでは、直近の出来事を確認しやすくするため、新しいEventから順に表示する。

Timelineは表示順にかかわらず、過去から現在までの出来事が積み重なる体験として扱う。

Timeline 上には Event のみを表示する。

カードは Event ごとに役割を持つ。

相談カード

・相談内容

・相談日時

提案カード

・神社

・提案理由

・History Theme

・ご利益

・Action Suggestion

参拝カード

・神社

・参拝日時

・参拝メモ

Reflection が存在する場合は、

同一カード内へ

・振り返り

・History Theme

・気分の変化

を表示する。

Journey Timeline は

一つの Visit を中心とした体験単位を優先して表示する。

---

## Recommendation の補足情報

Recommendation Event は

単に

「神社を提案した」

だけではなく、

提案理由も表示対象とする。

Journey Timeline では以下を補足表示する。

・Recommendation Reason

・History Theme

・Matched Benefits

・Action Suggestion

これらは Recommendation Event の補助情報であり、

独立した Event ではない。

Action Suggestion は

Journey Timeline において

「参拝前にできること」

として表示する。

Journey Timeline は

Action Suggestion の生成方法や判定ロジックを保持しない。

それらは Recommendation Layer の責務とする。

---

## MVP Scope

### Phase1

Journey Timeline が扱う Event

・相談

・提案

・参拝

・振り返り

Journey Timeline は

相談から振り返りまでの一本化を最優先とする。

---

### Phase2

将来的に以下を追加する。

・御朱印

・写真

・検索

・比較

・タグ

・感情推移

・統計

これらは Timeline の拡張機能として扱う。

現行MVPには含めない。

---

## Free / Premium

Journey Timeline 自体は

無料ユーザーでも利用できる。

Premiumでは、長期履歴、検索、比較、写真、御朱印、感情推移などの追加体験を将来的な候補として扱う。

具体的な提供範囲は、`docs/product/premium-experience.md`を正本とする。

KPI や計測方法は

Analytics 文書で管理する。

Journey Timeline 文書では保持しない。

---

## 責務境界

Journey Timeline は体験仕様のみを管理する。

以下は Journey Timeline の責務とする。

・Timeline が扱う Event の意味

・Timeline に表示する情報

・Visit と Reflection を一つの体験として扱う方針

・Event と State の責務分離

・Journey 全体のUX

以下は実装側の責務とする。

・Event の生成

・Serializer

・API Response

・Timeline の構築処理

・Visit と Reflection の関連付け

・並び順

・検索処理

・ペアリングアルゴリズム

・表示コンポーネント

Journey Timeline は

実装方法を規定しない。

---

## 実装との対応

Journey Timeline の物理仕様は

実装コードおよびテストを正本とする。

対象例

Backend

・Journey Timeline Service

・Journey Timeline API

・Journey Serializer

・Service Test

・API Test

Mobile

・Journey Screen

・Journey Timeline Builder

・Timeline Pairing Logic

Journey Timeline 文書は

それらの体験上の意味のみを定義する。

---

## Migration

Journey Timeline は

以下の履歴画面を一つの体験へ統合する。

・相談履歴

・参拝履歴

・振り返り履歴

↓

Journey Timeline

Journey Timeline は

ユーザーから見える「ご縁の歩み」を提供する。

内部実装は

複数の Event から構成されていてもよい。

---

## Design Philosophy

Journey Timeline は

記録アプリではない。

相談し、

提案を受け、

神社へ行き、

感じたことを残し、

再び相談する。

この循環そのものを、

一つの人生の歩みとして積み重ねる場所である。

Journey Timeline は

過去を保存するためではなく、

未来の行動を支えるための記憶を育てる体験レイヤーである。

途中で終わる Journey も、

振り返りだけが残る Journey も、

何度も相談を繰り返す Journey も、

すべて正常な Journey として扱う。

完成した Timeline は、

出来事の一覧ではなく、

ユーザー自身の「ご縁の歩み」として静かに積み重なっていく。

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/kami-musubi-experience-design.md`
- `docs/product/visit-reflection-flow.md`
- `docs/product/action_suggestion_v4.md`
- `docs/product/recommendation-v4-interpreter-contract.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/premium-experience.md`
- `docs/product/reflection-timeline-design.md`
- `docs/core/architecture.md`
- `docs/core/meaning-layer-connection.md`

AnalyticsのEvent、Payload、Property、Funnel、KPIおよび集計方法は、`docs/analytics/`配下の正本文書を参照する。

正確なJourney Event、API Response、Serializer、Field、Timeline構築、VisitとReflectionの関連付け、並び順および表示処理は、関連するBackend・Mobile実装とテストを正本とする。

---

## 更新ルール

- 本書はJourney Timelineの現行体験仕様を管理する。
- Timelineが扱うEventの追加、削除または意味変更がある場合は、本書を更新する。
- EventとStateの責務境界が変更された場合は、本書を更新する。
- VisitとReflectionの体験上の接続方針が変更された場合は、本書を更新する。
- Free / Premiumの体験境界が変更された場合は、本書を更新する。
- Event名、API、Serializer、Field、Payload、並び順、関連付け処理および表示コンポーネントは、本書で重複管理しない。
- Event、Payload、Property、FunnelおよびKPIは、Analytics文書で管理する。
- 写真、御朱印、検索、比較、感情推移および統計は、実装または正式仕様化されるまで将来構想として扱う。
- TODO、PR計画、実装進捗、テスト手順および作業履歴は、本書へ記載しない。
