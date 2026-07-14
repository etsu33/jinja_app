# Docs Directory Consistency Audit

## 目的

本監査は、`docs/` 配下の文書構成を確認し、正本・参照・Archiveの管理状況、およびディレクトリごとの責務分離状況を整理することを目的とする。

本書は監査結果の記録であり、仕様変更や実装計画は扱わない。

---

## 監査概要

### 対象

- `docs/` 配下の Markdown 文書
- README
- Status管理
- ディレクトリ構成
- 正本文書への参照

### 監査時点

監査実施時点の `develop` ブランチを対象とした。

---

## 監査結果

### 文書構成

|項目|件数|
|---|---:|
|docs配下ファイル総数|181|
|Markdown文書|179|

### Status管理

|Status|件数|
|---|---:|
|Active|9|
|Reference|11|
|Archive|22|

Statusが付与されている文書については、分類ルールが適用されていることを確認した。

一方で、多くの文書はStatus未付与であり、今後の分類対象となる。

### Status未付与文書

Status未付与文書は137件である。

未付与文書は主に以下へ集中している。

|ディレクトリ|件数|
|---|---:|
|docs(root)|46|
|docs/audit|41|
|docs/analytics|25|
|docs/knowledge|8|
|docs/core|5|
|その他|12|

---

## README整合性

以下のREADMEを確認した。

- docs/README.md
- docs/product/README.md
- docs/knowledge/README.md
- docs/concierge/README.md

監査時点では、READMEから参照される文書に参照切れは確認されなかった。

---

## Status文書の参照整合性

Statusを付与済みの文書について、`docs/`配下へのリンクを確認した。

監査時点では参照切れは確認されなかった。

---

## ディレクトリ構成

現時点では、以下の役割分離が確認できる。

|ディレクトリ|責務|
|---|---|
|core|全体設計・アーキテクチャ・ロードマップ|
|product|プロダクト仕様・UX・体験設計|
|knowledge|知識モデル・Meaning・Recommendation基盤|
|audit|監査・レビュー・整合性確認|
|analytics|分析・計測設計|
|infra|インフラ運用|
|ops|運用手順|

責務の大きな重複は確認されなかった。

---

## Archive運用

Archive文書について確認した結果、

- Status表記
- 正本文書への参照
- Archiveとしての位置付け

がおおむね統一されていることを確認した。

旧Phase文書や旧設計書についても、現行仕様ではなく履歴として扱う方針が反映されている。

---

## 判断

現時点では、

- 正本文書
- 参照文書
- Archive文書

の三層構造は維持されている。

また、READMEおよびStatus付与済み文書については重大な参照不整合は確認されなかった。

一方で、Status未付与文書は依然として多数存在しており、今後カテゴリ単位で整理を進める余地がある。

---

## 今後の監査対象

本監査では個別文書の分類変更は行わない。

今後は以下の単位で順次監査する。

- docs/root
- docs/analytics
- docs/audit
- docs/core
- docs/knowledge
- docs/product

---

## 更新ルール

- 本書はdocsディレクトリ全体の監査結果を記録する文書とする
- 個別仕様や実装内容は各正本文書で管理する
- Status変更や文書移動が行われた場合のみ更新する
