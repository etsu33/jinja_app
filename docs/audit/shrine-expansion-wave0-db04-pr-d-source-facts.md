# W0-DB04 PR-D: Source Fact materialization

## Status

```text
PR_D_SOURCE_FACT_TOTAL = 23
OSAKA_TENMANGU         = 7   (wave0-021)
OSAKI_HACHIMANGU       = 16  (wave0-025)
SOURCE_RECORDS         = 3   (shrine_official, URL-backed identity)
SOURCE_LINKAGE_BLOCKED = NO
MAPPING_ACTIVATION     = NOT_IN_PR_D
PRE_G6_HOLD            = ACTIVE
```

- Seed: `backend/temples/data/knowledge_seeds/wave0_batch_04_source_facts_seed.json`（Knowledge Seed schema 1.2）
- Import: 既存の `import_shrine_knowledge`（PR-A の Source Fact contract。同じ stable_key + 差分なし = `SKIP_EXISTS`、差分あり = `SOURCE_FACT_CONFLICT`）
- Tests: `backend/temples/tests/test_wave0_db04_source_facts_seed.py`
- 既存の G4 Knowledge Seed（`wave0_batch_04_seed.json`、schema 1.0、Deity / History 18 Fact）は変更していない。

本書の値はすべて Mother Ship が凍結した入力である。本実行環境は Source 本文へ到達しておらず、値を再導出・補完していない。

## Sources

| key | publisher | title | url | source_type |
|---|---|---|---|---|
| `w0-db04-osaka-tenmangu-gokito-official` | 大阪天満宮 | ご祈祷・ご祈願 | https://osakatemmangu.or.jp/gokito | `shrine_official` |
| `w0-db04-osaka-tenmangu-r8-torinuke-official` | 大阪天満宮 | 令和8年の通り抜け参拝について | https://osakatemmangu.or.jp/3944 | `shrine_official` |
| `w0-db04-oosaki-hachiman-gokigan-official` | 大崎八幡宮 | 御祈願の神札 | https://www.oosaki-hachiman.or.jp/event/shinsyun/doc/ofuda.pdf | `shrine_official` |

3件とも `language = ja` / `source_confirmed` / `high` / `verified_at = 2026-10-05T00:00:00+09:00`。
`accessed_at` は凍結されていないため持たない（`verified_at` から作らない）。`bibliography` もなし。
Source identity は既存の `source_type + normalized URL`。title だけで別神社の Source と一致することはない。

大崎八幡宮の既存 Source（宮城県神社庁、`government`）は Deity / History 用であり、祈願の Source Fact には使っていない。

## Source Facts

stable_key（MS-1）: `{shrine_slug}__{fact_type}__{fact_slug}`。
全 23 件: `source_confirmed` / `high` / `verified_at = 2026-10-05T00:00:00+09:00`、Source relation 1件。

### 大阪天満宮（7、`official_prayer_and_current_guidance_list_level`）

| stable_key | wording | Source |
|---|---|---|
| `osaka_tenmangu__prayer_and_current_guidance__shiken_gokaku` | 試験合格 | gokito |
| `osaka_tenmangu__prayer_and_current_guidance__gakugyo_joju` | 学業成就 | gokito |
| `osaka_tenmangu__prayer_and_current_guidance__yakuyoke` | 厄除け | gokito |
| `osaka_tenmangu__prayer_and_current_guidance__kotsu_anzen` | 交通安全 | gokito |
| `osaka_tenmangu__prayer_and_current_guidance__shobai_hanjo` | 商売繁昌 | gokito |
| `osaka_tenmangu__prayer_and_current_guidance__shushoku_joju` | 就職成就 | r8-torinuke |
| `osaka_tenmangu__prayer_and_current_guidance__gakutoku_kojo` | 学徳向上 | r8-torinuke |

試験合格 は r8-torinuke Source にも記載があるが、PR-D の正規 binding は gokito Source のみとする（Mother Ship decision）。
characterization は term 単位で分けず、list 単位のまま保持する（格上げしない）。

### 大崎八幡宮（16、`official_prayer_supported`、Source: gokigan）

家内安全 / 商売繁昌 / 交通安全 / 厄除 / 方除 / 学業成就 / 合格祈願 / 必勝 /
身体堅固 / 病気平癒 / 開運厄除 / 災難招福 / 心願成就 / 良縁 / 安産 / 旅行安全

stable_key は `osaki_hachimangu__prayer__{kanai_anzen | shobai_hanjo | kotsu_anzen | yakuyoke | hoyoke | gakugyo_joju |
gokaku_kigan | hissho | shintai_kengo | byoki_heiyu | kaiun_yakuyoke | sainan_shofuku | shingan_joju | ryoen | anzan | ryoko_anzen}`。

## Boundary

PR-D は data のみである。次は変更していない。

- Source Fact Mapping Registry（23 件とも registry entry なし）/ EXACT / SAFE_NORMALIZATION / Need mapping
- `goriyaku_tags` / `ShrineGoriyakuAssignment` / GoriyakuTag
- Recommendation（Channel A / Channel B / scoring / candidate universe / reason / U1 / U2）/ G5 eligibility / Compass / LLM

registry entry がないため、23 件は Recommendation signal を作らない（Channel B の carrier は付かない）。
mapping の有効化は PR-E（MS-2 承認後）が担う。

対象外: wave0-019 建勲神社（DIRECT_OFFICIAL_GOSHINTOKU_WORDING、Channel A 側）/ wave0-020 / wave0-022（既存 gate のまま）。
