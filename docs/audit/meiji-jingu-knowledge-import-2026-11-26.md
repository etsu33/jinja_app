# 明治神宮 Knowledge 投入の記録と、見どころの公開前の計画（2026-11-26）

> 状態：手順1（出典・由緒・歴史の投入）は本番に実施済み。手順2（見どころ）・手順3（公開）は未実施で、母艦（えつこさん）の個別承認を待つ。
> 本ドキュメントの作成にあたって本番DBへの書き込みはしていない（本番は読み取りのみ）。

## 1. 判断の根拠

- DB登録候補判定ルール v1.3（ドライブ）
- 判定シート「KAMI MUSUBI 明治神宮 見どころ下書きと判定（2026-11-26）」（ドライブ）。えつこさんの判定（O列・J列）と、タブ「本番投入データ（案）」
- 投入方針（2026-11-26 えつこさん決定）
  - Decision 1 カテゴリー：既存の6種類のみ（本殿・大鳥居・宝物殿＝architecture、御苑・代々木＝nature、清正井＝historical_site、ミュージアム＝cultural_heritage）
  - Decision 2 H-1：既存の ShrineHistory id=1 を管理画面で更新する（投入コマンドの上書き防止は変えない）
  - Decision 3 history_type：H-1 official_origin（既存）、H-2〜H-4 historical_event
  - Decision 4 sort_order：原宿口起点の暫定順（代々木・ミュージアム・御苑・清正井・大鳥居・本殿・宝物殿）。現地確認後の修正を許容
  - Decision 5 Publication：下書きで登録する。確認状態・確信度・翻訳の承認・公開状態は独立して管理し、確信度を出典の種類から自動で決めない
  - 宝物殿の歴史文：「創建の翌年に竣功し、長く御祭神の御物を展示していた」（最初の案「展示してきた」は、今も展示していると読めて出典とずれるため、17:48 に修正）
  - 公開前QA：Macのローカル環境で実際の画面を確認する（管理画面の表示条件だけで判断しない）
- 出典の種類は `docs/knowledge/shrine-knowledge-contract.md` の source_type 定義。出典URLごとに1つの ShrineKnowledgeSource にする

## 2. 手順1：本番への投入（実施済み）

| 項目 | 内容 |
| --- | --- |
| 投入用ファイル | `backend/temples/data/knowledge_seeds/meiji_jingu_2026_11_26_seed.json`（SHA-256 `5da5da1b62cd0666334774466ee9e6b969752154a8f11353f9799b115a631b29`） |
| 実行経路 | えつこさんのMacから `import_shrine_knowledge`（既存の候補F。接続情報はリポジトリ外のファイル） |
| 実行日時 | 2026-11-26 17:07 JST |

| 確認 | 結果 |
| --- | --- |
| V2 `--validate-only` | エラー0 |
| V3 `--dry-run` | source REUSE_EXISTING 1（meiji-about → 既存 id=1）／source CREATE 13／history CREATE 3。エラー0 |
| V4 投入 | sources created=13、histories created=3（deities・collectives・memberships・source_facts は0） |
| V5 再 `--dry-run` | source REUSE_EXISTING 14、history SKIP_EXISTS 3、CREATE 0 |
| V6 本番の読み取り | 明治神宮の由緒・歴史 1→4件、祭神2件のまま、見どころ0件のまま。出典は全体166件。直近30分で作られたのは出典13件・由緒・歴史3件のみ |
| V7 詳細ページ | 由緒・歴史は id=1「明治神宮の創建」の1件だけ表示（えつこさんのスクリーンショット 17:10）。draft の3件は出ていない |

本番で作られた行：

- 出典 id=155〜167（すべて source_confirmed。confidence は社報 161・展覧会告知 165 が medium、ほかは high。166・167 は cultural_property）
- 由緒・歴史 id=248「人工の杜の造営」（出典1）、id=249「戦災と復興」（出典157・162）、id=250「御本殿以下36棟の重要文化財指定」（出典159・164・166・167）。3件とも draft、confidence 空
- 既存の id=1「明治神宮の創建」と出典 id=1 は変更なし

### 投入中に起きたこと（本番の接続設定）

- Macの接続情報ファイルのパスワードが古く、`password authentication failed` で止まった（書き込みなし）
- その際、Render の `DATABASE_URL` が Supabase の直接接続（IPv6 のみ）の値に差し替えられ、16:49 の再デプロイ（trigger: service_updated）で本番のバックエンドがDBに `Network is unreachable` になった
- 17:01 に Session pooler の接続文字列へ差し替えて再デプロイ（service_updated）。17:10 に詳細ページ・検索の表示を確認
- 教訓：Render には直接接続ではなく Session pooler の接続文字列を使う。接続情報はチャットに貼らない

## 3. 追加監査：見どころが出ない原因の横断比較（2026-11-26）

本番DB（読み取り）、本番API（`/api/shrines/{id}/`、Chrome から取得）、本番Web（jinja-app-web.vercel.app）、リポジトリ（develop `ddaf60d`）で確認した。

| 観点 | 花園神社（id=61） | 乃木神社（id=59） | 明治神宮（id=1） |
| --- | --- | --- | --- |
| 見どころの登録 | 6件（すべて published） | 0件 | 0件 |
| 見どころの確認状態 | 6件 source_confirmed | — | — |
| 日本語の翻訳 | 6件 approved（英語 0件） | — | — |
| 公開の根拠になる出典 | 6件すべてあり | — | — |
| 見どころと由緒・歴史のつながり | 3本 | — | — |
| アンサー | 2件 | — | — |
| 由緒・歴史（確認済み／全体） | 3／3 | 3／3 | 1／4（3件は draft） |
| 本番API `highlights` | 6件 | 0件（項目はある） | 0件（項目はある） |
| 本番Web「ここで見られるもの」 | 表示（`shrine-highlight-1`〜`6`） | 節なし | 節なし |
| モバイル | 見どころの表示は未実装 | 同左 | 同左 |

判定：

- 乃木神社・明治神宮で見どころが出ないのは、本番に見どころが登録されていないため。公開判定・API・Web は花園神社で正しく動いており、**実装上の不具合は見つからなかった**（未登録による正常な非表示）
- モバイル（`apps/mobile`）には見どころを表示するコードが無い。見どころの設計（Web の詳細ページ）でモバイルは対象外のため、不具合ではなく**未実装**。モバイルで見せるかは別に決める
- 詳細APIの見どころは日本語固定（`HIGHLIGHT_DETAIL_LANGUAGE = "ja"`、`backend/temples/api/serializers/shrine.py`）。`?lang=en` を付けても日本語の判定で返る。英語の翻訳は本番に0件。設計どおり
- 本番とローカルの差：本番の Render は develop `ddaf60d` で動いており、えつこさんのMacも同じ develop に更新済み。コードの差は無い。データは本番とローカルで別（ローカルには見どころが無い前提）

## 4. 手順2：見どころ7件を下書きで入れる（未実施・承認待ち）

管理画面で入れる値は `docs/audit/fixtures/meiji-jingu-highlights-2026-11-26.json`。判定シートのタブ「本番投入データ（案）」と同じ。

- 7件とも publication_status=draft、verification_status=source_confirmed（verified_at=2026-11-26）、日本語の翻訳 review_status=draft、location_hint 空
- 出典は URL で既存の出典（id=1・155〜167）を選ぶ。由緒・歴史は 御苑・宝物殿→id=1、本殿→id=249
- 確信度（confidence）は見どころごとに判断する。今の値は high（7件）。出典の種類から自動で決めていない
- 宝物殿の historical_connection は Decision 1 の文。出典は宝物殿ページ（159）と境内地図（157）。展覧会告知（165）はこの文の根拠には使わない

### 宝物殿の文と出典の整合（確認済み）

宝物殿ページは「明治神宮が創建された翌年の大正10年（1921）10月末に竣功」「宝物殿で長らく御祭神の御物…が陳列されておりました」「現在、御祭神ゆかりの品々は…明治神宮ミュージアムに収蔵、展示されています」と書く。最初の案「長く…展示してきた」は今も展示しているとも読めたため、「展示していた」に直した（2026-11-26 17:48 えつこさん決定）。前半・後半とも宝物殿ページ（ページを開いて確認）で追えるので、確信度は high とする。

## 5. 手順3：公開（未実施・承認待ち）

1. 管理画面で id=1 の本文を H-1 に更新し、出典 155（Q&A 明治神宮関係）を足し、verified_at を更新する（`docs/audit/fixtures/meiji-jingu-h1-update-2026-11-26.json`）
2. id=248〜250 を source_confirmed にし、verified_at・confidence を個別に設定する
3. 見どころ7件の日本語の翻訳を approved にし、見どころを published にする
4. 確認：管理画面の表示条件が7件とも `ja: OK`、詳細API の highlights が7件、由緒・歴史が4件、Web の表示

## 6. ローカルQA（Mac）

本番の公開条件は変えずに、手元のDBでだけ公開条件を満たすデータを作って画面を見る。

1. 本番の接続情報を読み込んでいない新しいターミナルを開く（`echo $DATABASE_URL` が手元のDBか空であること）
2. 手元のDBに投入用ファイルを入れる：`python manage.py import_shrine_knowledge temples/data/knowledge_seeds/meiji_jingu_2026_11_26_seed.json --dry-run` → 問題なければフラグなしで実行
3. 見どころを入れる（まず `--dry-run`）：
   `python ../scripts/local_qa/load_highlight_fixture_local.py ../docs/audit/fixtures/meiji-jingu-highlights-2026-11-26.json --publish-for-local-qa --history-content-json ../docs/audit/fixtures/meiji-jingu-h1-update-2026-11-26.json`
   - スクリプトは接続先が手元のDBでなければ止まる。stable_key がすでにあれば止まる（上書きしない）
   - `--publish-for-local-qa` は手元のDBでだけ、見どころを公開・翻訳を承認・この神社の下書きの由緒・歴史を確認済みにする
4. バックエンドとWebを手元で起動し、明治神宮の詳細ページで「ここで見られるもの」7件・順番・由緒・歴史との相互リンク・出典・由緒・歴史4件を確認する

ローカルQAの結果：未実施（えつこさんのMacで実施する）。クラウドの作業環境では GDAL が無く、手元のDBを作れなかった。

## 7. 変えていないもの

Publication Gate、推薦エンジン、モデル・マイグレーション、投入コマンド、既存データ（id=1 を含む）。
