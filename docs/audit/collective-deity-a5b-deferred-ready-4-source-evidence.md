# A-5b DEFERRED_READY_4 — Existing Source Evidence Audit

- Status: **EVIDENCE INVENTORY RECORDED**
- Recorded at: 2026-10-01
- Audited commit: `origin/develop@98bbeaa9ffb5094545eacef85e92288a05dd68f6` (includes PR #3042)
- Scope: audit only, repository evidence only
- External research: **NONE**
- Seed / Source registry / DB / classification change: **NONE**

## 1. Authoritative candidate set

Source: `docs/audit/collective-deity-backfill-candidate-freeze.md` §5.2, §5.3, §10;
re-stated without change by `docs/audit/collective-deity-a5b-frozen-candidate-count-confirmation.md` §3.2.

| # | Shrine (name_jp / address) | Collective label | Pattern | Freeze-doc status | Initial-set status |
|---:|---|---|---|---|---|
| 1 | 富岡八幡宮 / 東京都江東区富岡1-20-3 | 応神天皇（誉田別命）外８柱 | C | BACKFILL_READY | DEFERRED_READY |
| 2 | 阿蘇神社 / 熊本県阿蘇市一の宮町宮地3083-1 | 健磐龍命をはじめ家族神12神 | C | BACKFILL_READY | DEFERRED_READY |
| 3 | 八坂神社 / 京都府京都市東山区祇園町北側625 | 八柱御子神 | A + D | BACKFILL_READY_COLLECTIVE_ONLY | DEFERRED_READY |
| 4 | 東京大神宮 / 東京都千代田区富士見2-4-1 | 造化の三神 | A | BACKFILL_READY_COLLECTIVE_ONLY | DEFERRED_READY |

```text
DEFERRED_READY count          4   (unchanged from PR #3042)
candidate identity            identical to PR #3042
artifact conflict             none (both documents list the same 4)
shrine block per name_jp      1 each in the Knowledge Seed corpus
```

Reason for deferral (freeze doc §10): the initial Data PR was limited to Pattern B
so it would not mix "Pattern C partial-membership or Pattern A/D collective-only
edge cases". `DEFERRED_READY` = "not selected for the initial Data PR" only.

Pattern definitions: `docs/audit/collective-deity-model-change-design.md` §6.2
(A = label stored as ShrineDeity; C = some named + unnamed remainder;
D = collective established, members not enumerated).

## 2. Source registry resolution

Each key is defined exactly once across the 15 Knowledge Seed files.

| source_key | Defined in | source_type | publisher | URL | verification | Registry gaps |
|---|---|---|---|---|---|---|
| batch13-tomioka-official | batch_13_seed.json | shrine_official | 富岡八幡宮 | http://www.tomiokahachimangu.or.jp/annai/goyuisho/goyuisho.html | source_confirmed / high | none |
| src-999035 | batch_1_7_seed.json | shrine_official | 阿蘇神社 | https://asojinja.or.jp/about/ | source_confirmed / high | `accessed_at` = null, `language` = "", `note` = "" |
| src-999044 | batch_1_7_seed.json | shrine_official | 八坂神社 | https://www.yasaka-jinja.or.jp/about/saijin.html | source_confirmed / high | `language` = ""; note does not mention the label |
| src-999050 | batch_1_7_seed.json | shrine_official | 東京大神宮 | https://www.tokyodaijingu.or.jp/syoukai/ | source_confirmed / high | `language` = ""; note does not mention the label |

```text
SOURCE_KEY_RESOLUTION = 4 / 4 PASS (single definition each)
```

No repository artifact stores the Source body text. All evidence below is the
quoted or paraphrased Source content recorded in seed `note` fields and earlier
audit documents.

## 3. Field-contract reference

From `docs/audit/collective-deity-knowledge-seed-v1-1-contract.md` §5.1–§5.2:

- `role`: `primary` / `enshrined` / `secondary` / `unknown` (default `unknown`)
- `member_count_relation`: `exact` / `minimum` / `approximate` / `unspecified` (default `unspecified`)
- `unspecified` requires `member_count = null`; any other relation requires a non-null count
- `note` "must not be parsed into Facts or Memberships"

## 4. Evidence matrix

### 4.1 富岡八幡宮 — 応神天皇（誉田別命）外８柱

| Field | Result | Repository evidence |
|---|---|---|
| shrine identity | 富岡八幡宮 / 東京都江東区富岡1-20-3 | batch_13_seed.json shrine_ref |
| collective label | 応神天皇（誉田別命）外８柱 | freeze doc §5.3 |
| current A-5b classification | BACKFILL_READY (Pattern C) / DEFERRED_READY | freeze doc §5.3, §10 |
| source_key | batch13-tomioka-official | — |
| source resolves | PASS | batch_13_seed.json `sources` |
| source authority | shrine_official, source_confirmed, high | same |
| collective label supported | **SUPPORTED** | Source note quotes 「御祭神 応神天皇（誉田別命）外８柱」; also `knowledge-batch13-seed-preflight.md` L17, L73, L97 |
| members supported | **PARTIAL** | 1 named member (応神天皇, ShrineDeity row, same source_key). Source note: "他8柱の個別名は明かしていない" |
| role supported | **PARTIAL** | Expression appears under heading 「御祭神」. No recorded statement of the Collective's rank. Member row 応神天皇 has role `primary` |
| member_count_relation supported | **PARTIAL** | "外８柱" (8 unnamed) is recorded. Freeze doc §5.3 records remainder = 8 and says the relation "must still be verified from the frozen Source packet" |
| unresolved ambiguity | (a) whether `member_count` is the total or the remainder (the freeze doc records only remainder 8); (b) the recorded quote includes the 「御祭神 」 prefix, which the freeze-doc label omits | freeze doc §5.3; Source note |
| missing evidence | Collective role; the count/relation semantics | — |

### 4.2 阿蘇神社 — 健磐龍命をはじめ家族神12神

| Field | Result | Repository evidence |
|---|---|---|
| shrine identity | 阿蘇神社 / 熊本県阿蘇市一の宮町宮地3083-1 | batch_1_7_seed.json shrine_ref |
| collective label | 健磐龍命をはじめ家族神12神 | freeze doc §5.3 |
| current A-5b classification | BACKFILL_READY (Pattern C) / DEFERRED_READY | freeze doc §5.3, §10 |
| source_key | src-999035 | — |
| source resolves | PASS | batch_1_7_seed.json `sources` |
| source authority | shrine_official, source_confirmed, high (`accessed_at` null, `note` empty) | same |
| collective label supported | **PARTIAL** | Only in the Deity note on 健磐龍命: 公式サイトは「健磐龍命をはじめ家族神12神を祀る」. The Source record carries no note. The freeze-doc label is that quote with 「を祀る」 removed |
| members supported | **PARTIAL** | 1 named member (健磐龍命, ShrineDeity row, same source_key). Deity note: the other 11 names were not confirmed |
| role supported | **UNSUPPORTED** | Deity note explicitly records: "他11柱の個別名・祭神としての位置づけは公式Sourceで確認できなかった" |
| member_count_relation supported | **PARTIAL** | Count 12 is recorded. Repository treats 健磐龍命 as one of the 12 ("他11柱": Deity note; `collective-deity-contract-stress.md` §D "残り11柱"). No relation value is recorded. Freeze doc §5.3 defers it to Source verification |
| unresolved ambiguity | (a) label boundary (quote vs. truncated label); (b) the Source's own position of the other 11 is recorded as unconfirmed | Deity note; freeze doc §5.3 |
| missing evidence | Source-level record of the expression (Source note is empty); Collective role; relation value; `accessed_at` | — |

### 4.3 八坂神社 — 八柱御子神

| Field | Result | Repository evidence |
|---|---|---|
| shrine identity | 八坂神社 / 京都府京都市東山区祇園町北側625 | batch_1_7_seed.json shrine_ref |
| collective label | 八柱御子神 | freeze doc §5.2 |
| current A-5b classification | BACKFILL_READY_COLLECTIVE_ONLY (Pattern A + D) / DEFERRED_READY | freeze doc §5.2, §10 |
| source_key | src-999044 | — |
| source resolves | PASS | batch_1_7_seed.json `sources` |
| source authority | shrine_official, source_confirmed, high | same |
| collective label supported | **SUPPORTED** | Existing ShrineDeity row `display_name` = 八柱御子神, source_keys [src-999044], source_confirmed/high; `shrine-knowledge-batch4-prep.md` L95 |
| members supported | **UNSUPPORTED** | Deity note: "公式サイトが個別列挙せず一括して呼称する". No named member. The freeze doc fixes Memberships = [] (§5.2) |
| role supported | **PARTIAL** | Legacy ShrineDeity row role = `enshrined` (same source_key). No Source text on rank is stored, and no contract states whether the legacy row's role carries over to the Collective |
| member_count_relation supported | **PARTIAL** | Count 8 is recorded (Deity note "8柱の総称"; `shrine-knowledge-rollout-batch-4.md` L103). No relation value is recorded |
| unresolved ambiguity | role transfer from the legacy row is not covered by any contract | — |
| missing evidence | Source-level record of the expression (the src-999044 note does not mention it); relation value | — |

### 4.4 東京大神宮 — 造化の三神

| Field | Result | Repository evidence |
|---|---|---|
| shrine identity | 東京大神宮 / 東京都千代田区富士見2-4-1 | batch_1_7_seed.json shrine_ref |
| collective label | 造化の三神 | freeze doc §5.2 |
| current A-5b classification | BACKFILL_READY_COLLECTIVE_ONLY (Pattern A) / DEFERRED_READY | freeze doc §5.2, §10 |
| source_key | src-999050 | — |
| source resolves | PASS | batch_1_7_seed.json `sources` |
| source authority | shrine_official, source_confirmed, high | same |
| collective label supported | **SUPPORTED** | Existing ShrineDeity row `display_name` = 造化の三神, source_keys [src-999050], source_confirmed/high; `shrine-evidence-integrity-full-audit.md` L145 (MATCH) |
| members supported | **PARTIAL** | Deity note names 天之御中主神・高御産巣日神・神産巣日神. None of these exists as a ShrineDeity row for this Shrine. The v1.1 `note` must not be parsed into Memberships, and freeze doc §5.2 forbids creating the rows (Memberships = []) |
| role supported | **PARTIAL** | Legacy ShrineDeity row role = `enshrined` (same source_key). Same contract gap as 4.3 |
| member_count_relation supported | **PARTIAL** | Three names are recorded in the Deity note and `shrine-knowledge-batch-5-source-availability.md` L124. No count or relation value is recorded as a field |
| unresolved ambiguity | role transfer from the legacy row is not covered by any contract | — |
| missing evidence | Source-level record of the expression (the src-999050 note does not mention it); relation value | — |

## 5. Summary

| Candidate | label | members | role | count relation |
|---|---|---|---|---|
| 富岡八幡宮 | SUPPORTED | PARTIAL | PARTIAL | PARTIAL |
| 阿蘇神社 | PARTIAL | PARTIAL | UNSUPPORTED | PARTIAL |
| 八坂神社 | SUPPORTED | UNSUPPORTED | PARTIAL | PARTIAL |
| 東京大神宮 | SUPPORTED | PARTIAL | PARTIAL | PARTIAL |

For "members", PARTIAL / UNSUPPORTED describes evidence coverage only. For 八坂神社
and 東京大神宮 the freeze doc already fixes Memberships = [], and Pattern C keeps
the unnamed remainder unnamed.

## 6. Evidence gaps

1. **`member_count_relation`: no candidate has a recorded relation value.** All four
   have only a count phrase in notes or labels.
2. **`role`: no candidate has a Source statement of the Collective's rank.**
   阿蘇神社 records explicitly that the position could not be confirmed.
3. **Label boundary**: for 阿蘇神社 and 富岡八幡宮, the freeze-doc label is a
   substring of the recorded quote.
4. **Source-level text**: for src-999035, src-999044 and src-999050, the Source
   record's own note does not record the collective expression. It appears only
   in Deity notes.
5. **Registry metadata**: src-999035 has `accessed_at` = null.

## 7. Will the next phase need new external research?

Repository evidence alone cannot support non-default values for `role` or
`member_count_relation` for any of the four candidates.

The v1.1 contract allows defaults (`role = unknown`,
`member_count_relation = unspecified` with `member_count = null`). A-5b contract
§6.1 condition 5 accepts "a contract-defined default". So the next phase needs one
Mother Ship decision:

- **(a) Use contract defaults** for unsupported fields. No external research is
  needed for those fields. Gaps 3 (label boundary) and 4 (Source-level text)
  still need adjudication.
- **(b) Author non-default `role` / `member_count_relation`**. This requires new
  external Source verification for all four candidates.

This audit does not choose between them.

## 8. Mutation record

```text
Production / development DB write = 0
Seed / Source registry change      = 0
Candidate classification change    = 0
External research                  = 0
```
