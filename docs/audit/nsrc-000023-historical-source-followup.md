# nsrc-000023 熱串彦神社 — Historical Source Follow-up (read-only)

## 1. Status / boundaries

- Recorded at: 2026-10-21
- Base: `develop@d132d8d00ebc15111bd038ce2a50b836beb3e898` (PR #3289 merged)
- Candidate: `nsrc-000023` / 熱串彦神社 / 新潟県佐渡市長江854番地
- Prior authority: `docs/audit/nsrc-000023-advancement-readiness.md`, `docs/audit/niigata-vpg001-g3-source-knowledge-fit.md` §6 / §6.1, `docs/knowledge/shrine-expansion-gate-contract.md` §6–7

```text
MOTHER_SHIP_A_TO_E_DECISION       = NOT_RECORDED
TECHNICAL_RECOMMENDATION         = A (retain HOLD / continue research; NOT an approval)
G3                               = HOLD / RESEARCH_REQUIRED_BEFORE_RELEASE (unchanged)
G3_RELEASE_CONDITION_1           = NOT_MET
G3_RELEASE_CONDITION_2           = NOT_MET
G3_REEVALUATION                 = NOT_AUTHORIZED_BY_CURRENT_EVIDENCE
PRODUCT_SURFACE                  = NOT_YET_APPLICABLE
G4                               = NOT_AUTHORIZED
HISTORICAL_SOURCE_RESEARCH       = PARTIAL (secondary transcription read; original page images not verified)
STOP                             = TRUE (no state or production write)
```

This is an evidence follow-up, **not** the Mother's Ship decision. No gate, lifecycle, Product Surface, model or production state changes are authorized.

## 2. New web review (2026-10-21): what was actually accessible

- Shrine-heritager, 熱串彦神社（佐渡市長江）: https://shrineheritager.com/atsukushihiko-shrine/ . Accessible as a **third-party transcription / excerpt / interpretive rendering**, not the original work. It attributes entries to (a) an onsite hall notice; (b) `佐渡神社誌` (1926); (c) `明治神社誌料` (1912); and (d) `特選神名牒` (1925 published edition). The reproduced readings are not independently verified against scans.
- たんぽぽろぐ, 熱串彦神社: https://momijiaoi.net/atsukushihiko/ . Accessible as an independent **third-party summary**, not a verified current shrine-issued deity record. It acknowledges the `佐渡神社誌` / `特選神名牒` difference.
- Kotobank, 熱串彦神社: https://kotobank.jp/word/%E7%86%B1%E4%B8%B2%E5%BD%A6%E7%A5%9E%E7%A4%BE-2002483 . Page body was accessible in web review and presents competing names attributed to two reference works. This is reference-work evidence, not confirmed current-principal-deity documentation.

### Primary/original access limit

- `佐渡神社誌`, NDL Digital Collections: https://dl.ndl.go.jp/pid/971197 — original viewer/page images **not accessible** through the available web tool in this session.
- `特選神名牒`, NDL Digital Collections: https://dl.ndl.go.jp/pid/1919019 — the catalog/landing page was accessible, but original scanned pages **were not inspected**.
- The above URLs establish leads and editions only. **No original-page collation is claimed.** Neither the page numbers nor precise image locations of the relevant passages were independently established.
- Consequently `PRIMARY_ORIGINAL_TEXT_VERIFIED = NO`. Quoted transcriptions cannot be silently promoted to `PRIMARY_PAGE_VERIFIED`.

## 3. Comparative evidence matrix

| Historical witness (as attributed in third-party reproduction) | Principal-deity wording / distinction | Reliability status for this audit |
| --- | --- | --- |
| Hall 由緒 notice reproduced by Shrine-heritager | 阿田都久志尼命 as main; separately 大彦命 as 合祀, 金山彦命 as 配祀 | **SECONDARY_TRANSCRIPTION_ONLY**; current onsite notice not visited or verified |
| `佐渡神社誌` (1926) reproduction | 阿田都久志尼命 as 祭神; 金山彦命 as 合祀 | **SECONDARY_TRANSCRIPTION_ONLY**; original scan not checked |
| `明治神社誌料` (1912) reproduction | 阿由都久志尼命 as 祭神; 金山彦命 as 合祀 | **SECONDARY_TRANSCRIPTION_ONLY**; original scan not checked |
| `特選神名牒` (1925 ed.) reproduction | 阿都久志比古命 preferred; explicitly challenges the name in the historical 明細帳 | **SECONDARY_TRANSCRIPTION_ONLY**; original scan not checked |
| 精選版日本国語大辞典 at Kotobank | 阿都久志比古命 | **REFERENCE_PAGE_VISIBLE**; does not establish current shrine practice |
| 日本歴史地名大系 at Kotobank | 阿田都久志比尼命; ancestry of 加茂氏 mentioned | **REFERENCE_PAGE_VISIBLE**; does not establish current shrine practice |
| Tourism `加茂氏の祖神` / 金山彦命 配祀 per prior G3 record | Descriptive ancestor role / accompanying deity, not a proper-name resolution | **PRIOR_SEARCH_SUMMARY**; no promotion to accepted G3 Source |

**Important:** These forms are not normalized or merged. Differences include 阿都 / 阿田都 / 阿由都, 比古 / 比尼 / 尼, and 合祀 / 配祀 / 主祭神. Editorial explanations, historical usage and current shrine practice must be kept separate. A third-party attribution of a hall notice is not direct verification of the present notice.

## 4. Acceptance / G3 re-entry evaluation

1. **Alternative 1** (accepted Source establishes the current principal deity's proper name): `NOT_MET`. Secondary reproductions and historical reference works identify names worth investigating, but they do not independently establish the currently accepted principal deity, and the original scans/onsite notice were not reviewed.
2. **Alternative 2** (meaning-preserving representation under existing contract): `NOT_MET`. No new approved model representation or contract ruling exists. A descriptor-only Deity row, 金山彦命 alone, a guessed equivalence, or a History-only bypass remains prohibited.
3. **G3 re-evaluation now:** no gate-changing re-evaluation justified; retain `RESEARCH_REQUIRED_BEFORE_RELEASE`. Do not treat new historical leads as new accepted/current Source.
4. **Candidate Master / production:** maintain `DISCOVERED`, `UNREVIEWED`, `G4 NOT_AUTHORIZED`. No changes to source data, migrations, fixtures, Seed, Recommendation, Ranking, or earlier audits.

## 5. Mother Ship options (UNSELECTED)

- **A:** retain HOLD and investigate original scans and a direct current shrine-issued source. **Technical recommendation only; not a recorded decision.**
- **B:** accept a specifically identified and directly verified current-deity Source, then re-evaluate G3. The present evidence does not qualify.
- **C:** separately authorize a model-risk review for a descriptor-only current principal deity. No such authorization exists.
- **D:** separately evaluate `CATALOG_ONLY` and its evidence contract, without inventing deity Facts.
- **E:** defer.

```text
MOTHER_SHIP_DECISION = NOT_RECORDED
NEXT_GATE            = NONE_AUTHORIZED
```

## 6. Follow-up evidence needed

- Inspect exact NDL scanned pages for `佐渡神社誌` and `特選神名牒`; record edition, volume, page/image location, retrieval date, and direct extract. Distinguish original characters from modernized transcription.
- Obtain and date-check the current onsite 由緒 notice or a shrine/神社庁-issued principal-deity listing; identify explicit 主祭神 and 配祀/合祀 roles.
- Compare the historical witnesses without inferring identity across names. Escalate any historical/current discrepancy to Mother Ship; no automatic promotion.
- Once accepted current-state evidence or a separately approved contract-compliant representation is available, propose a fresh G3 evaluation in a separate PR.

## 7. Change boundary and STOP

```text
CHANGED_FILES                    = THIS_DOCUMENT_ONLY
G1_G2_G3_HISTORICAL_RECORDS      = UNCHANGED
CANDIDATE_MASTER                 = UNCHANGED
FIXTURES_SEEDS_DB_PRODUCTION     = UNCHANGED
RECOMMENDATION_RANKING_RUNTIME   = UNCHANGED
G3_STATUS                       = HOLD
STOP                            = TRUE
```
