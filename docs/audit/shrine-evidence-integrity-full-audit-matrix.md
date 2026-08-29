# Shrine Evidence Integrity Full Audit — Per-Shrine Matrix

Companion to [`shrine-evidence-integrity-full-audit.md`](shrine-evidence-integrity-full-audit.md)
(PR-C). One canonical row per unique real shrine identity. **Read-only audit —
no Production / DB / Spreadsheet / Recommendation / GoriyakuTag / Knowledge /
`Shrine.goriyaku` / Need-mapping / model / migration / fixture / seed / frontend
change.**

- **Base SHA:** `1ecceb0e691050e68fcc0baa90f32940041c6cce` (`origin/develop`, PR #2613 merged)
- **Date:** 2026-08-29
- **Canonical audit units:** **103** (`FULL_AUDIT_DENOMINATOR = 103` [MS]).
  `RAW_PRODUCTION_SHRINE_ROWS = 108` − id 102 (QA fixture `テスト確認神社 20260611`)
  − id 105 (`NON_SHRINE_ARTIFACT` `広島市`) − ids 101 / 103 / 104
  (`SAME_REAL_SHRINE_DUPLICATE` shadows of primaries 22 / 21 / 49).
- **Production read:** sanctioned read-only credential bridge
  (`scripts/migration_safety/readonly_query.sh` + repo-external
  `~/.config/kami-musubi/production-db.env`). Every query passed
  `guard.py check-readonly-sql`. Credential value never printed / logged / in argv.

## Column legend

| Column | Meaning |
|---|---|
| `pref` | prefecture parsed from `Shrine.address` (`?` = address carries a `日本、〒…` Google-formatted prefix — both are Tokyo world) |
| `gori` | `Shrine.goriyaku` text shape: `DELIM` = delimiter-separated canonical labels · `PROSE` = free sentence · `EMPTY` |
| `d/h` | `ShrineDeity` rows / `ShrineHistory` rows (`(Nd)` = N of the history rows are `verification_status = disputed`) |
| `src` | distinct `ShrineKnowledgeSource` rows reachable from this shrine's deity/history |
| `fr d/h` | Evidence-Gate **fact-ready** deity / history counts (`decide_fact_usability`: fact `source_confirmed`/`reviewed` AND ≥1 `source_confirmed`/`reviewed` Source). `disputed` history is not fact-ready. |
| `purpose_conn` | runtime Purpose connectivity of the stored `goriyaku_tags` against **current** `NEED_TO_GORIYAKU_IDS` [repo]: `WIRED` = ≥1 tag id ∈ a Need's id set · `UNWIRED_CANONICAL` = tags exist but none is consumed by any Need · `NOT_APPLICABLE` = zero `goriyaku_tags` |
| `status` | Phase 7 cross-layer integrity: `MATCH` / `PARTIAL` / `UNSUPPORTED` / `MISSING` / `REVIEW_REQUIRED` |
| `root_causes` | audit-only labels (`·concept` = the shrine also carries wired tags — the mapping gap is at the concept level, not shrine-fatal) |
| `S` | `Y` = official Source fetched and compared **this session** (10 shrines); `·` = Source recorded, not re-fetched (Fact fidelity therefore `REVIEW_REQUIRED` per the pilot's M8 rule) |

## Status assignment rule (Phase 7)

- **MATCH** — official Source fetched this session **and** deity + history + every
  `goriyaku` label confirmed against it. → **1** shrine (id 6 太宰府天満宮).
- **REVIEW_REQUIRED** — knowledge-bearing but a specific integrity concern blocks
  resolution: no official/primary Source at all (10, 22), `goriyaku` stored as
  prose with tags not `parse_goriyaku`-derivable (22), sampled but deity identity
  unconfirmed on the fetched page (26), or zero `goriyaku` with eligibility
  genuinely `UNKNOWN` this session (106). → **4** shrines.
- **MISSING** — zero Knowledge **and** zero Source; the layer needed to
  substantiate the stored `goriyaku` is absent. → **14** shrines.
- **PARTIAL** — everything else knowledge-bearing: Evidence-Gate-usable Knowledge
  is present and structurally Source-linked, but the `goriyaku` is
  `LEGACY_EXISTING` without Recommendation-Evidence-Review provenance and/or the
  Source was not re-fetched this session. → **84** shrines.
- **UNSUPPORTED** — stored Recommendation evidence contradicted by a reviewed
  Source. → **0** at the whole-shrine level (individual labels are
  unsupported-on-source for ids 1 / 10 / 64 / 99, but each of those shrines has
  other valid layers → `PARTIAL` / `REVIEW_REQUIRED`).

### A. ids 1–40

| id | name | pref | gori | d/h | src | source_types | goriyaku_tags (name) | fr d/h | purpose_conn | status | root_causes | S |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 明治神宮 | 東京都 | DELIM | 2/1 | 2 | shrine_official,user_observation | 縁結び/厄除け/交通安全 | 2/1 | WIRED | **PARTIAL** | GORIYAKU_EVIDENCE_GAP;PROVENANCE_GAP | Y |
| 2 | 伏見稲荷大社 | 京都府 | DELIM | 5/1 | 1 | shrine_official | 商売繁盛/五穀豊穣 | 5/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 3 | 伊勢神宮（内宮） | 三重県 | DELIM | 1/1 | 1 | shrine_official | 厄除け/開運/家内安全 | 1/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 4 | 出雲大社 | 島根県 | DELIM | 1/3 | 2 | cultural_property,shrine_official | 縁結び/開運/福徳 | 1/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 5 | 春日大社 | 奈良県 | DELIM | 4/1 | 1 | shrine_official | 厄除け/開運/家内安全 | 4/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 6 | 太宰府天満宮 | 福岡県 | DELIM | 1/1 | 1 | shrine_official | 厄除け/学業成就/合格祈願 | 1/1 | WIRED | **MATCH** | - | Y |
| 7 | 熱田神宮 | 愛知県 | DELIM | 6/1 | 1 | shrine_official | 厄除け/開運/家内安全 | 6/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 8 | 宇佐神宮 | 大分県 | DELIM | 3/1 | 1 | shrine_official | 厄除け/家内安全/勝運 | 3/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 9 | 日光東照宮 | 栃木県 | DELIM | 1/3 | 2 | cultural_property,shrine_official | 厄除け/開運/家内安全 | 1/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 10 | 鶴岡八幡宮 | 神奈川県 | DELIM | 3/5 | 2 | secondary_editorial,tourism_official | 厄除け/勝運/仕事運 | 3/5 | WIRED | **REVIEW_REQUIRED** | SOURCE_GAP;PROVENANCE_GAP;GORIYAKU_EVIDENCE_GAP | Y |
| 11 | 住吉大社 | 大阪府 | DELIM | 4/1 | 1 | shrine_official | 厄除け/交通安全/航海安全 | 4/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 12 | 石清水八幡宮 | 京都府 | DELIM | 3/1 | 1 | shrine_official | 厄除け/開運/勝運 | 3/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 13 | 金刀比羅宮 | 香川県 | DELIM | 2/2 | 1 | shrine_official | 交通安全/開運/海上安全 | 2/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 14 | 鹿島神宮 | 茨城県 | DELIM | 1/1 | 1 | shrine_official | 厄除け/勝運/武運長久 | 1/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 15 | 香取神宮 | 千葉県 | DELIM | 1/0 | 1 | shrine_official | 厄除け/開運/勝運 | 1/0 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 16 | 氷川神社（大宮） | 埼玉県 | DELIM | 3/1 | 1 | shrine_official | 縁結び/厄除け/家内安全 | 3/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 17 | 三峯神社 | 埼玉県 | DELIM | 2/2 | 1 | shrine_official | 厄除け/開運/仕事運 | 2/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 18 | 箱根神社 | 神奈川県 | DELIM | 3/1 | 1 | shrine_official | 厄除け/交通安全/開運 | 3/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 19 | 富士山本宮浅間大社 | 静岡県 | DELIM | 3/2 | 1 | shrine_official | 開運/家内安全/安産 | 3/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 20 | 諏訪大社（上社本宮） | 長野県 | DELIM | 1/2 | 1 | shrine_official | 厄除け/開運/勝運 | 1/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 21 | 長太稲荷神社 | ? | PROSE | 0/0 | 0 | - | 商売繁盛/五穀豊穣 | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP;TAG_INTEGRITY_GAP;IDENTITY_DATA_GAP | · |
| 22 | 給田六所神社 | ? | PROSE | 2/4 | 2 | local_history,secondary_editorial | 家内安全 | 2/4 | WIRED | **REVIEW_REQUIRED** | PROVENANCE_GAP;SOURCE_GAP;TAG_INTEGRITY_GAP;IDENTITY_DATA_GAP | · |
| 23 | 神田神社（神田明神） | 東京都 | DELIM | 3/5 | 2 | secondary_editorial,shrine_official | 縁結び/商売繁盛/仕事運 | 3/5 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 24 | 浅草神社 | 東京都 | DELIM | 3/2 | 1 | shrine_official | 厄除け/商売繁盛/家内安全 | 3/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 25 | 大國魂神社 | 東京都 | DELIM | 7/2 | 1 | shrine_official | 縁結び/厄除け/開運 | 7/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 26 | 寒川神社 | 神奈川県 | DELIM | 2/2 | 1 | shrine_official | 厄除け/開運/八方除 | 2/2 | WIRED | **REVIEW_REQUIRED** | PURPOSE_MAPPING_GAP;PROVENANCE_GAP | Y |
| 27 | 榛名神社 | 群馬県 | DELIM | 0/0 | 0 | - | 商売繁盛/五穀豊穣/開運 | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP | · |
| 28 | 筑波山神社 | 茨城県 | DELIM | 2/1 | 1 | shrine_official | 縁結び/開運/夫婦円満 | 2/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 29 | 阿佐ヶ谷神明宮 | 東京都 | DELIM | 3/0 | 2 | secondary_editorial,shrine_official | 縁結び/厄除け/八難除 | 3/0 | WIRED | **PARTIAL** | PROVENANCE_GAP;PURPOSE_MAPPING_GAP·concept | · |
| 30 | 彌彦神社 | 新潟県 | DELIM | 1/1 | 1 | shrine_official | 縁結び/開運/勝運 | 1/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 31 | 氣多大社 | 石川県 | DELIM | 1/1 | 1 | shrine_official | 縁結び/開運/恋愛成就 | 1/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 32 | 越中一宮 高瀬神社 | 富山県 | DELIM | 3/2 | 1 | shrine_official | 厄除け/開運/家内安全 | 3/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 33 | 椿大神社 | 三重県 | DELIM | 5/1 | 1 | shrine_official | 開運/仕事運/導き | 5/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 34 | 賀茂御祖神社（下鴨神社） | 京都府 | DELIM | 2/5 | 1 | shrine_official | 縁結び/厄除け/美容 | 2/5 | WIRED | **PARTIAL** | PROVENANCE_GAP;PURPOSE_MAPPING_GAP·concept | · |
| 35 | 賀茂別雷神社（上賀茂神社） | 京都府 | DELIM | 1/2 | 1 | shrine_official | 厄除け/勝運/方除け | 1/2 | WIRED | **PARTIAL** | PROVENANCE_GAP;PURPOSE_MAPPING_GAP·concept | · |
| 36 | 生田神社 | 兵庫県 | DELIM | 1/1 | 1 | shrine_official | 縁結び/恋愛成就/健康長寿 | 1/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 37 | 吉備津神社 | 岡山県 | DELIM | 3/2 | 1 | shrine_official | 厄除け/開運/学業成就 | 3/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 38 | 厳島神社 | 広島県 | DELIM | 3/3 | 2 | cultural_property,shrine_official | 開運/海上安全/芸能 | 3/3 | WIRED | **PARTIAL** | PROVENANCE_GAP;PURPOSE_MAPPING_GAP·concept | · |
| 39 | 宮地嶽神社 | 福岡県 | DELIM | 3/1 | 1 | shrine_official | 交通安全/商売繁盛/開運 | 3/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 40 | 川越氷川神社 | 埼玉県 | DELIM | 5/2 | 1 | shrine_official | 縁結び/厄除け/家庭円満 | 5/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |

### B. ids 41–80

| id | name | pref | gori | d/h | src | source_types | goriyaku_tags (name) | fr d/h | purpose_conn | status | root_causes | S |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 41 | 白山比咩神社 | 石川県 | DELIM | 3/3 | 1 | shrine_official | 縁結び/厄除け/開運 | 3/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 42 | 高千穂神社 | 宮崎県 | DELIM | 0/0 | 0 | - | 縁結び/厄除け/家内安全 | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP | · |
| 43 | 日枝神社 | 東京都 | DELIM | 4/2 | 1 | shrine_official | 商売繁盛/仕事運/出世運 | 4/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 44 | 東京大神宮 | 東京都 | DELIM | 4/1 | 1 | shrine_official | 縁結び/恋愛成就 | 4/1 | WIRED | **PARTIAL** | GORIYAKU_EVIDENCE_GAP | Y |
| 45 | 芝大神宮 | 東京都 | DELIM | 2/2 | 1 | shrine_official | 縁結び/商売繁盛 | 2/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 46 | 愛宕神社 | 東京都 | DELIM | 0/0 | 0 | - | 仕事運/出世運 | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP | · |
| 47 | 亀戸天神社 | 東京都 | DELIM | 2/2 | 1 | shrine_official | 学業成就/合格祈願 | 2/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 48 | 根津神社 | 東京都 | DELIM | 5/2 | 1 | shrine_official | 縁結び/厄除け | 5/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 49 | 富岡八幡宮 | 東京都 | DELIM | 1/2 | 1 | shrine_official | 商売繁盛/勝運 | 1/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 50 | 品川神社 | 東京都 | DELIM | 3/3 | 2 | government,shrine_official | 開運/金運 | 3/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 51 | 大宮八幡宮 | 東京都 | DELIM | 3/1 | 1 | shrine_official | 家内安全/安産 | 3/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 52 | 江島神社 | 神奈川県 | DELIM | 3/1 | 1 | shrine_official | 縁結び/芸能運 | 3/1 | WIRED | **PARTIAL** | PROVENANCE_GAP;PURPOSE_MAPPING_GAP·concept | · |
| 53 | 水戸東照宮 | 茨城県 | DELIM | 2/4 | 1 | shrine_official | 開運/勝運 | 2/4 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 54 | 二荒山神社 | 栃木県 | DELIM | 3/1 | 1 | shrine_official | 縁結び/開運 | 3/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 55 | 貴船神社 | 京都府 | DELIM | 2/1 | 1 | shrine_official | 縁結び/恋愛成就 | 2/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 56 | 八坂神社 | 京都府 | DELIM | 3/3 | 1 | shrine_official | 厄除け/開運/美容 | 3/3 | WIRED | **PARTIAL** | PROVENANCE_GAP;PURPOSE_MAPPING_GAP·concept | · |
| 57 | 住吉神社（博多） | 福岡県 | DELIM | 5/2 | 1 | shrine_official | 厄除け/航海安全 | 5/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 58 | 靖國神社 | 東京都 | DELIM | 0/0 | 0 | - | 厄除け/家内安全/勝運 | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP | · |
| 59 | 乃木神社 | 東京都 | DELIM | 2/3 | 2 | secondary_editorial,shrine_official | 家内安全/勝運/仕事運 | 2/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 60 | 赤坂氷川神社 | 東京都 | DELIM | 3/2 | 1 | shrine_official | 縁結び/厄除け/仕事運 | 3/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 61 | 花園神社 | 東京都 | DELIM | 0/0 | 0 | - | 商売繁盛/開運/芸能運 | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP;PURPOSE_MAPPING_GAP·concept | · |
| 62 | 小網神社 | 東京都 | DELIM | 2/1 | 1 | shrine_official | 商売繁盛/金運/強運厄除け | 2/1 | WIRED | **PARTIAL** | GORIYAKU_EVIDENCE_GAP | Y |
| 63 | 鳥越神社 | 東京都 | DELIM | 0/0 | 0 | - | 厄除け/商売繁盛/開運 | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP | · |
| 64 | 湯島天満宮 | 東京都 | DELIM | 2/4 | 1 | shrine_official | 開運/学業成就/合格祈願 | 2/4 | WIRED | **PARTIAL** | PROVENANCE_GAP;GORIYAKU_EVIDENCE_GAP | Y |
| 65 | 白山神社 | 東京都 | DELIM | 3/3 | 1 | shrine_official | 縁結び/厄除け/家内安全 | 3/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 66 | 王子神社 | 東京都 | DELIM | 5/3 | 1 | shrine_official | 厄除け/開運/家内安全 | 5/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 67 | 千住神社 | 東京都 | DELIM | 0/0 | 0 | - | 厄除け/商売繁盛/開運 | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP | · |
| 68 | 葛西神社 | 東京都 | DELIM | 3/3 | 1 | shrine_official | 厄除け/家内安全/勝運 | 3/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 69 | 穴守稲荷神社 | 東京都 | DELIM | 1/3 | 1 | shrine_official | 交通安全/商売繁盛/開運 | 1/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 70 | 多摩川浅間神社 | 東京都 | DELIM | 1/3 | 1 | shrine_official | 縁結び/開運/家内安全 | 1/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 71 | 武蔵御嶽神社 | 東京都 | DELIM | 4/5 | 1 | shrine_official | 厄除け/開運/勝運 | 4/5 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 72 | 武蔵一宮 氷川女體神社 | 埼玉県 | DELIM | 0/0 | 0 | - | 縁結び/家内安全/安産 | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP | · |
| 73 | 調神社 | 埼玉県 | DELIM | 0/0 | 0 | - | 厄除け/開運/勝運 | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP | · |
| 74 | 秩父神社 | 埼玉県 | DELIM | 4/2 | 1 | shrine_official | 開運/家内安全/学業成就 | 4/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 75 | 鷲宮神社 | 埼玉県 | DELIM | 2/2 | 1 | shrine_official | 厄除け/開運/家内安全 | 2/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 76 | 箭弓稲荷神社 | 埼玉県 | DELIM | 1/3 | 1 | shrine_official | 商売繁盛/開運/芸能運 | 1/3 | WIRED | **PARTIAL** | PROVENANCE_GAP;PURPOSE_MAPPING_GAP·concept | · |
| 77 | 安房神社 | 千葉県 | DELIM | 7/2 | 1 | shrine_official | 開運/仕事運/技芸上達 | 7/2 | WIRED | **PARTIAL** | PROVENANCE_GAP;PURPOSE_MAPPING_GAP·concept | · |
| 78 | 千葉神社 | 千葉県 | DELIM | 0/0 | 0 | - | 厄除け/開運/八方除け | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP | · |
| 79 | 玉前神社 | 千葉県 | DELIM | 1/3 | 1 | shrine_official | 縁結び/開運/安産 | 1/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 80 | 櫻木神社 | 千葉県 | DELIM | 4/3 | 1 | shrine_official | 縁結び/開運/学業成就 | 4/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |

### C. ids 81–108 (incl. 106–108)

| id | name | pref | gori | d/h | src | source_types | goriyaku_tags (name) | fr d/h | purpose_conn | status | root_causes | S |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 81 | 大洗磯前神社 | 茨城県 | DELIM | 2/1 | 1 | shrine_official | 厄除け/開運/海上安全 | 2/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 82 | 笠間稲荷神社 | 茨城県 | DELIM | 1/2 | 1 | shrine_official | 商売繁盛/五穀豊穣/開運 | 1/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 83 | 酒列磯前神社 | 茨城県 | DELIM | 2/2 | 1 | shrine_official | 厄除け/開運/病気平癒 | 2/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 84 | 宇都宮二荒山神社 | 栃木県 | DELIM | 3/3 | 1 | shrine_official | 縁結び/開運/家内安全 | 3/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 85 | 足利織姫神社 | 栃木県 | DELIM | 2/3 | 1 | shrine_official | 縁結び/学業成就/仕事運 | 2/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 86 | 古峯神社 | 栃木県 | DELIM | 0/0 | 0 | - | 厄除け/開運/火防 | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP;PURPOSE_MAPPING_GAP·concept | · |
| 87 | 冠稲荷神社 | 群馬県 | DELIM | 0/0 | 0 | - | 縁結び/安産/子宝 | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP | · |
| 88 | 妙義神社 | 群馬県 | DELIM | 4/4 | 2 | cultural_property,shrine_official | 厄除け/開運/勝運 | 4/4 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 89 | 赤城神社 | 群馬県 | DELIM | 0/0 | 0 | - | 縁結び/開運/心願成就 | 0/0 | WIRED | **MISSING** | KNOWLEDGE_GAP;SOURCE_GAP;GORIYAKU_EVIDENCE_GAP | · |
| 90 | 鶴嶺八幡宮 | 神奈川県 | DELIM | 4/4 | 1 | shrine_official | 厄除け/家内安全/勝運 | 4/4 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 91 | 森戸大明神 | 神奈川県 | DELIM | 2/1 | 1 | shrine_official | 縁結び/開運/海上安全 | 2/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 92 | 報徳二宮神社 | 神奈川県 | DELIM | 1/4 | 1 | shrine_official | 開運/学業成就/仕事運 | 1/4 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 93 | 九頭龍神社 新宮 | 神奈川県 | DELIM | 1/1 | 1 | shrine_official | 縁結び/開運/心願成就 | 1/1 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 94 | 平塚八幡宮 | 神奈川県 | DELIM | 3/3 | 1 | shrine_official | 厄除け/家内安全/勝運 | 3/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 95 | 忌宮神社 | 山口県 | DELIM | 3/2 | 1 | shrine_official | 厄除け/開運/家内安全 | 3/2 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 96 | 高良大社 | 福岡県 | DELIM | 3/2 | 1 | shrine_official | 厄除け/開運/延命長寿 | 3/2 | WIRED | **PARTIAL** | PROVENANCE_GAP;PURPOSE_MAPPING_GAP·concept | · |
| 97 | 寳登山神社 | 埼玉県 | DELIM | 3/1 | 1 | shrine_official | 開運/家内安全/火防 | 3/1 | WIRED | **PARTIAL** | PROVENANCE_GAP;PURPOSE_MAPPING_GAP·concept | · |
| 98 | 枚岡神社 | 大阪府 | DELIM | 4/3 | 1 | shrine_official | 厄除け/商売繁盛/開運 | 4/3 | WIRED | **PARTIAL** | PROVENANCE_GAP | · |
| 99 | 護王神社 | 京都府 | DELIM | 4/2 | 1 | shrine_official | 厄除け/勝運/足腰健康 | 4/2 | WIRED | **PARTIAL** | GORIYAKU_EVIDENCE_GAP;PROVENANCE_GAP | Y |
| 100 | 阿蘇神社 | 熊本県 | DELIM | 1/1 | 1 | shrine_official | 開運/家内安全/農業守護 | 1/1 | WIRED | **PARTIAL** | PROVENANCE_GAP;PURPOSE_MAPPING_GAP·concept | · |
| 106 | 北海道神宮 | 北海道 | EMPTY | 4/3 | 1 | shrine_official | - | 4/3 | NOT_APPLICABLE | **REVIEW_REQUIRED** | GORIYAKU_EVIDENCE_GAP | Y |
| 107 | 建部大社 | 滋賀県 | EMPTY | 2/4(2d) | 2 | government,shrine_official | - | 2/2 | NOT_APPLICABLE | **PARTIAL** | GORIYAKU_EVIDENCE_GAP | Y |
| 108 | 波上宮 | 沖縄県 | EMPTY | 6/6 | 1 | shrine_official | - | 6/6 | NOT_APPLICABLE | **PARTIAL** | GORIYAKU_EVIDENCE_GAP | Y |

## Excluded rows (not canonical audit units — recorded for traceability)

| id | name_jp | reason | audit primary | notes |
|---|---|---|---|---|
| 101 | 給田六所神社 | `SAME_REAL_SHRINE_DUPLICATE` shadow | **22** | `place_ref = ChIJl-MEepfxGGAR1Eo44p__GaE`; goriyaku empty; 0 deity / 0 history / 0 source; byte-identical address+coords to id 22 (`production-canonical-set-preflight.md` §10) |
| 103 | 長太稲荷神社 | `SAME_REAL_SHRINE_DUPLICATE` shadow | **21** | `place_ref = ChIJX19mq8nxGGARsA2kP4gX90M`; empty; 0/0/0; byte-identical to id 21 |
| 104 | 富岡八幡宮 | `SAME_REAL_SHRINE_DUPLICATE` shadow | **49** | `place_ref = ChIJK11I4BGJGGAR5mZswigcu58`; empty; 0/0/0; resolved SAME in `tomioka-hachimangu-identity-resolution.md` (PR #2613) — `NORMALIZED_MATCH` address + `SHADOW_PATTERN_MATCH = STRONG` |
| 102 | テスト確認神社 20260611 | QA fixture | — | matched by `exclude_qa_fixture_shrines` (`name_jp LIKE 'テスト%'`); address `東京テスト`; no coordinates |
| 105 | 広島市 | `NON_SHRINE_ARTIFACT` | — | a city, not a shrine; `place_ref = ChIJu0_z7giZWjURcvfBz1DO5Ac`; **not** removed by `exclude_qa_fixture_shrines` (name convention only) → the tooling denominator (107) still counts it |

## Mechanical consistency (Phase 9)

| Check | Result |
|---|---|
| canonical rows in matrix | **103**, each `primary_shrine_id` exactly once (ids 1–100, 106, 107, 108) |
| excluded ids 101 / 102 / 103 / 104 / 105 as independent units | **absent** from the matrix |
| shadow → primary traceability | 21 ↔ 103 · 22 ↔ 101 · 49 ↔ 104 — all present above |
| `RAW_PRODUCTION_SHRINE_ROWS` | 108 [prod] |
| `Shrine` id space | 1–108 contiguous (`MAX(id) = 108`, `COUNT(DISTINCT id) = 108`) |
| duplicate `name_jp` across all rows | only {49,104}, {22,101}, {21,103} — all shadows in the excluded set; **0** duplicate names among the canonical 103 |
| Production `GoriyakuTag` | **39 rows, ids 1–39, names exact** to the canonical master (`recommendation-evidence-review-contract.md` §5) — `ALIGNED` re-verified this session |
| every `NEED_TO_GORIYAKU_IDS` value id | ∈ 1–39, resolves to the expected canonical Production name |
| every `goriyaku_tags` M2M link | → a canonical id 1–39 (no non-canonical tag ids anywhere) |
| `exclude_qa_fixture_shrines(Shrine.objects.all())` count | **107** (removes only id 102) → `KNOWLEDGE_COVERAGE_TOOL_DENOMINATOR_MISMATCH` vs the canonical 103 (difference = ids 105 + 101 + 103 + 104) |
