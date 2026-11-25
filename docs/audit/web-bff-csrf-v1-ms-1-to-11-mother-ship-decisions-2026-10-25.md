# CSRF V-1 — Mother Ship MS-1〜MS-11 design decisions (2026-10-25)

## Authority and scope

Mother Ship explicitly selected **MS-1=B, MS-2=B, MS-3=C, MS-4=A, MS-5=A, MS-6=A, MS-7=A, MS-8=A, MS-9=A, MS-10=A, MS-11=A** in the review following #3337. **DESIGN DECISIONS ONLY.** The owner also reported partial understanding and explicitly requested cautious security handling; do not treat these decisions as acceptance of unspecified details or implementation risk.

This record interprets the choice letters **exclusively according to the option definitions at** [#3337 decision matrix](web-bff-csrf-v1-ms-rv-ud-decision-and-validation-plan-2026-10-25.md). It does not approve A-0 Runtime implementation, L4-O Production observation, L4-E enforcement, Rollback/Promote, deployments, env changes, logging configuration changes, controlled request probes, or any measured rehearsal. **A-0 / L4-O / L4-E = NOT APPROVED.**

Existing choices **U-5=B (verified-deployment restoration design)** and **EU-8=A (read-only recovery-readiness only)** remain separate. MS-2=B **does not supersede EU-8=A** and does not authorize a surrogate rehearsal.

## Selected design intent and unresolved parameters

| ID | Selected | Design intent (not an implementation instruction) | Evidence/parameters still required |
| --- | --- | --- | --- |
| MS-1 | B | Document both verified deployment restoration and `rollback by revert` with explicit conditions | Precedence, Hobby eligibility, immutable restore target, applicability to V-1 vs pre-V-1, conflict reconciliation with RV-11, O-5/O-6 if CSRF control weakens |
| MS-2 | B | Isolated non-Production surrogate results may serve as **supplemental** evidence | Equivalence limits, acceptance thresholds, scope & separate execution approval; read-only results alone do not satisfy RV-10/P-13 |
| MS-3 | C | Config change + redeploy is a **conditionally gated** possible recovery path | EU-3/EU-4, explicit approval path, fallback & stop conditions; neither procedure nor invocation authorized |
| MS-4 | A | Separate fixed schema for allowed/blocked security events and explicit production emission policy | Exact allowlisted fields, levels, PII redaction, integration with existing logger which suppresses production `info`; storage belongs to MS-8 |
| MS-5 | A | Would-be 415 reason code: `content_type_would_reject_415` | Verify name against canonical contract and tests before implementation |
| MS-6 | A | Count inbound requests at BFF handler entry; not UI actions; never deduplicate by untrusted request ID | Define handler boundaries, request retries and count/test invariants |
| MS-7 | A | Classify QA by server-verifiable internal properties | Exact trusted signal/authentication and spoofing tests; client assertion alone cannot mark QA |
| MS-8 | A | Durable server-side aggregation respecting CSRF rejection/Django separation | Actual datastore/provider, consistency and retry model, no unauthorized exception to #3323 §5, budget/privacy review |
| MS-9 | A | Explicit retention/access policy linked to observation and review lifecycle | **Days not selected**; reviewer roles, deletion schedule, storage limitations and incident requirements remain open |
| MS-10 | A | Normalized evidence export with SHA-256 and audit review reference | Canonical encoding, hashing inputs, signing/provenance, reviewers, reproducibility |
| MS-11 | A | **No Log Drains in the present phase** | Reassessment requires separate approval; avoid IP/UA exposure and verify permissible alternative evidence storage |

## Compatibility audit and unresolved safety gates

- MS-1=B is a **contract-reconciliation obligation**, not a silent change to prior `rollback by revert` language or an execution approval. RV-11 stays OPEN until the controlling recovery contract is explicitly amended and reviewed.
- MS-2=B allows **only optional supplemental evidence in principle**. EU-8=A stays selected; no rehearsal, duration measurement or Production traffic switch authorized. RV-9, RV-10 and P-13 remain BLOCKED/OPEN.
- MS-3=C is **not approval** to redeploy/configure. EU-3/EU-4 and RV-4/RV-5 remain OPEN.
- MS-4=A and MS-8=A are **separate**: log field/level contract vs aggregation system of record. No new log output, external sink or Django backend call approved.
- MS-9=A fixes policy direction, **not a numeric retention period**. EU-5 and UD-4/5 remain unresolved.
- MS-10=A chooses integrity strategy, **not evidence authenticity on its own**. MS-11=A forbids introducing log drains in this phase; it does not justify losing required audit evidence.
- **RV-1〜RV-11 and UD-1〜UD-11 are still unresolved**, subject to implementation and direct evidence. Prior EU read-only facts remain partial and time-dependent.
- **A-0 / L4-O / L4-E remain NOT APPROVED**; no runtime, Production, deploy, env, logging or restore action is part of this PR.

## Human-readable meaning

1. If security accidentally blocks legitimate users, we must have a reversible, explicitly limited recovery procedure; options MS-1 to MS-3 choose design direction, not safe restore capability.
2. We must be able to explain what got allowed, blocked and counted without trusting attacker-controlled labels or leaking personal information; MS-4 to MS-7 define the recording semantics.
3. We must be able to retain, check and inspect security evidence securely; MS-8 to MS-11 select an approach, not yet a built or verified system.

## Next review gates

1. Separate docs-only PR(s) to reconcile the canonical recovery contract (MS-1/2/3) and detail log/evidence acceptance criteria (MS-4〜11). Do **not** infer missing configuration values or retention duration from option letters.
2. Evidence matrix review against canonical RV/UD acceptance criteria with tests and measurable STOP conditions.
3. Explicit separate Mother Ship authorization before any A-0, L4-O, L4-E, test traffic, rehear­sal, rollback/promote, production deploy or environment change.

**Record state: 11/11 Mother Ship design choices captured; technical parameters and RV/UD evidence remain OPEN; runtime/production authorization remains NOT APPROVED.**
