# W0-DB04 Source Packet Freeze

## Status

- Batch: `W0-DB04`
- Recorded at: `2026-10-03`
- Base: `develop@d031c019d3928ce1e9abad94236f6c4d57d2f9e5`（PR #3070 merged）
- Original batch membership: 5 shrines
- G4 eligible subset: 3 shrines（wave0-019 / wave0-021 / wave0-025）
- Excluded: wave0-020（G2 HOLD）、wave0-022（G3 HOLD）
- Source Packet Freeze: `PASS_3_OF_3`（Mother Ship frozen decision）
- G4 Knowledge Fact + Evidence: **NOT EXECUTED**
- Production write: `NONE`
- Candidate Master write: `NONE`
- Base Seed write: `NONE`
- Knowledge Seed write: `NONE`
- goriyaku_tags: **NOT FROZEN**（本Packetの対象外）

本書はMother Shipが本実行環境の外で確定したG4 Source Packetの記録である。
本実行環境はSource本文へ到達しておらず、値を再導出・補完・正規化していない。

本書はProduction importを許可しない。G4 Knowledge Fact + Evidenceを実行しない。
G5以降を実行しない。

## Governing contracts

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/knowledge/shrine-position-contract.md`
- `docs/audit/model-risk-release-contract.md`
- `docs/audit/shrine-expansion-wave0-db04-unified-gate-preflight.md`（G1〜G3 正本）
- Precedent: `docs/audit/shrine-expansion-wave0-db03-source-packet-freeze.md`

## Mother Ship decision boundary

```text
Original W0-DB04 membership = KEEP 5
G4 eligible subset          = wave0-019 / wave0-021 / wave0-025
Position hold               = wave0-020 水堂須佐男神社   (owning Gate G2, HOLD_POSITION_REVIEW)
Model hold                  = wave0-022 毛谷黒龍神社     (owning Gate G3, MODEL_REVIEW_REMAINS)
Replacement                 = NONE
Renumbering                 = NONE
```

wave0-020 / wave0-022 は本Packetの対象外であり、昇格させない。lifecycle statusも変更しない。

---

# 1. 建勲神社（wave0-019）

## Source Packet result

```text
PASS / FROZEN / G4_EVIDENCE_READY
```

## Canonical identity / Fact owner

```text
candidate_id   = wave0-019
fact_owner     = 建勲神社 本社
```

G1 PASSは `shrine-expansion-wave0-db04-unified-gate-preflight.md` に記録済み。
`official_address` は本Packetへ供給されていない（§Field gaps）。

## Position

G2の採用値は `shrine-expansion-wave0-db04-unified-gate-preflight.md` §G2 を正本とする。

```text
position_status = PASS
latitude        = 35.0386537
longitude       = 135.7431512
```

Position `verified_at` はKnowledge Factの `verified_at` に流用しない。

## Knowledge Facts

### Deity

1.

```text
display_name  = 織田信長公
source_role   = 主祭神
model_role    = primary
```

2.

```text
display_name  = 織田信忠卿
source_role   = 配祀
model_role    = enshrined
```

Deity boundary:

- anonymous collective = NONE
- sub-shrine contamination = NONE
- 義照稲荷神社、命婦元宮、船岡妙見社その他の摂末社・関連境内対象の祭神を、本社の祭神集合へ取り込まない。

### History

| # | 年 | 内容 |
|---|---|---|
| 1 | 1869 | 明治天皇による神社創立の宣下 |
| 2 | 1870 | 神号「建勲」の宣下 |
| 3 | 1875 | 別格官幣社に列格、船岡山に社地 |
| 4 | 1880 | 社殿造営、織田信忠卿を配祀 |
| 5 | 1910 | 山麓から山上の現在地へ本殿以下諸舎を移建 |

History boundary:

```text
founding                                   = 1869
relocation to current mountain-top location = 1910
```

- 創立・造営・移建を1つのeventへ統合しない。
- 神社資料に記載があっても、織田信長の一般的な伝記をShrineHistoryとして取り込まない。

## goriyaku evidence

```text
evidence_type = DIRECT_OFFICIAL_GOSHINTOKU_WORDING
```

Frozen official wording:

```text
国家安泰 / 万民安堵 / 大願成就 / 開運 / 難局突破 / 産業指導 / 災難除け
```

本PacketはKAMIMUSUBI goriyaku_tagsへmappingしない。Source wordingとRecommendation taxonomyは別である。

---

# 2. 大阪天満宮（wave0-021）

## Source Packet result

```text
PASS / FROZEN / G4_EVIDENCE_READY
```

## Canonical identity / Fact owner

```text
candidate_id      = wave0-021
fact_owner        = 大阪天満宮 本社
official_address  = 大阪市北区天神橋2丁目1番8号
```

`official_address` は `shrine-expansion-wave0-db04-unified-gate-preflight.md` §G2 に
official identity / address corroboration（大阪天満宮公式）として記録済みの値である。

## Position

G2の採用値は preflight §G2 を正本とする。

```text
position_status = PASS
latitude        = 34.6958917
longitude       = 135.5126472
```

Position `verified_at` はKnowledge Factの `verified_at` に流用しない。

## Knowledge Facts

### Deity

```text
display_name  = 菅原道真公
model_role    = primary
```

Deity boundary:

- 大将軍社は本社の祭神ではない。
- anonymous collective = NONE

### History

| # | 年 | 内容 | semantic boundary |
|---|---|---|---|
| 1 | 650 | 大将軍社がこの地に祀られる | prehistory / regional context |
| 2 | 901 | 菅原道真公が太宰府へ向かう途中、大将軍社に参拝 | historical event |
| 3 | 949 | 村上天皇の勅命により社を建立し、菅原道真公の御霊を祀る | founding / official origin |

Critical boundary:

```text
founding boundary = 949
```

- 650を大阪天満宮の創建年として記録しない。
- 大将軍社の前史と大阪天満宮を区別して保持する。

## goriyaku evidence

```text
evidence_type = OFFICIAL_PRAYER_SUPPORTED / OFFICIAL_CURRENT_GUIDANCE_SUPPORTED
```

Frozen supported wording（includes）:

```text
試験合格 / 学業成就 / 厄除け / 交通安全 / 商売繁昌 / 就職成就 / 学徳向上
```

- これらは祈祷・現行案内のevidenceである。直接の公式ご神徳wordingとして書き換えない。
- 本PacketはKAMIMUSUBI goriyaku_tagsへmappingしない。

---

# 3. 大崎八幡宮（wave0-025）

## Source Packet result

```text
PASS / FROZEN / G4_EVIDENCE_READY
```

## Canonical identity / Fact owner

```text
candidate_id      = wave0-025
fact_owner        = 大崎八幡宮
official_address  = 宮城県仙台市青葉区八幡4-6-1
```

Identity boundary:

- 大崎市岩出山に所在する、同名・類似名の別の神社entityと混同しない。

## Position

G2の採用値は preflight §G2 を正本とする。

```text
position_status = PASS
latitude        = 38.2725678
longitude       = 140.8449622
```

Position `verified_at` はKnowledge Factの `verified_at` に流用しない。

## Knowledge Facts

### Deity

```text
応神天皇
仲哀天皇
神功皇后
```

Frozen model interpretation:

```text
3柱とも、現行Modelで primary として表現してよい。
```

Deity boundary:

- anonymous collective = NONE

### History

Sourceの構造を保持し、1つの任意の創建年へ平坦化しない。

Frozen semantic structure:

| # | 要素 |
|---|---|
| 1 | より古い起源・系譜の文脈（older origin / lineage context） |
| 2 | 現社が表す系譜への統合（consolidation into the lineage represented by the current shrine） |
| 3 | 仙台開府後の、仙台の現在地での造営（construction at the current Sendai location） |
| 4 | 1607-08-12: 遷座祭 |

Critical boundary:

- 1607を、元となる信仰・歴史の起源として扱わない。
- Frozen Source Packetが支持しない単一の創建年を作らない。
- 要素1〜3の年代・本文は本Packetへ供給されていない。推測で補わない（§Field gaps）。

## goriyaku evidence

```text
evidence_type = OFFICIAL_PRAYER_SUPPORTED
```

Frozen supported wording:

```text
家内安全 / 商売繁昌 / 交通安全 / 厄除 / 方除 / 学業成就 / 合格祈願 / 必勝 /
身体堅固 / 病気平癒 / 開運厄除 / 災難招福 / 心願成就 / 良縁 / 安産 / 旅行安全
```

- 直接のご神徳wordingへ変換しない。
- 本PacketはKAMIMUSUBI goriyaku_tagsへmappingしない。

---

# Cross-candidate freeze rules

```text
1. Source Packet Freeze            = 3 / 3 PASS
     wave0-019 PASS
     wave0-021 PASS
     wave0-025 PASS
2. Deity ownership consistency     = PASS
3. History semantic boundary       = PASS
4. goriyaku evidence typing        = PASS
5. anonymous collective Model Risk = NONE (3 / 3)
```

6. Evidence typeの区別を保持する:

```text
DIRECT_OFFICIAL_GOSHINTOKU_WORDING
!= OFFICIAL_PRAYER_SUPPORTED
!= OFFICIAL_CURRENT_GUIDANCE_SUPPORTED
!= KAMIMUSUBI recommendation taxonomy
```

7. goriyaku_tagsは本Source Packetでfreezeしない。
8. G2 Positionの `verified_at` をKnowledge Factの `verified_at` に流用しない:

```text
Position verification
!= Deity Fact verification
!= History Fact verification
!= goriyaku evidence verification
```

9. Fact `verified_at` をG2 timestamp・git timestamp・`accessed_at`・過去audit日付から作らない。
10. Source URLはrepository evidenceまたはMother Ship verified source recordにある値だけを使う。
    推測・再構成・検索結果による代替をしない。

---

# Field gaps（本Packetで記録しなかった値）

以下はW0-DB03 precedent / current contractsが要求またはG4で必要となる値だが、
本Packetへ供給されていないため記録しない。推測で補わない。

| Field | 対象 | 要求元 | 状態 |
|---|---|---|---|
| Knowledge Fact `verified_at`（Deity / History） | 019 / 021 / 025 | W0-DB03 precedent（Canonical identityの `verified_at`）、Knowledge Contract「accessed_atとverified_at」（内容確認日を独立記録） | **NOT SUPPLIED — STOP for this field** |
| Fact `verification_status` / `confidence` | 019 / 021 / 025 | W0-DB03 precedent（各Factに記録）、Knowledge Contract「verification_status候補」「Fact利用条件」 | **NOT SUPPLIED — STOP for this field** |
| Factごとの正確なSource URL（`official_source_url`、Deity / History / goriyaku の各Primary Source） | 019 / 021 / 025 | W0-DB03 precedent（Canonical identity / Primary Sources）、Knowledge Contract「出典必須条件」 | **NOT SUPPLIED — STOP for this field** |
| `official_address` | 019 | W0-DB03 precedent（Canonical identity） | NOT SUPPLIED |
| History要素1〜3の年代・本文 | 025 | Knowledge Contract「創建情報」「歴史的出来事」 | NOT SUPPLIED（Mother Shipは構造のみをfreeze） |
| `history_type` の割当（1869=founding、949=founding 以外） | 019 / 021 / 025 | Knowledge Contract「分類案」 | NOT SUPPLIED（semantic boundaryのみ記録） |

Repository内に記録済みのURL（2026-09-09 Wave0 availability audits）は次の通り。
いずれもSource availabilityの記録であり、どのFactを支えるかは本Packetで確定していない。
Fact Sourceとしてbindしない。

```text
wave0-019  https://kenkun-jinja.org/
           https://kenkun-jinja.org/history/
wave0-021  https://osakatemmangu.or.jp/
           https://osakatemmangu.or.jp/gokito
wave0-025  https://miyagi-jinjacho.or.jp/jinja-search/detail.php?code=310010033
           https://www.oosaki-hachiman.or.jp/guidance/
```

---

# Batch Freeze Summary

| Shrine | Identity | Adopted Position | Deity Facts | History items | goriyaku evidence type | goriyaku_tags | Source Packet |
|---|---|---|---|---|---|---|---|
| 建勲神社 | PASS | PASS | 2 | 5 | DIRECT_OFFICIAL_GOSHINTOKU_WORDING（7語） | NOT FROZEN | PASS |
| 大阪天満宮 | PASS | PASS | 1 | 3 | OFFICIAL_PRAYER_SUPPORTED / OFFICIAL_CURRENT_GUIDANCE_SUPPORTED（7語） | NOT FROZEN | PASS |
| 大崎八幡宮 | PASS | PASS | 3 | 4（構造） | OFFICIAL_PRAYER_SUPPORTED（16語） | NOT FROZEN | PASS |

```text
W0_DB04_SOURCE_PACKET_FREEZE = PASS_3_OF_3
G4_ELIGIBLE_SUBSET           = wave0-019 / 021 / 025
WAVE0_020                    = EXCLUDED_AT_G2_HOLD_POSITION_REVIEW
WAVE0_022                    = EXCLUDED_AT_G3_MODEL_REVIEW_REMAINS
G4_KNOWLEDGE_FACT_EVIDENCE   = NOT EXECUTED
PRODUCTION_WRITE             = NONE
```

## G4 handoff boundary

- G4 Knowledge Fact + Evidenceは本書では実行していない。
- §Field gapsの値（Fact `verified_at`、`verification_status` / `confidence`、Factごとの正確なSource URL）は
  Knowledge Seed作成に必要である。供給されるまで、G4でこれらの値を推測・補完しない。
- wave0-020 / wave0-022 を変更しない。
- G4着手時に本Packetとcurrent canonical contractsが矛盾した場合はSTOPする。

## Files / Data Changed

```text
Production DB                                  NONE
backend/temples/data/shrines_seed_clean.json   NONE
Knowledge Seed                                 NONE
Candidate Master JSON                          NONE
Model Risk Resolution Record                   NONE
goriyaku taxonomy / mapping                    NONE
Model / Migration / Serializer / Runtime       NONE
Recommendation / Ranking / Concierge / Compass NONE
A-5b records                                   NONE
```

変更は本Audit文書の新規作成のみ。
