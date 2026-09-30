# A6-00b Collective Runtime Activation Seed Workflow

- Status: IMPLEMENTED (PR) / Production apply NOT EXECUTED
- Date: 2026-09-30
- Foundation: `CollectiveRuntimeActivation` (A6-00, #3035; migrations `0119` / NoGIS `0018`)
- Seed: `backend/temples/data/runtime_rollout/a6_collective_runtime_activation_v1.json`
- Command: `backend/temples/management/commands/activate_collective_runtime.py`
- Service: `backend/temples/services/collective_runtime_activation_seed.py`

## 1. Semantics

```text
CollectiveRuntimeActivation row exists = explicitly approved runtime rollout candidate
row absent                             = not runtime activated
Activation                             = necessary, NOT sufficient, for runtime admission
```

Runtime admission checks (Collective evidence, `member_list_status`, Membership
count / evidence, deity resolution, same-Shrine integrity) belong to A6-01 and are
not implemented here. Pattern B is backfill history only; no pattern is inferred
or stored.

## 2. Activation seed

The seed is derived one-to-one from the A-5b seed
(`backend/temples/data/knowledge_seeds/a5b_collective_pattern_b_seed.json`);
`shrine_ref` and `source_attested_label` values are identical.

| # | shrine_ref.name_jp | shrine_ref.address | source_attested_label |
|---|---|---|---|
| 1 | 箱根神社 | 神奈川県足柄下郡箱根町元箱根80-1 | 箱根大神 |
| 2 | 寒川神社 | 神奈川県高座郡寒川町宮山3916 | 寒川大明神 |
| 3 | 二荒山神社 | 栃木県日光市山内2307 | 二荒山大神 |
| 4 | 住吉神社（博多） | 福岡県福岡市博多区住吉3-1-51 | 住吉五所大神 |
| 5 | 安房神社 | 千葉県館山市大神宮589 | 忌部五部神 |
| 6 | 王子神社 | 東京都北区王子本町1-1-12 | 王子大神 |

`shrine_ref` is a portable deployment reference used only during activation
import. After activation, runtime relies on the `CollectiveRuntimeActivation.collective` FK.

## 3. Resolution

```text
shrine_ref -> knowledge_seed.resolve_shrine()               (existing Knowledge import helper)
           -> knowledge_seed.find_collectives_by_identity() (resolved Shrine + exact label)
           -> CollectiveRuntimeActivation.collective FK
```

- Shrine: `OK` / `OK_CANONICAL_PREFERRED` accepted (same contract as `import_shrine_knowledge`); `NOT_FOUND` / `AMBIGUOUS` abort.
- Collective: exactly 1 match required; 0 = `COLLECTIVE_NOT_FOUND`, >1 = `COLLECTIVE_AMBIGUOUS`.
- Two seed entries resolving to the same Collective = `IDENTITY_CONFLICT`.

## 4. Command

```text
python manage.py activate_collective_runtime <seed.json> --validate-only
python manage.py activate_collective_runtime <seed.json> --dry-run
python manage.py activate_collective_runtime <seed.json>
```

| Mode | Behavior | DB writes |
|---|---|---|
| `--validate-only` | JSON / schema / structure / duplicate checks + Shrine and Collective resolution | none |
| `--dry-run` | above + exact `CREATE` / `SKIP_EXISTS` plan | none |
| apply | re-resolve and plan inside one `transaction.atomic()`; create `CREATE` rows only | Activation rows only |

Any error in any mode aborts the entire run with a non-zero exit. Partial activation is not possible.

## 5. Expected Production-equivalent results

```text
initial dry-run   CREATE=6 SKIP_EXISTS=0
first apply       created=6, skipped=0
second apply      created=0, skipped=6
later dry-run     CREATE=0 SKIP_EXISTS=6
```

These are verified in `backend/temples/tests/test_collective_runtime_activation_seed.py`
against a fixture built by importing the repository A-5b seed with the existing
`import_shrine_knowledge` command (no Production primary keys used).

## 6. Production execution boundary

This PR performs no Production write. Production activation is a separate
Mother Ship-controlled step after merge, following the A-5b sequence:
backup, `--validate-only`, `--dry-run` (expect `CREATE=6 SKIP_EXISTS=0`), apply,
post-apply verification (6 activation rows), and a second `--dry-run`
(expect `CREATE=0 SKIP_EXISTS=6`).
