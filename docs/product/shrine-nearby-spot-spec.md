> **Status: 正本（承認済み仕様）。実装は未着手。**
> 母艦承認：2026-11-24（「KAMI MUSUBI｜ShrineNearbySpot 統合実装指示書 v1.0」、History関連付け条件 v1.0、DB登録候補判定ルール v1.3）。
> 登録候補判定の上位ルール：Google Drive「KAMI MUSUBI｜DB登録候補判定ルール v1.3（正式）」第9章（2026-11-24承認）。
> 承認範囲：設計方針・カテゴリー・座標・同一神社性・削除保護・Publication Gate・API / UI 契約。
> 2026-11-25：カテゴリーを 3 種類から 5 種類に変更（えつこさん決定。Drive「KAMI MUSUBI 文章と見どころの選定・表現ルール v1.0（案）」7章。値の名前と日本語表示は同日確定。§2.1.1）。
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
- 3 件の「OK／直す／保留／入れない」はそれぞれ独立して判定し、登録候補・本番投入・公開の各承認を混同しない。H-4 はスプレッドシートの候補ラベルであり、`ShrineHistory.id` として扱わない。
- 2026-11-25、No.15「乃木将軍と辻占売少年像」と No.17「水師営の会見のなつめの木」も、境内（神社が管理している敷地）の外にあるとして周辺スポットに区分した（えつこさん決定）。カテゴリーは §2.1.1 のとおり `monument` / `historic_tree`。この 2 件は上の初期対象 3 件の承認範囲には含めない。

## 2. データモデル

4 つのモデルを追加する。既存モデル・既存 Migration は変更しない。

### 2.1 ShrineNearbySpot

| 項目 | 内容 |
|---|---|
| `id` | |
| `shrine` | FK → `Shrine` |
| `stable_key` | 一意。空白だけの値は禁止 |
| `category` | `historical_building` / `historical_site` / `park` / `monument` / `historic_tree` の 5 種類だけ（§2.1.1） |
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
| `position_source_type` | `official_map` / `map_provider_poi` / `public_geospatial_data` の3値。Knowledgeの `source_type` と独立 |
| `position_source_url` | 座標の出典 URL |
| `position_verified_at` | 座標を確かめた日時 |

- 座標の数値範囲・ペア整合（片方だけは不可）・形式上の必須項目は、Django の検証と DB 制約の両方で守る。出典が指す対象施設・地点用途の一致や出典競合の解消は人間が確認し、DB 制約だけで保証済みとは扱わない。
- 初期実装では、Spot 用の GIS PointField を追加しない。
- 神社本体の座標で代わりに埋めることは禁止する。

### 2.1.1 カテゴリー（2026-11-25 変更）

カテゴリーの使い道は、神社詳細のカードに出す日本語表示だけ（§6）。推薦・並び順には使わない。

| 値 | 日本語表示 | 対象 | 例（乃木神社） |
|---|---|---|---|
| `historical_building` | 歴史的建造物 | 歴史的な建物 | No.14 旧乃木邸、No.16 厩 |
| `historical_site` | 歴史の舞台 | 歴史的な出来事が起きた場所 | （なし） |
| `park` | 公園 | 公園 | No.19 乃木公園 |
| `monument` | 像・記念碑 | 像・碑など、人物や出来事を記念して置かれたもの | No.15 乃木将軍と辻占売少年像 |
| `historic_tree` | 由緒のある木 | 歴史的な出来事・人物とつながる木 | No.17 水師営の会見のなつめの木 |

- `monument` と `historic_tree` は 2026-11-25 に追加した（えつこさん決定）。
- 値の名前と日本語表示は 2026-11-25 に確定した（えつこさん決定）。
- `historical_site` の日本語表示に「史跡」を使わない。国・自治体の指定史跡と誤解されるため。
- 「御神木」はカテゴリーにしない。神社が祀る木は境内のものであり、周辺スポットではないため。

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
- 既存 `backend/temples/services/highlight_publication.py` の値ベースの公開判定関数を再利用し、同じ5条件の関数を複製しない。公開済み History へのリンクは6番目の必須条件に追加しない。

### 4.2 Position Gate（Publication Gate とは別に判定する）

| Publication | Position | 表示 |
|---|---|---|
| PASS | PASS | カードと地図導線を出せる |
| PASS | HOLD | カードだけ出せる（座標は出さない） |
| FAIL | — | カードも地図導線も出さない |

**Position Gate v1.0（2026-11-24 母艦承認）**

`PASS` には以下をすべて必要とする。

1. `latitude` と `longitude` が両方存在し、WGS84の有効範囲内にある。
2. `position_source_type` が次の3値のいずれか：`official_map`（公式案内地図）、`map_provider_poi`（地図事業者の施設POI）、`public_geospatial_data`（公的地理空間資料）。
3. 追跡可能な有効な `position_source_url` が存在する。
4. `position_verified_at` に確認日時が記録されている。
5. 出典が示す実世界の対象施設が該当Spotと一致している。
6. 出典における位置の用途が建物・公園など当該Spotの案内目的と一致している。
7. 採用座標に関する未解決の出典間競合がない。

- 座標出典の種類だけでは自動的に `PASS` としない。検証不能または競合未解決の場合は `HOLD_POSITION_REVIEW`。
- `HOLD_POSITION_REVIEW` の採用座標 `latitude` / `longitude` は両方 `NULL`。公開APIでも両方 `null` を返し、地図・経路案内には使用しない。親 `Shrine` の座標で代替しない。
- `Publication Gate` と `Position Gate` は独立する。文章カードが公開可能で座標だけHOLDの場合、地図導線なしの文章カードを返す。
- 人による施設同定・出典整合の確認とDB上の形式制約は別責務。新しい `position_source_type` は既存 `ShrineKnowledgeSource.source_type` を変更しない。

### 4.3 historical_connection と History関連付け（2026-11-24 母艦承認）

- `historical_connection` は、神社とSpotの歴史的なつながりについて、**文章中の個々の主張を出典から追跡・確認できる範囲のみ**記述する。事実・伝承・編集上の解釈を混同せず、未確認の主張や未解決の相違を確定事実として公開しない。
- 下書きで未確認事項を管理することと、公開文章に含めることを分離する。
- **公開済み `ShrineHistory` への関連付けは、Spotの公開必須条件にしない。** 既存のPublication Gate 5条件を維持する。各Spot独自の出典で確認済みの情報は、History未公開でも独立して公開審査を受けられる。
- `linked_history_ids` は、同じ神社のHistoryで、かつ神社詳細APIの `histories` に実際に表示されるものに限る。該当がなければ `[]`。保留中のH-4を公開済みHistoryと推定してリンクを作らない。
- `historical_connection` に個別主張の根拠がない場合、当該主張を公開文章に含めない。空欄の場合も既存5条件の `name` / `description` を満たすか別途判定する。

### 4.4 DB登録候補と本番投入の境界（Drive正式ルール v1.3）

- 適用対象は `ShrineNearbySpot`・`ShrineNearbySpotTranslation`・`ShrineNearbySpotSource`・`ShrineNearbySpotHistory` と、関連する既存のSource / History。
- 人間の判断 `OK / 直す / 保留 / 入れない` と作業状態を分離する。**「直す」には既存ルール第3章の7条件、「OK」には第3A章の7条件**をそのまま適用し、保存後の再取得・維持項目・主張ごとの出典・事実と伝承の分離・関連整合・採用範囲を確認する。
- 「登録候補」はDB書込み・`published` / `approved`・本番公開の許可ではない。本番投入には独立した検証工程と明示承認が必要。既存の神社・History・Highlightの確認状態をNearbySpotへ自動継承しない。
- No.14 旧乃木邸、No.16 厩、No.19 乃木公園は個別審査が必要。第1〜8章に残る未整備の検証工程・内容審査が、この仕様同期によって実装済みになったとは扱わない。

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
- **モバイル（母艦承認済みの限定例外）：** `ShrineNearbySpot` のみ新規開発保留の例外としてPR-5の対象とする。現行の神社詳細画面の構造を確認し、同じ情報を表示する独立コンポーネントを実装する。Publication / Position Gate・出典・翻訳・History表示判定はBackendのみを正本とし、Web・Mobileで判定を複製しない。Mobile全体の新規開発・ストア公開・Phase 8順序は依然保留。PR開始・マージ・配布はそれぞれ母艦の個別判断が必要（README / Roadmapへの限定例外はPR #3521で反映済み）。

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
| PR-5 | Mobile UI（Web と同等の表示）。NearbySpot限定のMobile保留例外 | 母艦の個別承認 |

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
- 公開可能なSpotでHistoryリンクが無くても公開でき、`linked_history_ids=[]` になる。
- 未確認のH-4由来主張を `historical_connection` に公開しない。
- Position Gate PASSに出典種別3値・URL・確認日時・施設同定・用途一致・競合解消が必要で、HOLD時は座標が両方NULLになる。
- MobileはWebと同じBackendの公開判定を使用し、独自のGateを作らない。
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

## 11. 承認事項・残る実装判断（2026-11-24 同期）

次の6論点は母艦で判断・Drive文書に反映済みであり、旧「未決事項」ではない。

1. Position Gate PASS必須条件：座標ペア、出典種別、出典URL、確認日時、対象施設同定、地点用途、競合解消。
2. `position_source_type`：`official_map` / `map_provider_poi` / `public_geospatial_data` の3値。Knowledge Sourceの資料分類から独立。
3. `historical_connection`：歴史的主張ごとに根拠確認。未確認・相違未解決の主張は公開しない。
4. History関連付け：公開の必須条件ではない。画面に実際に表示される同じ神社のHistory IDのみ公開する。
5. DB登録候補判定：Driveの「KAMI MUSUBI｜DB登録候補判定ルール v1.3（正式）」第9章を適用。登録候補・本番投入・公開の承認は別。
6. Mobile：NearbySpotに限定した保留例外をPR #3521でREADME / Roadmapへ反映。Drive目次の該当ルールは「最新」。

**追加（2026-11-25）：** カテゴリーを 5 種類にした（§2.1.1）。Drive「KAMI MUSUBI 文章と見どころの選定・表現ルール v1.0（案）」7章を先に更新し、本書へ同期した。値の名前と日本語表示は同日確定。

**今後の実装判断：** PR-1〜PR-5は各PRの開始・マージを母艦が個別判断する。Migration番号は着手時の最新leafを再確認する。既存コード実装、乃木神社3件のDB投入・本番公開、Mobileの配布、未整備の内容審査は本同期PRの範囲外。

**正式ルールの参照：** [KAMI MUSUBI｜DB登録候補判定ルール v1.3（正式）](https://docs.google.com/document/d/1i0YD1fI-_btMQHusmvFzQDnFT4_3PfkwwJnif53QHU4/edit)（2026-11-24 母艦承認）。Driveの「KAMI MUSUBI ルールの目次（神社の選定・推薦・データ）」に登録済み。

## 12. 関連文書

- 見どころの公開判定：`docs/audit/highlights-publication-gate.md`
- 見どころの DB 整合性：`docs/audit/highlights-db-integrity.md`
- 見どころの神社詳細 API：`docs/audit/highlights-detail-api.md`
- 神社詳細のレイヤー：`docs/product/shrine-detail-layer.md`
- 神社知識と出典：`docs/knowledge/shrine-knowledge-contract.md`
