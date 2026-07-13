> **Status: Archive**
>
> 本ドキュメントは、Google Docs とリポジトリ間の統合作業方針を記録したアーカイブである。
>
> 現行の仕様判断には使用しない。
>
> 最新のプロダクト仕様は以下を正本とする。
>
> - `docs/product/README.md`
> - `docs/product/concierge-first-final-spec.md`
> - `docs/product/product-document-audit.md`

# Product Doc Consolidation

## 目的

Google Docs の Product ドキュメントを、現行のプロダクト仕様へ統合するための方針を記録する。

本書は統合作業の履歴を保存することを目的とし、現行仕様の判断には利用しない。

---

## 統合方針

Google Docs の Product ドキュメントは、リポジトリ内の正本ドキュメントを参照する構成へ整理する。

```text
Google Docs
        │
        ▼
README
        │
        ▼
各正本ドキュメント
```

Google Docs 側では仕様を重複管理せず、最新仕様への入口として利用する。

---

## 当時の統合対象

- Concierge First
- HomeHero
- Concierge Entry
- Filter
- Need Mode
- Compat Mode
- Meaning Translation
- Explore

---

## 統合方針

- 古いワイヤーフレームは現行仕様へ置き換える
- 重複する仕様は削除する
- Google Docs を単独の正本にしない
- 実装判断は Git リポジトリ内の正本を参照する

---

## 現行の正本

現在の仕様は以下のドキュメントで管理する。

- `docs/product/README.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/consultation-theme-taxonomy.md`
- `docs/product/history-theme-taxonomy.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/visit-reflection-flow.md`
- `docs/product/action_suggestion_v4.md`

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/product-document-audit.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/core/architecture.md`

---

## 更新ルール

- 本書は統合作業の履歴として保持する
- 現行仕様の変更では更新しない
- 新たな統合作業を行う場合のみ更新する
- 実装判断・仕様判断は正本ドキュメントで管理する
