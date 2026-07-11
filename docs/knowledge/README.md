# KAMI MUSUBI Knowledge Base

## 目的

KAMI MUSUBIが、神社の事実をどのように意味へ変換し、
推薦・行動提案・振り返りへ接続するかを定義する。

このKnowledge Baseは、LLMや実装担当者が変わっても、
KAMI MUSUBIらしい提案品質を維持するための正本とする。

## ドキュメント構成

| ドキュメント | 責務 |
| --- | --- |
| shrine-profile-spec.md | 神社知識モデルと推薦可能品質を定義 |
| shrine-data-guide.md | 神社データの入力・出典・品質基準を定義 |
| meaning-layer-spec.md | 事実を意味へ変換するルールを定義 |
| recommendation-copy-guide.md | 推薦理由の文章構造を定義 |
| action-guide.md | 行動提案の生成原則を定義 |
| reflection-guide.md | 振り返りの問いと接続方法を定義 |
| glossary.md | 共通用語と命名基準を定義 |

Knowledge Base（Single Source of Truth）
        ↓
Database
        ↓
Meaning Layer
        ↓
Prompt
        ↓
Backend
        ↓
Frontend
        ↓
Analytics

## 依存関係

神社プロフィール
↓
神社データ入力
↓
意味レイヤ
↓
推薦文
↓
行動提案
↓
振り返り

## 更新ルール

- 事実と解釈を分離する
- 宗教的・心理的な断定をしない
- 推薦理由は神社データに基づく
- 変更時は関連ドキュメントとの整合を確認する
- DB・Prompt・UIへ反映する前にKnowledge Baseを更新する


## 更新順序

Knowledge Baseは以下の順序で更新する。

1. shrine-profile-spec.md
2. shrine-data-guide.md
3. meaning-layer-spec.md
4. recommendation-copy-guide.md
5. action-guide.md
6. reflection-guide.md
7. glossary.md

上流の仕様変更は、下流ドキュメントへ反映する。
下流だけを更新し、上流仕様と矛盾する変更は禁止する。
