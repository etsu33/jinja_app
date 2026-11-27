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
  - Decision 4 sort_order：原宿口起点の暫定順（代々木・御苑・清正井・大鳥居・本殿・宝物殿）。現地確認後の修正を許容。ミュージアムは 18:32 に表示対象から外した
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

## 4. 手順2：見どころ6件を下書きで入れる（実施済み 2026-11-27）

### 実施の結果

2026-11-27 05:31 にえつこさんが手順2の実行を承認。10:15〜11:32 にえつこさんが本番の Django 管理画面（`https://jinja-backend.onrender.com/admin/`）で入力し、1画面ごとに Claude が本番を読み取りだけのSQLで確かめた。Claude は本番に書き込んでいない。

| id | stable_key | category | sort_order | 出典（ShrineKnowledgeSource id） | 由緒・歴史（ShrineHistory id） |
|---|---|---|---|---|---|
| 7 | meiji-yoyogi | nature | 1 | 157、155 | なし |
| 8 | meiji-gyoen | nature | 2 | 158、1 | 1 |
| 9 | meiji-kiyomasa-ido | historical_site | 3 | 157、155 | なし |
| 10 | meiji-otorii | architecture | 4 | 157、156、163 | なし |
| 11 | meiji-honden | architecture | 5 | 157、162、164 | 249 |
| 12 | meiji-houmotsuden | architecture | 6 | 159、157 | 1 |

- 件数：見どころ6件、日本語の翻訳6件（1件ずつ）、出典のつながり14件、由緒・歴史のつながり3件（shrine はすべて明治神宮 id=1）、アンサー0件
- 本文：6件とも name・description・historical_connection が `docs/audit/fixtures/meiji-jingu-highlights-2026-11-26.json`（PR #3542 の版）と1文字も違わない（MD5 で照合）。location_hint は空
- 状態：6件とも publication_status=draft、verification_status=source_confirmed、verified_at=2026-11-26 16:30 JST（07:30 UTC）、confidence=high。翻訳は review_status=draft、reviewed_at 空
- 公開側：本番の `GET /api/shrines/1/` で `highlights` は `[]`、`histories` は id=1 の旧本文1件だけ（H-2〜H-4 は draft のため出ない）。利用者に見える変化は無い
- 出典（ShrineKnowledgeSource）は166件のまま。途中で誤って開いた出典の追加画面からは何も作られていない
- 下書きの由緒・歴史（id=249）への見どころのつながりは、管理画面で保存できた

### 入力中に分かったこと（次の神社のため）

- 管理画面は1画面につき1行。見どころ本体 → 翻訳（Shrine highlight translations）→ 出典のつながり（Shrine highlight sources）→ 由緒・歴史のつながり（Shrine highlight historys）の4画面に分かれる。「Shrine knowledge sources」は出典そのものを作る画面で、手順2では使わない
- verified_at は管理画面で日本時間で入る（`TIME_ZONE = "Asia/Tokyo"`）。ファイルの 07:30 UTC は 16:30 と入れる
- 由緒・歴史のプルダウンは「神社の番号:題名」（`ShrineHistory.__str__`）。頭の数字は由緒・歴史の id ではない
- 出典のプルダウンは番号が出ず、新しい順（`ordering = ["-created_at"]`）。166件から題名で探すことになる
- 翻訳と由緒・歴史のつながりの画面では、前に選んだ見どころが残ることがある。1回、代々木のまま保存し、翻訳の一意制約（見どころ×言語）で止まった（本番は変わっていない）
- 由緒・歴史のつながりの画面の Shrine は最初は空。選ばずに保存すると入らない（宝物殿で1回起きて入れ直した）

### 入れた値（計画）

管理画面で入れる値は `docs/audit/fixtures/meiji-jingu-highlights-2026-11-26.json`。判定シートのタブ「本番投入データ（案）」と同じ。

- 6件とも publication_status=draft、verification_status=source_confirmed（verified_at=2026-11-26）、日本語の翻訳 review_status=draft、location_hint 空
- 出典は URL で既存の出典（id=1・155〜167）を選ぶ。由緒・歴史は 御苑・宝物殿→id=1、本殿→id=249
- 確信度（confidence）は見どころごとに判断する。今の値は high（6件）。出典の種類から自動で決めていない
- 宝物殿の historical_connection は Decision 1 の文。出典は宝物殿ページ（159）と境内地図（157）。展覧会告知（165）はこの文の根拠には使わない

### 宝物殿の文と出典の整合（確認済み）

宝物殿ページは「明治神宮が創建された翌年の大正10年（1921）10月末に竣功」「宝物殿で長らく御祭神の御物…が陳列されておりました」「現在、御祭神ゆかりの品々は…明治神宮ミュージアムに収蔵、展示されています」と書く。最初の案「長く…展示してきた」は今も展示しているとも読めたため、「展示していた」に直した（2026-11-26 17:48 えつこさん決定）。前半・後半とも宝物殿ページ（ページを開いて確認）で追えるので、確信度は high とする。

## 5. 手順3：公開（実施済み 2026-11-27）

### 計画

1. 管理画面で id=1 の本文を H-1 に更新し、出典 155（Q&A 明治神宮関係）を足し、verified_at を更新する（`docs/audit/fixtures/meiji-jingu-h1-update-2026-11-26.json`）
2. id=248〜250 を source_confirmed にし、verified_at・confidence を個別に設定する
3. 見どころ6件の日本語の翻訳を approved にし、見どころを published にする
4. 確認：詳細API の highlights が6件、由緒・歴史が4件、Web の表示

### 承認と信頼度の決定

- 2026-11-27 13:36 えつこさんが公開を承認。14:35 に H-2〜H-4 の confidence を決定（3件とも high）
- 根拠は出典の種類ではなく、本文の各事実と出典の整合（判定シート「本番投入データ（案）」タブ H26〜H29）
  - H-2：約70万㎡・献木約10万本・「永遠の杜」を公式「明治神宮とは」で確認
  - H-3：空襲・仮殿・奉賛会・木造での復興・昭和33年を歴史DB「本殿遷座祭」と「境内地図」で確認
  - H-4：指定日は国指定文化財等DB、36棟は文化審議会の議事要旨、告示は歴史DB年表、宝物殿の平成23年指定は宝物殿ページ。本文に含まれない未確認（36棟の内訳）は下げる理由にしない
- 文化庁の2資料（出典 166・167）は、2026-11-26 は検索の抜粋で確認。2026-11-27 にページを開いて確認した（166：名称「明治神宮」・重文指定年月日「2020.12.23(令和2.12.23)」・所在「東京都」、ページは本殿1棟の項目で36棟の記載はない／167：令和2年10月16日の議事要旨の別紙「（重要文化財の新規指定）」に「明治神宮 ３６棟」）。判定シートの記録をこれに合わせた

### 実施の結果

2026-11-27 14:44〜15:15 にえつこさんが本番の Django 管理画面で入力し、1画面ごとに Claude が本番を読み取りだけのSQLで確かめた。Claude は本番に書き込んでいない。

| 対象 | 変更 | 確認 |
|---|---|---|
| ShrineHistory id=248〜250 | draft → source_confirmed、confidence=high、verified_at=2026-11-26 16:30 JST | 本文・note・時期・並び順・出典は不変（MD5 で照合） |
| ShrineHistory id=1（H-1） | 本文を H-1 に、出典 1 に 155 を追加、verified_at=2026-11-26 16:30 JST | 本文は fixture と一致（MD5）。題名・種類・時期・並び順0・source_confirmed・high は不変 |
| 見どころの翻訳 id=7〜12（ja） | review_status=approved、reviewed_at=2026-11-27 15:05〜15:09 JST | name・description・historical_connection は fixture と一致、location_hint 空 |
| ShrineHighlight id=7〜12 | publication_status=published | 出典・由緒・歴史のつながりは手順2のまま、アンサー0件 |

- 公開側：本番 `GET /api/shrines/1/` で highlights 6件（sort_order 1〜6、linked_history_ids は 御苑・宝物殿→1、本殿→249）、histories 4件（id=1 は新しい本文・出典 2件）
- Web 本番（develop `fe5c77e`）の明治神宮の詳細ページで、「ここで見られるもの」6件・各「出典（N件）」、由緒・歴史4件・カードごとの「出典（N件）」（最初は閉じている）、由緒・歴史→見どころのリンク（御苑・宝物殿・本殿）を確認

### 入力中に起きたこと

- id=248 の note に、出典 166 用の文を誤って保存した（画面を取り違えた）。本文・状態は変わっておらず、利用者に見える影響は無い。投入時の note（投入用ファイルの文）に1文字も違わず戻した
- source_confirmed にするとき verified_at が空だと保存できない（`_validate_verified_at_consistency`）。1回エラーになり入れ直した
- id=1 は最初の保存で出典と verified_at だけ入り、本文が前のままだった（出典を選び直す途中でページを読み込み直したとみられる）。本文だけ入れ直した
- 由緒・歴史の出典欄は1つの一覧で複数選ぶ形で表示された。設定は `filter_horizontal`（左右2つの箱）だが、管理画面の部品の画像が壊れて表示されていたため、管理画面の静的ファイル（JS・画像）が本番で読み込めていない可能性がある（未調査）。Command キーを押したまま選ぶ
- reviewed_at は手で入れた時刻のため、6件のうち4件が保存時刻より1〜3分あとになっている（表示・公開判定には影響しない）

### 残り

- 出典 166・167 の note は、本番ではまだ「ウェブ検索の抜粋で確認（2026-11-26）」のまま。ページを開いて確認した事実と日付を、既存の記録を残したまま足す（confidence・verification_status は変えない）
- 御苑の「由緒・歴史を読む：明治神宮の創建」のリンク文字が、画面の幅によって途中で切れて見える。スマホの幅で要確認

## 6. ローカルQA（Mac）

本番の公開条件は変えずに、手元のDBでだけ公開条件を満たすデータを作って画面を見る。

1. 本番の接続情報を読み込んでいない新しいターミナルを開く（`echo $DATABASE_URL` が手元のDBか空であること）
2. 手元のDBに投入用ファイルを入れる：`python manage.py import_shrine_knowledge temples/data/knowledge_seeds/meiji_jingu_2026_11_26_seed.json --dry-run` → 問題なければフラグなしで実行
3. 見どころを入れる（まず `--dry-run`）：
   `python ../scripts/local_qa/load_highlight_fixture_local.py ../docs/audit/fixtures/meiji-jingu-highlights-2026-11-26.json --publish-for-local-qa --history-content-json ../docs/audit/fixtures/meiji-jingu-h1-update-2026-11-26.json`
   - スクリプトは接続先が手元のDBでなければ止まる。stable_key がすでにあれば止まる（上書きしない）
   - `--publish-for-local-qa` は手元のDBでだけ、見どころを公開・翻訳を承認・この神社の下書きの由緒・歴史を確認済みにする
4. バックエンドとWebを手元で起動し、明治神宮の詳細ページで「ここで見られるもの」7件・順番・由緒・歴史との相互リンク・出典・由緒・歴史4件を確認する

ローカルQAの結果（1回目・7件の版）：2026-11-26 18:19、えつこさんのMacで実施。手元の `jinja_db` はマイグレーションが 0104 で止まりデータも本番と違ったため（0105 が前提違いで fail-closed）、`scripts/migration_safety/` の `dump_readonly.sh`／`restore_isolated.sh` で本番の写しを捨ててよい手元のDB（`kami_musubi_restore_test_*`）に戻して使った。並び順・相互リンク・H-1 の新しい本文・由緒・歴史4件・宝物殿の文を画面で確認。画面で「情報が多く、何を伝えたいかが迷子になる」と分かり、文を見直した（7章）。2回目（6件の版）は写しを作り直して確認する。

## 7. 見どころの文の見直し（2026-11-26 18:23〜18:48）

ローカルQAの画面を見て、えつこさんが文の見直しを決めた。

- 芯：KAMI MUSUBI を使って「ここに訪れたい」という経験につなげる。事実（見どころの本文）→ 歴史的背景（この見どころが伝える歴史・由緒）→ ご縁（相談の答え＝アンサー）の順に伝える。ご縁は今のルールどおりアンサーに書く
- 見どころの文章の原則（ドライブ「文章と見どころの選定・表現ルール v1.0（案）」6章⑤に記録し、目次に1行追加）：情報量を減らすこと自体を目的にしない。現地で見られるもの・日本文化・歴史的背景・その場所だけの特徴を優先。本文と歴史の文の役割を分け、同じ内容を繰り返さない。長さは文字数ではなく、情報の必要性・独自性・可読性で判断する（19:53 決定。最初に置いた目安 本文 60〜120字・歴史の文 30〜60字は基準にしない）。出典・確認状態・元の詳しい情報は残し、事実と伝承を混ぜない。長い文は折りたたみ・「もっと見る」を推奨（画面の変更は別に決める）
- ミュージアム：由緒・歴史とのつながりが無く「その場所がある」だけになるため外した（出典 id 160・161 は本番に残ったまま使わない）
- 6件の本文・歴史の文は `docs/audit/fixtures/meiji-jingu-highlights-2026-11-26.json` と判定シート（見どころタブ S〜W列）。削った情報は判定シートの元の文（E列）に残している
- H-4 との重なり（19:44 えつこさん決定）：事実の部分的な重複は許容し、説明の重複は避ける。重要文化財の指定年月日と36棟は H-4 に集約し、本殿・宝物殿の本文には建築的特徴と「国の重要文化財に指定されている」だけを残した。historical_connection・由緒・歴史とのつながり・出典は変えていない
- ルール v1.3 の状態：6件とも登録候補（本文の事実は 2026-11-26 にページを開いて確認した公式ページで追える）

## 8. 清正井の名称（2026-11-27 えつこさん決定）

- 名前を「清正井」から「清正井（きよまさのいど）」に変える。明治神宮公式サイトの御苑ページ・境内地図ページの表記に合わせる（2026-11-27 にページを開いて確認）。代々木（よよぎ）と同じく読みを添える
- stable_key（`meiji-kiyomasa-ido`）・id・出典・由緒・歴史とのつながり・本文・状態は変えない
- 投入用ファイルの name と判定シート（見どころタブ D6、本番投入データ（案）タブ A34・E34）を直した
- 本番の下書き：2026-11-27 12:07 にえつこさんが承認し、12:10 に管理画面で翻訳 id=9 の name を「清正井（きよまさのいど）」に直した。読み取りで確認：name は投入用ファイルと1文字も違わない（MD5 一致）、本文・歴史の文・location_hint・review_status=draft・reviewed_at 空・出典（157、155）・publication_status=draft・sort_order=3 は変わっていない

## 9. 変えていないもの

Publication Gate、推薦エンジン、モデル・マイグレーション、投入コマンド、既存データ（id=1 を含む）。
