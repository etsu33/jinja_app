> **Status: 正本（承認済み仕様）。実装は未着手。**
> 母艦承認：2026-11-24（「KAMI MUSUBI｜ShrineNearbySpot 統合実装指示書 v1.0」）。
> 承認範囲：設計方針・カテゴリー・座標・同一神社性・削除保護・Publication Gate・API / UI 契約。
> 本書は PR-0（仕様・ドキュメント）で追加した。モデル・Migration・API・UI はまだ無い。
> PR-1 以降は、それぞれ母艦の承認を得てから始める。

# 神社周辺の歴史スポット（ShrineNearbySpot）仕様

## 1. 目的

神社に関係する周辺の歴史スポットを、境内の見どころ（ShrineHighlight）とは独立して管理し、神社詳細に表示する。

- 周辺スポットは**境内施設ではない**。参道順・境内施設・神社の開門時間といった、見どころ側の表現を流用しない。
- 既存の神社詳細（由緒・歴史、見どころ、解釈・推薦レイヤー）の挙動を変えない。
- 推薦・Compass・Ranking・課金ロジックには使わない。

### 初期対象（乃木神社の 3 件）

| No. | 名称 | カテゴリー |
|---|---|---|
| 14 | 旧乃木邸 | `historical_building` |
| 16 | 厩 | `historical_building` |
| 19 | 乃木公園 | `park` |

- 3 件とも、歴史候補 H-4「赤坂の乃木邸と厩」と関係する。
- H-4 が本番の `ShrineHistory` として登録・承認済みであるとは**仮定しない**。H-4 はシート上で保留中である。
- 3 件の本番公開は、この仕様の範囲に含まない。

## 2. データモデル

4 つのモデルを追加する。既存モデル・既存 Migration は変更しない。

### 2.1 ShrineNearbySpot

| 項目 | 内容 |
|---|---|
| `id` | |
| `shrine` | FK → `Shrine` |
| `stable_key` | 一意。空白だけの値は禁止 |
| `category` | `historical_building` / `historical_site` / `park` の 3 種類だけ |
| `sort_order` | 表示順。**参道順ではない** |
| `verification_status` | 既存の `KNOWLEDGE_VERIFICATION_STATUS_CHOICES` |
| `confidence` | 既存の `KNOWLEDGE_CONFIDENCE_CHOICES` |
| `verified_at` | |
| `publication_status` | `draft` / `published` / `archived`（見どころと同じ） |
| `created_at` / `updated_at` | |

**座標**

| 項目 | 内容 |
|---|---|
| `latitude` | `DecimalField(11, 8)`、NULL 可。WGS84 |
| `longitude` | `DecimalField(12, 8)`、NULL 可。WGS84 |
| `position_status` | `PASS` / `HOLD_POSITION_REVIEW` |
| `position_source_type` | 座標の出典の種類 |
| `position_source_url` | 座標の出典 URL |
| `position_verified_at` | 座標を確かめた日時 |

- 範囲、緯度・経度のペアの整合（片方だけは不可）、Position Gate は、Django の検証と DB の制約の両方で守る。
- 初期実装では、Spot 用の GIS PointField を追加しない。
- 神社本体の座標で代わりに埋めることは禁止する。

### 2.2 ShrineNearbySpotTranslation

| 項目 | 内容 |
|---|---|
| `spot` | FK → `ShrineNearbySpot` |
| `language_code` | `ja` / `en` |
| `name` / `description` / `historical_connection` / `location_hint` | 利用者に見える文章 |
| `review_status` / `reviewed_at` | |
| `created_at` / `updated_at` | |

- `UNIQUE(spot, language_code)`。
- 承認済みの文章が通常の save で変わったら、`review_status = draft`、`reviewed_at = NULL` に戻す。

### 2.3 ShrineNearbySpotSource

- `spot`、`source`（既存の `ShrineKnowledgeSource` への FK）。`UNIQUE(spot, source)`。
- 出典テーブルを新しく作らない。

### 2.4 ShrineNearbySpotHistory

- `spot`、`history`、`shrine`。`UNIQUE(spot, history)`。
- Spot と History が同じ神社に属することを、PostgreSQL の複合外部キーで保証する。

## 3. 削除保護

見どころと同じ方針にする。

| 対象 | 方針 |
|---|---|
| `draft` の Spot | ORM で削除できる |
| `published` / `archived` の Spot | ORM での削除を禁止する |
| `published` → `archived` | 状態の変更はできる |
| History・Source への参照 | `PROTECT` |
| 直接 SQL による削除 | 状態に応じた削除保護の**対象外** |

ORM の削除保護（状態に応じた保護）と、DB の参照整合性（PROTECT・複合外部キー）は別のものとして扱う。

## 4. 公開判定

### 4.1 Publication Gate

次の 5 条件をすべて満たした Spot だけを、利用者向け API に返す。判定は読み出すときに行う。

1. `publication_status == "published"`
2. `verification_status` が `source_confirmed` または `reviewed`
3. 公開の根拠になる fact-ready な出典が 1 件以上
4. 対象言語の Translation が `approved`
5. `name` と `description` が空でない

- 出典の扱いは見どころと同じにする。`user_observation` と `internal_research` だけでは公開できない。
- 言語ごとに独立して判定する。英語の翻訳が未承認でも、日本語の判定には影響しない。

### 4.2 Position Gate（Publication Gate とは別に判定する）

| Publication | Position | 表示 |
|---|---|---|
| PASS | PASS | カードと地図導線を出せる |
| PASS | HOLD | カードだけ出せる（座標は出さない） |
| FAIL | — | カードも地図導線も出さない |

## 5. API 契約

既存の神社詳細 API（`ShrineDetailSerializer`）に `nearby_spots` を追加する。新しい公開エンドポイントは作らず、一覧 API にも足さない。

| フィールド | 内容 |
|---|---|
| `id` / `category` / `sort_order` | |
| `name` / `description` / `historical_connection` / `location_hint` | 承認済みの翻訳から出す |
| `linked_history_ids` | 同じ神社に属し、神社詳細の `histories` に実際に出ている History の id だけ |
| `sources` | 公開の根拠になる出典 |
| `observed_on` | 現地確認日（ある場合） |
| `latitude` / `longitude` | Position PASS のときだけ値を出す。HOLD なら `null` |
| `map_available` | Publication PASS かつ Position PASS のとき `true` |

- `nearby_spots` は常に配列で返す。該当が無ければ `[]`。
- 公開判定を通らない Spot は、座標が確認済みでも配列に入れない。
- 追加によって N+1 クエリを起こさない。

## 6. UI 契約

新しいセクションの表示名は **「神社周辺の歴史スポット」**。

**Web の神社詳細での順番**

1. 神社について
2. ここで見られるもの
3. 神社周辺の歴史スポット
4. 既存の解釈・推薦レイヤー

- Spot が 0 件なら、セクション全体を表示しない。
- カードに出すもの：
  - カテゴリーの日本語表示
  - 名前、説明
  - 場所の目安（ある場合）
  - 歴史的なつながり（ある場合）
  - 公開済み History へのリンク（ある場合）
  - 出典
  - 現地確認日（ある場合）
  - 地図導線（`map_available` が `true` の場合）
- 既存の Design Token を使う。
- **モバイル：** 現行の神社詳細画面の構造を確かめたうえで、同じ内容を出せる独立コンポーネントを足す。公開してよいかの判定は Web とモバイルで二重に実装せず、Backend の判定結果を正本にする。Web とモバイルは同じ PR でなくてよい。

## 7. MVP から外すもの

- 周辺スポット専用の公開 API
- 周辺スポット同士の親子関係
- 人気順・おすすめ順
- 推薦スコアへの加点
- Concierge・Compass のロジック変更
- 新しいランキング
- 施設の開放時間・入場料金の管理
- アプリ内の新しい地図エンジン
- 新しい課金制御
- 新しい Analytics イベント
- 自動ジオコーディング
- AI による歴史文章の自動公開
- 乃木神社以外のデータの一括登録

## 8. PR の分け方

| PR | 内容 | 開始条件 |
|---|---|---|
| PR-0 | 仕様・ドキュメント（本書、README.md、architecture.md、roadmap.md） | — |
| PR-1 | 4 モデル、Migration、Admin、基礎テスト。PostGIS と NoGIS の Migration 系列の整合を確かめる | 母艦承認 |
| PR-2 | 同一神社性、削除保護、Publication Gate、Position Gate とテスト | 母艦承認 |
| PR-3 | 神社詳細 API（`nearby_spots`・出典・History リンク・座標の公開条件） | 母艦承認 |
| PR-4 | Web UI（独立セクション・表示・リンク・地図導線） | 母艦承認 |
| PR-5 | Mobile UI（Web と同等の表示） | 母艦承認 |

各 PR は、独立してレビュー・マージできる範囲に限り、テストとドキュメントの更新まで含める。

## 9. テスト（最低限）

- 同じ神社の関連付けが成功する。
- 別の神社の History との関連付けは DB で拒否される。
- `draft` 以外の ORM 削除が拒否される。
- 直接 SQL での削除保護の限界が明記されている。
- 不正なカテゴリー・不正な座標・片方だけの座標が拒否される。
- 未承認の Spot が API に出ない。
- 英語の翻訳が未承認でも、日本語の公開条件は独立して判定される。
- 承認後に文章を変えると、承認が失効する。
- 座標が未確認でも、公開条件を満たす説明カードは表示される。
- 未公開の History へのリンクが出ない。
- 既存の見どころが従来どおり表示される。
- 推薦・Compass・Ranking の挙動が変わらない。
- API のクエリ数が件数に比例して増えない。
- Web・Mobile の小さな画面で表示が崩れない。

DB テストは隔離された PostgreSQL で行う。本番には接続しない。

## 10. 現行実装との照合（PR-0 時点、develop `9d05105`）

**[事実]** develop の実コードと照らし合わせた結果。

| 仕様の項目 | 現行実装 | 照合 |
|---|---|---|
| 公開状態 `draft / published / archived` | `ShrineHighlight.PublicationStatus` が同じ 3 値（`backend/temples/models_highlights.py`） | 一致 |
| 削除保護 | 見どころは `pre_delete` 受信関数 `protect_non_draft_highlight` で、保存済みの状態を `select_for_update` で読んで `ProtectedError` を出す。直接 SQL は対象外とモジュールに明記 | 同じ方式を使える |
| 複合外部キー | `backend/temples/constraints_highlights.py` の `CompositeForeignKey`（PostgreSQL 専用。Migration の import パスを固定するとモジュールに明記） | 再利用できる。History 側の `UNIQUE(id, shrine)`（`history_id_shrine_unique`）は既にある（Migration `0125` / NoGIS `0024`） |
| 公開判定 | `temples/services/highlight_publication.py` の `decide_highlight_publication(...)` は値だけで判定する関数。`public_evidence_sources`・`find_translation`・`latest_observed_on` もある | 5 条件が見どころと同じなので、複製せずに再利用できる |
| 承認の失効 | `models_highlights._invalidate_approval_if_content_changed` を翻訳とアンサーで共有している | 再利用できる |
| 神社詳細 API | `ShrineDetailSerializer`（`temples/api/serializers/shrine.py`）に `highlights` があり、言語は `HIGHLIGHT_DETAIL_LANGUAGE = "ja"`。表示する History は `_detail_displayed_histories` で決まり、見どころと由緒・歴史で同じ判定を使っている。先読みは `temples/api/views/shrine.py` の retrieve で行う | 同じ形で `nearby_spots` を足せる |
| Migration 系列 | 通常系 `temples/migrations/`（最新 `0126`）と NoGIS 系 `temples/migrations_nogis/`（最新 `0025`）の 2 系列がある | PR-1 で両方に同じ内容を足す必要がある |
| Web の順番 | `ShrineDetailArticle.tsx` で「神社について」（`ShrineFactSection`）→「ここで見られるもの」（`ShrineHighlightSection`）→ 解釈・推薦レイヤー（`contextReasonSections`）の順 | 3 番目に差し込める |
| 座標の型 | 神社本体は `Shrine.latitude` / `longitude` が `FloatField`、`location` が `PointField` | Spot は仕様どおり `DecimalField` で、神社本体とは型が違う（仕様の判断どおり） |
| モバイル | `apps/mobile/app/shrines/[id].tsx` に神社詳細画面がある。見どころは未実装 | README の「現行開発スコープ」は Mobile の新規開発を保留している（§11） |

## 11. 未決事項（母艦の判断が要るもの。本書では決めていない）

1. **Position Gate の PASS の条件。** PASS のとき必須にする項目（両方の座標・`position_source_type`・`position_source_url`・`position_verified_at` のどれまでか）が決まっていない。
2. **`position_source_type` の値。** 既存の出典の種類（`ShrineKnowledgeSource.source_type`）を使うか、別の語彙を作るか。
3. **historical_connection の書き方。** 見どころには「つながった由緒・歴史の言い換えだけを書く」という決まりがある（ドライブの目次「神社の見どころ」）。Spot にも当てはめるか。乃木神社の 3 件は H-4（保留中）の言い換えを含んでいる。そのため、当てはめる場合は H-4 が出るまで文章を出せない。
4. **登録候補の判定ルールの対象。** 「DB登録候補判定ルール v1.2（正式）」の対象は ShrineHighlight・ShrineHistory・関連する ShrineKnowledgeSource で、ShrineNearbySpot は入っていない。
5. **PR-5（モバイル）と開発スコープの関係。** README の「現行開発スコープ（2026-10-25）」は Mobile の新規開発を保留している。PR-5 はこの保留の例外として扱うか、保留が解けるまで待つか。
6. **ドライブの目次への登録。** CLAUDE.md の決まりでは、新しいルールはドライブの目次に 1 行足す。本書を正本として目次に載せる時期（PR-0 のマージ後など）。

## 12. 関連文書

- 見どころの公開判定：`docs/audit/highlights-publication-gate.md`
- 見どころの DB 整合性：`docs/audit/highlights-db-integrity.md`
- 見どころの神社詳細 API：`docs/audit/highlights-detail-api.md`
- 神社詳細のレイヤー：`docs/product/shrine-detail-layer.md`
- 神社知識と出典：`docs/knowledge/shrine-knowledge-contract.md`
