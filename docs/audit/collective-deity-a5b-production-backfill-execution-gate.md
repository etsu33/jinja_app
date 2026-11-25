# A-5b Production Backfill Execution Gate

- Status: **P0 CONTRACT FREEZE — PARTIAL / STOP BEFORE PRODUCTION**
- Date: 2026-09-27
- Scope: A-5b Pattern B production backfill execution
- Upstream closure: `docs/audit/collective-deity-a5b-pattern-b-verification-closure.md`
- Seed: `backend/temples/data/knowledge_seeds/a5b_collective_pattern_b_seed.json`
- Production write: **NOT AUTHORIZED / NOT EXECUTED**

## 1. Purpose

This contract defines the production execution boundary after the A-5b Pattern B isolated verification closure. It does not treat the isolated scratch state as evidence of current Production state. Production must pass its own read-only preflight before any write can be authorized.

The canonical write path remains `import_shrine_knowledge`; manual SQL, ad-hoc ORM writes, partial repair, and reinterpretation or expansion of the frozen candidate universe are outside this Gate.

## 2. Frozen repository identity

P0 was assembled from the merged `develop` branch.

```text
develop HEAD = f6664e67208add51da143e9018f2611f5b4d74bc
merge commit = docs(audit): close A-5b Pattern B isolated verification (#3023)
seed Git blob SHA = 2d6a919431f5c02f726c6e1ca0e6a0dd4f5df447
closure Git blob SHA = a122835eb1895bcb9e09d5780865554640a53941
repository migration head used by upstream closure = temples.0118_shrine_deity_collective_count_relation_constraint
```

The cryptographic SHA-256 of the Seed file must be freshly calculated from the exact `develop` checkout before P0 can become PASS. The Git blob SHA above is an immutable repository identity but is not substituted for the precedent's SHA-256 integrity check.

## 3. Frozen Pattern B payload

### Sources — 6 canonical identities

1. `batch9-hakone-official` — `https://hakonejinja.or.jp/hakone/`
2. `batch10-samukawa-deities` — `https://samukawajinjya.jp/about/main-deities.html`
3. `batch12-futarasan-official` — `http://www.futarasan.jp/`
4. `batch12-sumiyoshi-hakata-official` — `https://www.nihondaiichisumiyoshigu.jp/about/`
5. `batch12-awa-official` — `http://awajinjya.org/gosaijin.htm`
6. `batch14-oji-official` — `http://ojijinja.tokyo.jp/goyuisho/index.html`

### Collective identities — 6

1. 箱根神社 — 箱根大神
2. 寒川神社 — 寒川大明神
3. 二荒山神社 — 二荒山大神
4. 住吉神社（博多） — 住吉五所大神
5. 安房神社 — 忌部五部神
6. 王子神社 — 王子大神

### Membership identities — 23

- 箱根大神: 瓊瓊杵尊 / 木花咲耶姫命 / 彦火火出見尊
- 寒川大明神: 寒川比古命 / 寒川比女命
- 二荒山大神: 大己貴命 / 田心姫命 / 味耜高彦根命
- 住吉五所大神: 底筒男神 / 中筒男神 / 表筒男神 / 天照皇大神 / 神功皇后
- 忌部五部神: 櫛明玉命 / 天日鷲命 / 彦狭知命 / 手置帆負命 / 天目一箇命
- 王子大神: 伊邪那岐命 / 伊邪那美命 / 天照大御神 / 速玉之男命 / 事解之男命

Frozen cardinality:

```text
Source = 6
Collective = 6
Membership = 23
```

No additional candidate may be inferred or added inside this execution Gate.

## 4. Upstream isolated evidence

The merged upstream closure records:

```text
A5B_PREREQUISITE_GATE = PASS
A5B_ISOLATED_DRY_RUN_GATE = PASS
A5B_ISOLATED_APPLY_GATE = PASS
A5B_POST_IMPORT_INTEGRITY_GATE = PASS
A5B_SECOND_RUN_IDEMPOTENCY_GATE = PASS
A5B_PATTERN_B_VERIFICATION_CLOSURE = CLOSED
```

Its verified initial isolated plan was:

```text
source_REUSE_EXISTING = 6
collective_CREATE = 6
membership_CREATE = 23
```

Its second-run plan was:

```text
source_REUSE_EXISTING = 6
collective_SKIP_EXISTS = 6
membership_SKIP_EXISTS = 23
CREATE = 0
```

These values are evidence for the isolated repository-derived state only. They are not Production observations.

## 5. Expected Production plan

If and only if Production read-only preflight proves that all six canonical Sources and all 23 ShrineDeity prerequisites exist exactly as required, while all six target Collective identities and all 23 target Membership identities are absent, the expected Production `--dry-run` plan is:

```text
source_REUSE_EXISTING = 6
collective_CREATE = 6
membership_CREATE = 23
```

This is an **expected plan**, not a statement of current Production state.

Any different action or count is a STOP condition until the difference is explained and a new Mother Ship decision is recorded.

## 6. Production execution phases

```text
P0  Contract freeze
P1  Production environment / migration parity
P2  Production read-only pre-state
P3  Source prerequisite 6/6
P4  ShrineDeity prerequisite 23/23
P5  Collective / Membership collision audit
P6  Production validate-only
P7  Production dry-run
P8  Exact plan comparison
P9  Fresh backup / recovery readiness
P10 Human Execution Boundary
---- STOP / explicit Mother Ship approval ----
P11 Production write exactly once
P12 Post-import integrity
P13 Second-run dry-run idempotency
P14 Production Closure
```

## 7. P0 completion requirements

P0 is PASS only when all of the following are fixed against the same repository state:

- [x] merged `develop` HEAD
- [x] Seed path
- [x] Seed Git blob identity
- [ ] Seed SHA-256 freshly calculated from exact `develop` content
- [x] upstream Closure identity
- [x] migration head recorded by upstream Closure
- [x] Source identities 6
- [x] Collective identities 6
- [x] Membership identities 23
- [x] expected Production plan explicitly classified as expectation, not observation
- [x] STOP conditions
- [x] prohibited operations
- [x] Human Execution Boundary

Until the Seed SHA-256 item is filled and verified, status remains:

```text
A5B_PRODUCTION_P0_CONTRACT_FREEZE = PARTIAL
PRODUCTION_PREFLIGHT = NOT_STARTED
PRODUCTION_WRITE = NOT_AUTHORIZED
```

## 8. Mandatory STOP conditions

STOP immediately if any of the following is true:

- local/runner repository identity does not match the frozen `develop` identity used for the Gate;
- Seed SHA-256 is missing or changes after freeze;
- Production migration state is behind, divergent from, or otherwise incompatible with the required collective schema;
- any of the six Shrine identities is ambiguous or absent;
- canonical Source prerequisite count is not exactly 6/6;
- ShrineDeity prerequisite count is not exactly 23/23;
- a Source resolves semantically to a conflicting Production row;
- any target Collective or Membership has an unexpected pre-existing or duplicate state;
- `--validate-only` reports any error;
- Production `--dry-run` differs from the plan justified by measured Production pre-state;
- backup/recovery readiness is not established under the applicable Production precedent;
- any unexpected CREATE / UPDATE / DELETE / conflict / ambiguity is observed;
- explicit Mother Ship approval has not been given after all read-only Gates pass.

A STOP is not permission to repair Production inside this Gate. Drift must be classified first.

## 9. Prohibited operations before Human Execution Boundary

Before P10 PASS and explicit Mother Ship approval, do not perform:

- Production import in apply mode;
- manual Production SQL writes;
- manual ORM writes;
- partial backfill or repair;
- deletion or mutation of existing Source / ShrineDeity / Collective / Membership rows;
- candidate-universe expansion;
- evidence reinterpretation;
- ranking, recommendation, UI, or unrelated data changes;
- a second real Production import.

Read-only inspection, `--validate-only`, and `--dry-run` are permitted only in their defined phases after preceding Gates pass.

## 10. Production write boundary

Passing isolated verification does not authorize Production write.

Passing P1-P9 does not itself perform Production write.

After P1-P9 are all PASS, P10 must explicitly stop and present the measured Production plan and remaining risks to Mother Ship. Only an explicit approval after that STOP may authorize P11.

If authorized, P11 is one invocation of the canonical importer in apply mode for the frozen Seed. A second real import is prohibited; post-write idempotency is checked with read-only `--dry-run`.

## 11. Current classification

```text
A5B_PATTERN_B_ISOLATED_VERIFICATION = PASS
A5B_PATTERN_B_VERIFICATION_CLOSURE = CLOSED
A5B_PRODUCTION_P0_CONTRACT_FREEZE = PARTIAL
A5B_PRODUCTION_P1 = NOT_STARTED
PRODUCTION_WRITE = NOT_AUTHORIZED
```

Next action: calculate and record the Seed SHA-256 from the exact frozen `develop` content. Do not connect to Production before P0 becomes PASS.
