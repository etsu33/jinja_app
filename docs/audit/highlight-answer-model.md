# Highlight Answer Model（見どころ単位の推薦 PR-1）

> Status: Audit — 実装記録。推薦・画面への接続は後続PR。
> 日付: 2026-11-22 JST
> Base: develop `4a9b821`
> Branch: `feature/highlight-answer-model`
> 設計: プロジェクト文書 `claude/highlight-level-recommendation-plan.md`

## 目的

推薦した神社ごとに「相談に合う見どころ1つ」と「その見どころがなぜ相談と重なるか」を出すための、確認済みの文を保存する場所を作る。

## 決めたこと（2026-11-22 えつこさん）

- アンサーの単位は need_tag（15分類）。consultation_axis（9軸）にすると protection・family・travel_safe・health・communication の相談に出せないため
- 「芸能・表現」の分類は足さない。芸能浅間神社は今の分類（mental・courage・career）に答える
- 段階Aの表示は無料の人にも出す

## 変更

### モデル `ShrineHighlightAnswer`（`temples/models_highlights.py`）

| 項目 | 内容 |
|---|---|
| highlight | FK → ShrineHighlight（CASCADE。見どころは公開後は削除できないので、実際に消えるのは下書きの見どころと一緒のときだけ） |
| need_tag | `temples.domain.need_tags.NEED_TAGS` の15分類（CheckConstraint） |
| language_code | ja / en |
| answer_text | 空・空白だけは不可（Pythonの検証とDBの制約の両方） |
| review_status / reviewed_at | 承認済みには reviewed_at が必須 |

- 一意：(highlight, need_tag, language_code)
- 承認済みのアンサーで answer_text が変わったら、`save()` で draft に戻す。need_tag の付け替えは文の変更ではないので承認は残る
- 承認の取り消しの処理は、翻訳（ShrineHighlightTranslation）と共有の関数 `_invalidate_approval_if_content_changed` にまとめた（翻訳の挙動は変えていない。テストで確認）

### 公開判定 `decide_answer_publication(answer, language_code)`（`temples/services/highlight_publication.py`）

すべて満たすときだけ出せる。
- アンサーの言語が表示する言語と同じ（`answer_language_mismatch`）
- アンサーが承認済み（`answer_not_approved`）
- 文が空でない（`answer_empty`）
- 見どころ自体が同じ言語で公開判定を通っている（`highlight_not_displayable`）。見どころが出せないのにアンサーだけ出すことはしない

### 管理画面

- `ShrineHighlightAnswerAdmin`：一覧に「表示条件」列（`OK` か落ちた理由）
- 見どころの編集画面の中で、アンサーを入れられるようにした（`ShrineHighlightAnswerInline`）

### Migration

- `migrations/0125_highlight_answer.py` / `migrations_nogis/0024_highlight_answer.py`（CreateModel 1件のみ。両系列の operation 一致をテストで確認）
- 本番では、マージ後に `python manage.py migrate` が必要（`RUN_MIGRATIONS_ON_START` は 0 のため、起動では適用されない）

### 既存テストの修正

`test_highlights_migrations.py` の往復テストは、後片付けで基盤の4モデルだけを外していた。基盤より後に足したモデル（アンサー）も外すよう、鎖が作ったモデルを状態の差分から求める形にした。比べる相手も「最新の状態」から「基盤を当てた直後の状態」に直した。確認している内容は同じ。

## 含まないもの

- 推薦結果への highlight_pick の追加（PR-2）
- コンシェルジュのカード表示・計測（PR-3）
- 花園神社のアンサーの入力（データ）

## 確認

- 新規 `temples/tests/test_highlight_answers.py`（15分類すべての保存、一意、空の文、承認の取り消し、公開判定、管理画面）
- バックエンド全体（ローカル PostgreSQL 16・NoGIS・8並列）：8895 passed / 10 failed。9件は develop でも同じく失敗する環境依存のもの。残り1件（`test_migration_0105_...::test_reverse_fails_closed_when_operator_user_is_absent_but_db_is_not_fresh`）は単体で実行すると通る（並列実行のときだけ落ちる）
