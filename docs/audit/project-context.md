> **Status: Archive**
>
> 本ドキュメントは、KAMI MUSUBIのProject Contextを一か所へ集約する構想段階で作成された未完成記録である。
>
> 現行仕様、開発フェーズ、正本文書の判断には使用しない。
>
> 現在の参照先は以下とする。
>
> - 全体設計：`docs/core/architecture.md`
> - Meaning Layer：`docs/core/meaning-layer.md`
> - Meaning接続：`docs/core/meaning-layer-connection.md`
> - Narrative方針：`docs/core/narrative-guideline.md`
> - 開発Roadmap：`docs/core/roadmap.md`
> - Product仕様入口：`docs/product/README.md`
> - Knowledge Base入口：`docs/knowledge/README.md`

# KAMI MUSUBI Project Context

## 目的

本書は、KAMI MUSUBIのプロダクト概要・中核体験・設計原則・開発状況を一か所にまとめる目的で作成された初期構想文書である。

その後、責務ごとにCore・Product・Knowledge文書へ分離されたため、本書は当時の情報集約方針を残すArchiveとして扱う。

---

## 当時想定していた中核体験

KAMI MUSUBIでは、神社を検索すること自体ではなく、ユーザーの相談や現在の状態から行動と振り返りへ接続する体験を中核に置く構想だった。

```text
相談
↓
推薦
↓
行動
↓
参拝
↓
振り返り
↓
再相談
```

現在の体験仕様は、以下を正本とする。

- `docs/product/concierge-first-final-spec.md`
- `docs/product/visit-reflection-flow.md`
- `docs/core/roadmap.md`

---

## 当時想定していた設計原則

初期段階では、以下の原則をプロジェクト全体へ適用する方針としていた。

- 神社検索ではなく状態整理を起点とする
- 宗教的・心理的な断定を行わない
- Backendを業務判定の正本とする
- Fact・Meaning・Runtimeを分離する
- 占術情報は補助シグナルとして扱う
- 神社そのものではなく、ユーザーの変化を主役にする

現在の正確な設計原則と責務境界は、以下を参照する。

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/narrative-guideline.md`
- `docs/product/concierge-first-final-spec.md`

---

## 当時想定していたシステム境界

Project Contextでは、システムを以下の領域へ分けて整理する構想だった。

### Backend

- 相談解釈
- 推薦判定
- 保存
- 認証
- 課金
- Analytics用データ

### Frontend

- 入力
- 表示
- 画面遷移
- 行動導線
- Analytics Event送信

### Knowledge Base

- 神社情報
- Taxonomy
- Copy Rule
- Recommendation説明
- Action・Reflection補助

### Analytics

- Recommendation
- Detail
- Route
- Visit
- Reflection
- 継続利用

現在の責務境界は、`docs/core/architecture.md`および各Product正本を参照する。

---

## 正本文書の分離

本書で一括管理する予定だった情報は、現在は以下へ分離されている。

| 領域 | 現在の正本 |
|---|---|
| Architecture | `docs/core/architecture.md` |
| Meaning Layer | `docs/core/meaning-layer.md` |
| Meaning接続 | `docs/core/meaning-layer-connection.md` |
| Narrative | `docs/core/narrative-guideline.md` |
| Roadmap | `docs/core/roadmap.md` |
| Concierge | `docs/product/concierge-first-final-spec.md` |
| Recommendation Mode | `docs/product/concierge-modes.md` |
| Visit / Reflection | `docs/product/visit-reflection-flow.md` |
| Product文書入口 | `docs/product/README.md` |
| Knowledge Base入口 | `docs/knowledge/README.md` |

---

## 本書が保持するもの

- Project Contextを一文書へ集約しようとした背景
- 相談から振り返りまでを一本の体験として捉えた初期構想
- Backend・Frontend・Knowledge Base・Analyticsの分離方針
- 現在のCore・Product・Knowledge文書へ至る前段階の考え方

---

## 本書が扱わないもの

- 現在のプロダクト仕様
- 現在の開発フェーズ
- 現在の優先順位
- 正本文書一覧の管理
- API契約
- Recommendation契約
- UI仕様
- Analytics契約
- TODO
- PR候補
- 実装計画
- 作業進捗

---

## 関連ドキュメント

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/narrative-guideline.md`
- `docs/core/roadmap.md`
- `docs/product/README.md`
- `docs/knowledge/README.md`

---

## 更新ルール

- 本書は初期Project Context構想のArchiveとして保持する
- 現行仕様や開発状況に合わせて更新しない
- 当時の意図に重大な事実誤認が確認された場合のみ修正する
- TODO、PR候補、現在の開発フェーズ、作業進捗は記載しない
