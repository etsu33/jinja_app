# Collective Deity Backfill Candidate Freeze（A-5b）

## 1. Status

- Status: **`A5B_CANDIDATE_UNIVERSE_RECORDED / SOURCE_VERIFICATION_BLOCKED / FREEZE = 0`**
- Recorded at: `2026-09-30`
- Base: `develop@a5768c97f1e40184b1e3b5c9fc503cb5ff4015c7`（A-5a PR #3014 merged）
- Branch: `audit/collective-deity-backfill-candidate-freeze`
- Change type: docs-only audit record
- Production write: **NONE**（INSERT = 0 / UPDATE = 0 / DELETE = 0 / DDL = 0）
- Production reconciliation: **`NOT_RUN`**
- Knowledge Seed write: **NONE**（backfill seed 未作成 / 既存 1.0 seed 未変更）
- Backfill execution: **NONE**

結論を先に記す。

```text
candidate universe           = 57
FREEZE_COLLECTIVE_ONLY       = 0
FREEZE_WITH_MEMBERSHIPS      = 0
HOLD                         = 21
OUT_OF_SCOPE                 = 5
NOT_A_COLLECTIVE             = 31
```

freeze が 0 件である理由は1つである。本 audit 実行環境から全候補の accepted Source（公式サイト）へ
到達できず（§4.3）、**Source の実文言を確認できなかった**。本 task の Evidence rule（§6）は、
note・audit 文章を discovery hint に限定し Evidence authority として認めない。したがって
repository 上の記述だけで `source_attested_label` を確定した候補は1件も無い。
PASS を作らず、候補ごとに HOLD 理由を固定する。

## 2. Purpose

最初の `ShrineDeityCollective` / `ShrineDeityCollectiveMembership` backfill 対象を、
repository に記録された既存 Knowledge から決定的に洗い出し、候補ごとに
freeze / HOLD / OUT_OF_SCOPE / NOT_A_COLLECTIVE を固定する。

本書は candidate discovery と freeze 判定の記録であり、backfill seed の作成・import・
Production write は行わない。

## 3. Fixed Mother Ship decisions

```text
WRITE_PATH_AUTHORITY         = EXTEND_EXISTING_KNOWLEDGE_IMPORTER
BULK_WRITE_POLICY            = PROHIBITED_FOR_COLLECTIVE_BACKFILL
INTEGRITY_BOUNDARY           = DB_ROW_LOCAL_MODEL_SERVICE_CROSS_ROW
COLLECTIVE_IDENTITY          = SHRINE_PLUS_SOURCE_ATTESTED_LABEL
KNOWLEDGE_SEED_SCHEMA        = VERSION_1_1_WITH_1_0_BACKWARD_COMPATIBILITY
Membership Evidence          = B
Named Collective Migration   = C
```

本書はこれらを再解釈しない。

## 4. Candidate discovery method

### 4.1 対象

- `backend/temples/data/knowledge_seeds/*.json`（14 files。全件 `schema_version = "1.0"`、
  shrine block の重複 0）
  - Deity: `display_name` / `canonical_name` / `note`
  - History: `title` / `content` / `note`
  - Source: `key` / `source_type` / `url` / `verification_status` / `confidence` / `verified_at`
- 集合表現の扱いを決めた過去 audit（Batch 3〜17 の target-selection / seed-preflight /
  rollout / closure、Wave0 source packet freeze、collective-deity-contract-stress）
- `docs/audit/model-risk-release-contract.md` §6（9社の現在分類）
- `backend/temples/data/shrine_expansion_candidate_master.json`（wave0-014 の現在状態の読取のみ）

### 4.2 検索パターン

Deity 走査（116 hit）:

```text
collective|集合|総称|一括|柱|大神|三神|五神|八柱|十二|ほか|他|外
```

History 走査:

```text
総称|一括|奉称|と称|と呼|併祀|集合|外N柱|他N柱|[三五八十二]+柱|五所|三神|五神|大明神|権現|諸神|一族
```

audit 横断 grep: 各 hint label（八柱御子神・造化の三神・王子大神・二荒山大神・忌部五部神・
宮地嶽三柱大神・住吉五所大神・外８柱・二十二柱・箱根大神・寒川大明神・五神さま・三社権現・
比売大神・比咩大神・御霊大神・国内諸神・家族神・一族の神々）。

hit はすべて discovery hint として扱い、候補化・除外の判定は §6 の規則だけで行った。

### 4.3 Source 到達性（2026-09-30 実測）

HOLD 候補の accepted Source URL 18件へ、本環境から1回ずつ接続を試行した。

| 結果 | host |
|---|---|
| HTTPS `CONNECT` を proxy が 403 で拒否（policy denial） | `www.yasaka-jinja.or.jp` / `www.tokyodaijingu.or.jp` / `asojinja.or.jp` / `www.miyajidake.or.jp` / `www.nihondaiichisumiyoshigu.jp` / `www.oiwajinja.jp` / `www.ookunitamajinja.or.jp` / `samukawajinjya.jp` / `www.asakusajinja.jp` / `hakonejinja.or.jp` / `www.atsutajingu.or.jp` / `www.usajinguu.com` / `iwashimizu.or.jp` / `www.kibitujinja.com` |
| HTTP 403 | `ojijinja.tokyo.jp` / `www.futarasan.jp` / `awajinjya.org` / `www.tomiokahachimangu.or.jp` |

到達 0 / 18。repository 内に Source ページの本文 capture（HTML / text snapshot）は存在しない。
Wave0 source packet freeze も `他二十二柱` 等を audit 文章として記録するのみで、
Source 本文の capture ではない。

## 5. Complete candidate universe

57 items。1 item = 1 つの（Shrine, 集合表現または false-positive 表現）。

| 区分 | 件数 | ID |
|---|---:|---|
| Collective 候補（HOLD） | 21 | C01〜C21 |
| OUT_OF_SCOPE | 5 | X01〜X05 |
| NOT_A_COLLECTIVE | 31 | N01〜N31 |

## 6. Evidence rules applied

1. **Label authority**: `source_attested_label` は accepted Source の実文言だけで確定する。
   seed の `note`、audit の要約・引用、`canonical_name`、Deity 列挙からの合成は hint に限る。
2. **Count semantics**: `member_count` / `member_count_relation` は Source が明示した場合だけ
   確定する。hint から推定した値は「hint」として記録し、freeze 値にしない。
   Membership 行数から導出しない。
3. **member_list_status**: Source が完全性を明示した場合だけ `complete` / `partial` /
   `not_enumerated` を採る。確認できない場合は `not_determined`。個別名が存在することを理由に
   `complete` としない。
4. **Membership evidence（B）**: Membership ごとに、その所属関係を明示する Source を要する。
   Collective の Source を自動で流用しない。
5. **Deity identity**: 同一 Shrine + `ShrineDeity.display_name` 完全一致だけ。
   `canonical_name`・別名・部分一致・note・意味的同一性は使わない。
   本書の identity 確認は **repository seed 上の確認**であり、Production DB 照合ではない（§11）。
6. **候補化の規則**: repository hint が「Source が集合表現を用いている」と記録している
   ものを Collective 候補（HOLD 以上）とする。hint がその主張を含まず、個別祭神の列挙・
   編集上の柱数・別名・単独祭神名・境内社・宗教一般概念・歴史記述にとどまるものを
   `NOT_A_COLLECTIVE` とする。
7. **Legacy Deity（Named Collective Migration = C）**: 既存 `ShrineDeity` は全候補で **KEEP**。
   削除・書換・Source relation 変更・Runtime 変更をしない。

## 7. Freeze matrix（Collective 候補）

全行共通:

```text
Collective evidence        = HOLD（§4.3: Source 実文言 未確認）
Membership Source evidence = HOLD（同上。Collective Source の流用なし）
Legacy Deity action        = KEEP
verification_status / confidence / verified_at（Collective 用）= 未確定
  - 下表の Source 列の status / confidence は既存 ShrineKnowledgeSource seed 値であり、
    Collective Fact の値ではない。
```

「hint label」は repository 記述上の表記であり、`source_attested_label` として確定していない。

| ID | Shrine（seed name_jp / address） | Current representation | hint label | Source key / type / URL / status / confidence | count hint | list-status hint | Proposed Memberships（seed 上の exact display_name、各1件） | Freeze decision | Reason |
|---|---|---|---|---|---|---|---|---|---|
| C01 | 八坂神社 / 京都府京都市東山区祇園町北側625 | legacy collective-as-Deity（`ShrineDeity` 八柱御子神, enshrined） | 八柱御子神 | `src-999044` / shrine_official / https://www.yasaka-jinja.or.jp/about/saijin.html / source_confirmed / high | 8（note「8柱の総称」） | not_enumerated（note「個別列挙せず」） | なし（個別8柱の Deity は存在しない。legacy row `八柱御子神` は個別 Deity ではないため Membership にしない） | `HOLD_SOURCE_LABEL_NOT_PROVEN` | Source 実文言未確認 |
| C02 | 東京大神宮 / 東京都千代田区富士見2-4-1 | legacy collective-as-Deity（`ShrineDeity` 造化の三神, enshrined） | 造化の三神 | `src-999050` / shrine_official / https://www.tokyodaijingu.or.jp/syoukai/ / source_confirmed / high | 3（note） | 不明 | 天之御中主神・高御産巣日神・神産巣日神は note にのみ記載、Deity row 0 → `HOLD_MEMBERSHIP_DEITY_NOT_FOUND`（Deity を作らない） | `HOLD_SOURCE_LABEL_NOT_PROVEN` | Source 実文言未確認。Membership は Deity 不在 |
| C03 | 阿蘇神社 / 熊本県阿蘇市一の宮町宮地3083-1 | omitted aggregate（主祭神1柱のみ登録） | 家族神12神（hint は「健磐龍命をはじめ家族神12神を祀る」という文中表現） | `src-999035` / shrine_official / https://asojinja.or.jp/about/ / source_confirmed / high | 12（hint） | partial（1柱のみ個別確認の hint） | 健磐龍命（seed 1件）→ Membership evidence 未確認 | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認。hint 自体が集合名ではなく文中表現で、label として成立するか未確定 |
| C04 | 王子神社 / 東京都北区王子本町1-1-12 | members-only（5柱を個別登録、総称未登録） | 王子大神 | `batch14-oji-official` / shrine_official / http://ojijinja.tokyo.jp/goyuisho/index.html / source_confirmed / high | 5（hint） | 不明 | 伊邪那岐命・伊邪那美命・天照大御神・速玉之男命・事解之男命 | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認 |
| C05 | 二荒山神社 / 栃木県日光市山内2307 | members-only（3柱） | 二荒山大神 | `batch12-futarasan-official` / shrine_official / http://www.futarasan.jp/ / source_confirmed / high | 3（hint） | 不明 | 大己貴命・田心姫命・味耜高彦根命 | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認 |
| C06 | 安房神社 / 千葉県館山市大神宮589 | members-only（相殿5柱） | 忌部五部神 | `batch12-awa-official` / shrine_official / http://awajinjya.org/gosaijin.htm / source_confirmed / high | 5（hint） | 不明 | 櫛明玉命・天日鷲命・彦狭知命・手置帆負命・天目一箇命 | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認 |
| C07 | 宮地嶽神社 / 福岡県福津市宮司元町7-1 | members-only（3柱。総称は History tradition 文中のみ） | 宮地嶽三柱大神 | `src-999059` / shrine_official / https://www.miyajidake.or.jp/history/gosaijin / source_confirmed / high | 3（hint） | 不明 | 勝村大神・勝頼大神（seed 各1件）。hint の「神功皇后」は seed display_name `息長足比売命` と完全一致しない → `HOLD_MEMBERSHIP_DEITY_NOT_FOUND`（別名で解決しない） | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認。hint は tradition History 内の記述で current enshrinement の label か未確定 |
| C08 | 住吉神社（博多） / 福岡県福岡市博多区住吉3-1-51 | members-only（5柱） | 住吉五所大神 | `batch12-sumiyoshi-hakata-official` / shrine_official / https://www.nihondaiichisumiyoshigu.jp/about/ / source_confirmed / high | 5（hint） | 不明 | 底筒男神・中筒男神・表筒男神・天照皇大神・神功皇后 | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認 |
| C09 | 住吉神社（博多） / 同上 | members-only（3柱） | 住吉三神 | 同上 | 3（hint） | 不明 | 底筒男神・中筒男神・表筒男神 | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認。hint は note「住吉三神の一柱」のみで、Source が当社の label として用いるか未確認 |
| C10 | 富岡八幡宮 / 東京都江東区富岡1-20-3 | partial（主祭神1柱のみ） | なし（hint は「御祭神 応神天皇（誉田別命）外８柱」の残余表現） | `batch13-tomioka-official` / shrine_official / http://www.tomiokahachimangu.or.jp/annai/goyuisho/goyuisho.html / source_confirmed / high | 8（残余の hint） | not_enumerated（hint） | なし | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認。hint にも集合 label が無い（残余を label 化しない） |
| C11 | 御岩神社 / 茨城県日立市入四間町752 | partial（4柱のみ） | なし（hint は `他二十二柱`） | `wave0-db01-oiwa-official` / shrine_official / https://www.oiwajinja.jp/jinjasyoukai.html / source_confirmed / high | 22（残余の hint） | not_enumerated（hint） | なし | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 同上。境内別社（全山188柱）を本社へ混ぜない |
| C12 | 大國魂神社 / 東京都府中市宮町3-1 | omitted aggregate | 御霊大神 | `batch10-okunitama-official` / shrine_official / https://www.ookunitamajinja.or.jp/yuisho/ / source_confirmed / high | 未確定 | 不明 | なし | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認。当社祭神構造上の位置づけも未確定 |
| C13 | 大國魂神社 / 同上 | omitted aggregate | 国内諸神 | 同上 | 未確定 | 不明 | なし | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 同上 |
| C14 | 大國魂神社 / 同上 | members-only（配祀6柱） | 配祀六所（hint は note「配祀六所の一柱」、「武蔵総社六所宮」） | 同上 | 6（hint） | 不明 | 小野大神・小河大神・氷川大神・秩父大神・金佐奈大神・杉山大神 | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認。hint が label か社号由来の編集表現か未確定 |
| C15 | 寒川神社 / 神奈川県高座郡寒川町宮山3916 | members-only（2柱） | 寒川大明神 | `batch10-samukawa-deities` / shrine_official / https://samukawajinjya.jp/about/main-deities.html / source_confirmed / high | 2（hint） | 不明 | 寒川比古命・寒川比女命 | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認 |
| C16 | 浅草神社 / 東京都台東区浅草2-3-1 | members-only（3柱） | 三社権現 / 三社明神（hint は「呼ばれた」） | `batch10-asakusa-official` / shrine_official / https://www.asakusajinja.jp/asakusajinja/about/ / source_confirmed / high | 3（hint） | 不明 | 檜前浜成・檜前武成・土師真中知 | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認。hint が過去形で、current enshrinement label か歴史的呼称か未確定。2表記のどちらを identity にするかも Source 次第 |
| C17 | 箱根神社 / 神奈川県足柄下郡箱根町元箱根80-1 | members-only（3柱） | 箱根大神 | `batch9-hakone-official` / shrine_official / https://hakonejinja.or.jp/hakone/ / source_confirmed / high | 3（hint「御三神を併祀して箱根大神と奉称」） | 不明 | 瓊瓊杵尊・木花咲耶姫命・彦火火出見尊 | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認。Source は箱根神社・九頭龍神社・箱根元宮の共通ページで、本社への帰属も要確認 |
| C18 | 熱田神宮 / 愛知県名古屋市熱田区神宮1-1-1 | members-only（相殿5柱） | 五神さま | `src-999032` / shrine_official / https://www.atsutajingu.or.jp/jingu/about/enshrined.html / source_confirmed / high | 5（hint） | 不明 | 天照大神・素盞嗚尊・日本武尊・宮簀媛命・建稲種命 | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認 |
| C19 | 宇佐神宮 / 大分県宇佐市南宇佐2859 | legacy unit-as-Deity（`ShrineDeity` 比売大神） | 比売大神 | `batch9-usa-official` / shrine_official / https://www.usajinguu.com/lineage/ / source_confirmed / high | 未確定 | 不明 | なし | `HOLD_IDENTITY_RECONCILIATION` | 既存 seed は「公式の祭祀単位を保持し三女神へ展開しない」単一祭神として登録済み。単一祭神か集合かは identity 判断であり本 task で決めない |
| C20 | 石清水八幡宮 / 京都府八幡市八幡高坊30 | legacy unit-as-Deity（`ShrineDeity` 比咩大神、canonical_name に3柱名） | 比咩大神 | `src-999042` / shrine_official / https://iwashimizu.or.jp/about/ / source_confirmed / high | 未確定 | 不明 | なし（canonical_name からは解決しない） | `HOLD_IDENTITY_RECONCILIATION` | C19 と同型 |
| C21 | 吉備津神社 / 岡山県岡山市北区吉備津931 | partial（3柱登録、残余あり） | なし（hint は「等、一族の神々」） | `src-999054` / shrine_official / https://www.kibitujinja.com/about/engi.php / source_confirmed / high | 未確定 | not_determined | なし | `HOLD_SOURCE_LABEL_NOT_PROVEN` | 実文言未確認。hint は記述句で集合 label ではない |

## 8. Frozen candidate set

```text
FREEZE_COLLECTIVE_ONLY   = 0
FREEZE_WITH_MEMBERSHIPS  = 0
```

凍結された候補は無い。§9 の再判定条件を満たすまで、A-5b backfill seed は機械的に導出できない。

## 9. HOLD set（21）

| Status | 件数 | ID |
|---|---:|---|
| `HOLD_SOURCE_LABEL_NOT_PROVEN` | 19 | C01〜C18, C21 |
| `HOLD_IDENTITY_RECONCILIATION` | 2 | C19, C20 |

副次的に記録した Membership HOLD（Collective の HOLD 理由とは別に固定）:

| ID | Membership | Status |
|---|---|---|
| C02 | 天之御中主神・高御産巣日神・神産巣日神 | `HOLD_MEMBERSHIP_DEITY_NOT_FOUND`（seed に Deity row 無し） |
| C07 | 神功皇后（hint 表記） | `HOLD_MEMBERSHIP_DEITY_NOT_FOUND`（seed display_name は `息長足比売命`） |
| 全候補の他 Membership | — | `HOLD_MEMBERSHIP_EVIDENCE`（Membership 固有 Source 未確認） |

### 再判定条件（HOLD_SOURCE_LABEL_NOT_PROVEN）

候補ごとに、accepted Source の本文を取得し、次を記録した場合だけ freeze へ進める。

1. Source 上の集合表現の完全一致文字列（前後空白なし、正規化なし）
2. その表現が当該 Shrine 本社の **current enshrinement** を指すこと（歴史的呼称・境内社・
   宗教一般概念でないこと）
3. 柱数の明示有無と種類（exact / minimum / approximate、無ければ unspecified / null）
4. 構成の完全性の明示有無（無ければ `not_determined`）
5. Membership ごとに、その神がその集合に属することを明示する記述の有無

本環境で再判定するには、§4.3 の host への network access が必要である。

## 10. OUT_OF_SCOPE set（5）

| ID | Shrine | Status | Reason |
|---|---|---|---|
| X01 | 宮城縣護國神社（wave0-014） | `OUT_OF_SCOPE_WAVE0` | Candidate Master は `HOLD / MODEL_CHANGE_REQUIRED / W0-DB03`、G3 Model Risk record も HOLD。hydrate・Seed 作成・HOLD 解除・lifecycle 変更をしない |
| X02 | 高千穂神社 | `OUT_OF_SCOPE_MODEL_RELEASE` | Model Risk Release Contract §6 `MODEL_CHANGE_REQUIRED`（「ほか8柱」）。Knowledge seed に存在しない。model が表現可能になったことは Source / curation / lifecycle gate を満たさない |
| X03 | 冠稲荷神社 | `OUT_OF_SCOPE_MODEL_RELEASE` | 同 §6 `MODEL_CHANGE_REQUIRED`（「ほか15柱以上」）。Knowledge seed に存在しない |
| X04 | 千葉神社 | `OUT_OF_SCOPE_MODEL_RELEASE` | 同 §6 `MODEL_CHANGE_REQUIRED`（主祭神 identity 未解決の神仏習合ケース。集合祭神の問題ではない） |
| X05 | 靖國神社 | `OUT_OF_SCOPE_PRODUCT_POLICY` | 同 §6 `PRODUCT_DECISION_REQUIRED` |

Model Risk Release Contract §6 の残り5社（千住神社・榛名神社・古峯神社・愛宕神社・赤城神社）は
集合祭神の問題として分類されていないため、本 universe に含めない。

## 11. Production reconciliation

```text
PROD_RECONCILIATION = NOT_RUN
```

- 本 session に Production の read-only credential は無く、repository 承認済みの read-only path も
  本 task で使用していない。raw Production access は行っていない。
- 本書の Shrine identity・Deity identity は **repository seed 上の記録**である
  （全候補とも seed 上は shrine block 1件、提案 Membership の display_name は block 内 1件）。
  Production 上の Shrine / ShrineDeity / Source relation / 既存 Collective・Membership の有無は
  未照合であり、PASS として扱わない。
- freeze 後も、seed 実行前に Production reconciliation が必要である。

## 12. Expected shape of the future A-5b backfill seed

本書時点では凍結候補 0 件のため、seed は作成しない。再判定後に作る seed の形だけを固定する。

```text
schema_version = "1.1"
sources        = freeze した Collective / Membership が参照する Source のみ
                 （既存 Source と同一 source_type + normalized URL で REUSE_EXISTING になること）
shrines[]      = freeze した候補の Shrine のみ
  shrine_ref   = 既存 seed と同じ name_jp / address
  deities      = []   （既存 Deity は再宣言しない。Membership は既存 Deity を参照する）
  histories    = []
  collectives[]
    source_attested_label = Source 実文言（完全一致）
    role / sort_order / member_count / member_count_relation / member_list_status
                          = freeze 値（Source 明示のみ）
    verification_status / confidence / verified_at = freeze 値
    source_keys           = Collective 固有（非空）
    memberships[]         = FREEZE_WITH_MEMBERSHIPS の場合のみ
      deity_ref           = {"display_name": 既存 Deity の完全一致名}
      source_keys         = Membership 固有（非空、Collective から継承しない）
```

legacy `ShrineDeity`（C01 八柱御子神・C02 造化の三神・C19 比売大神・C20 比咩大神）は
seed に含めず、KEEP する。

## 13. NOT_A_COLLECTIVE set（31）

| ID | Shrine | 表現 | Reason |
|---|---|---|---|
| N01 | 伏見稲荷大社 | 四大神 | 摂社四大神（中社摂社）の祭神名として登録済み。境内社の祭神を本社の集合へ混ぜない |
| N02 | 鶴岡八幡宮 | 八幡神（三柱） | 宗教一般概念。当社固有の Source-attested label の hint 無し（Source は secondary / tourism） |
| N03 | 筑波山神社 | 筑波男大神 / 筑波女大神 | 各1柱の別称。集合ではない |
| N04 | 住吉大社 | 三神 | History（鎮座伝承）の記述。当社の label 主張の hint 無し |
| N05 | 春日大社 | 四柱併祀 | History（創建）の出来事記述 |
| N06 | 枚岡神社 | 二神 | History（奉遷）の出来事記述 |
| N07 | 根津神社 | 主祭神三柱 / 相殿二柱 | role 区分の編集上の柱数。集合 label の hint 無し |
| N08 | 赤坂氷川神社 | 三柱 | 個別列挙のみ |
| N09 | 葛西神社 | 三柱 | 個別列挙のみ |
| N10 | 櫻木神社 | 四柱 | 個別列挙のみ |
| N11 | 白山神社 | 三柱 | 個別列挙のみ |
| N12 | 妙義神社 | 4柱 | 個別列挙のみ |
| N13 | 足利織姫神社 | 二柱 | 個別列挙のみ |
| N14 | 鶴嶺八幡宮 | 應神天皇・仁徳天皇・佐塚大神 | 個別列挙のみ |
| N15 | 波上宮 | 御祭神三柱 / 別鎮斎 | 区分の列挙のみ |
| N16 | 川越氷川神社 | 5柱の家族神 | audit の編集的記述。Source label の hint 無し |
| N17 | 玉前神社 | 家族神 | 玉依姫命のみ。家族神は audit 上「不明値」で label の hint 無し |
| N18 | 小網神社 | お稲荷大神 / 弁財天 / 福禄寿 | 別称・関連信仰対象（福禄寿は ASSOCIATED_WORSHIP_TARGET として別課題） |
| N19 | 富士山本宮浅間大社 | 浅間大神 | 1柱の別称 |
| N20 | 出雲大社 | 所造天下大神 | 1柱の別名 |
| N21 | 香取神宮 | 伊波比主命 | 1柱の別名 |
| N22 | 白山比咩神社 | 菊理媛尊 | 1柱の別名 |
| N23 | 単独祭神名（大神を含む） | 大國魂大神・熱田大神・武甕槌大神・九頭龍大神・天満大神・猿田彦大神・八幡大神（宇佐）・大物主大神・大国主大神（高瀬）・賀茂別雷大神・伊夜日子大神（彌彦神社 canonical_name） | 1柱の祭神名 |
| N24 | 高良大社 | 八幡大神 / 住吉大神 | 各1柱として登録された祭神名 |
| N25 | 芝大神宮 | 外宮 | 伊勢の外宮を指す語。集合ではない |
| N26 | 給田六所神社 | 六所 | 社号の由来（本宮の六柱）。当社の祭神集合ではない |
| N27 | 箭弓稲荷神社 | 團十郎稲荷 | 末社。本社へ混ぜない |
| N28 | 武蔵御嶽神社 / 三峯神社 | 大口真神 | 境内独立社の祭神 / 御眷属 |
| N29 | 大神神社 / 岡田宮 | packet 境界 note | 集合表現を作らない旨の境界記録 |
| N30 | 王子神社 / 波上宮 | 熊野三社権現 / 熊野権現 | History 内の他社・歴史的呼称 |
| N31 | 富岡八幡宮 / 護王神社 / 妙義神社 / 小網神社 | 「江戸最大の八幡様」「護王大明神」「波己曽の大神」「小網稲荷大明神」 | History 内の称号・旧称 |

## 14. Non-goals

本 task は次を行っていない。

- backfill seed の作成（`backend/temples/data/knowledge_seeds/*backfill*.json` なし）、
  既存 seed の 1.1 化
- `import_shrine_knowledge` の実行（validate-only / dry-run / apply とも）、isolated apply
- Production への接続・write
- models / migrations / `knowledge_seed.py` / `import_shrine_knowledge.py` / serializers /
  Evidence Gate / Recommendation Eligibility / Concierge / Compass / Deep Dive /
  Evidence Transport / frontend / mobile / Score / Ranking の変更
- Candidate Master・wave0 lifecycle data・wave0-014・Model Risk status の変更
- legacy `ShrineDeity` の削除・書換
- note からの Fact 導出

## 15. Completion checklist

| 項目 | 結果 |
|---|---|
| Base SHA / branch 記録 | done |
| Mother Ship decisions 記録（再解釈なし） | done |
| repository 全 seed の走査（Deity 116 hit + History） | done |
| 既知 anchor 以外の discovery（大國魂・寒川・浅草・箱根・熱田・宇佐・石清水・吉備津・富岡・御岩 等） | done |
| candidate universe 全件の分類（57） | done |
| freeze 行の必須条件（exact label / non-empty Collective Source evidence / count / list status） | 対象 0 件（freeze なし） |
| FREEZE_WITH_MEMBERSHIPS の Membership 条件 | 対象 0 件 |
| note 由来 Fact | 0 件 |
| OUT_OF_SCOPE の明示（wave0-014 / 高千穂 / 冠稲荷 / 千葉 / 靖國） | done |
| Source 到達性の記録 | done（0 / 18） |
| Production reconciliation | `NOT_RUN` |
| Production writes | 0 |
| Knowledge Seed writes | 0 |
| Model / Migration changes | 0 |
| Candidate Master / wave0-014 changes | 0 |
| Runtime changes | 0 |

## 16. Final classification

```text
A5B_CANDIDATE_UNIVERSE_RECORDED_SOURCE_VERIFICATION_BLOCKED
```

- `A5B_SOURCE_BACKED_BACKFILL_CANDIDATES_FROZEN` は付与しない（freeze 0 件）。
- 次工程は、§4.3 の Source へ到達できる環境で §9 の再判定条件に沿って候補ごとの
  Source 実文言を記録し、本書を更新して freeze を確定すること。
- backfill seed 作成・isolated apply は freeze 確定後の別 task とする。
