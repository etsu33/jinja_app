# SEC-B02 Bootstrap Exit-Status Compatibility Audit（2026-11-03）

> **Status: Audit / Historical（read-only audit + tests; PR #3429 follow-up）**
>
> - Target: PR #3429 branch `fix/security-remove-hardcoded-credentials` @ `136267c`（base `develop` @ `f9cf35c4`）.
> - Question: PR #3429 changes the "user already exists" outcome of both bootstrap paths from a normal exit to an
>   error exit. Who calls these paths, and what breaks?
> - No Production connection, no credential retrieval, no account change and no history rewrite. Local disposable
>   PostgreSQL only, with synthetic credentials（`.invalid` addresses）.
> - Values of the credentials removed by PR #3429 are **not** reproduced here. They remain in git history and need
>   rotation（SEC-E01）.

## 0. Verdict

- **No tracked caller exists, and none ever existed.** This holds across the whole history of `develop`（4,486
  commits）. The exit-status change breaks nothing that the repository runs.
- External callers are **UNKNOWN**: Render one-off jobs, a Render shell, or manual procedures kept outside the
  repository. The owner must confirm these.
- **One compatibility finding（C-1）:** after PR #3429, `manage.py shell < create_user_once.py` exits 0 and silently
  does nothing. It is fail-closed（nothing is created）, but it looks like success.

## 1. Behaviour change

| Path | Case | Before PR #3429（from code; the old scripts were not executed） | After PR #3429（tested） |
| --- | --- | --- | --- |
| `create_initial_user`（management command） | User exists | Prints "initial user already exists", exit 0 | `CommandError("bootstrap_user_already_exists")`, **exit 1**; user unchanged |
| | No explicit flag | Not applicable（ran unconditionally with fixed credentials） | `explicit_bootstrap_authorization_required`, exit 1 |
| | Credentials missing | Not applicable | `bootstrap_credentials_missing`, exit 1 |
| | Success | Regular user with fixed credentials | Regular user（not a superuser）from environment variables |
| `create_user_once.py` | User exists | Prints "User already exists", exit 0 | `RuntimeError("bootstrap_user_already_exists")`; user unchanged |
| | No explicit flag | Not applicable | `explicit_bootstrap_authorization_required` |
| | Credentials missing | Not applicable | `bootstrap_credentials_missing` |
| | Success | **Superuser** with fixed credentials | **Superuser** from environment variables; prints only `bootstrap_user_created` |

The explicit flags are separate: `KAMIMUSUBI_BOOTSTRAP_SUPERUSER=1` for `create_user_once.py` and
`KAMIMUSUBI_BOOTSTRAP_INITIAL_USER=1` for the command. Only the exact value `1` is accepted, and the command's flag
does not authorize the superuser path（tested）.

## 2. Caller audit

**Method**

1. `git grep` over every tracked file for `create_user_once`, `create_initial_user` and `KAMIMUSUBI_BOOTSTRAP`.
2. `git grep` over the executable configuration for indirect paths（`manage.py shell`, `shell <`,
   `createsuperuser`, `create_superuser`, `create_user`）:
   - shell scripts, YAML（including `.github/`）, Makefile and `mk/`, Dockerfiles, Procfile, TOML, JSON, `bin/`;
   - `docker-manage.sh`.
3. The clone was shallow（96 commits）, so the full history was fetched read-only（`git fetch --unshallow`; no
   rewrite）. `git log -S` was then run for both names over all 4,486 commits.

**Result**

| Item | Finding |
| --- | --- |
| References outside the two scripts and their tests | Only `docs/audit/security-follow-up-backlog.md:59`（backlog text） |
| Startup / deploy | `backend/start.sh` calls neither script. Its only `manage.py shell` heredoc（line 153）repairs the `ShrineReflection` table. `bootstrap_production_data` creates no user. `scripts/deploy.sh`, `scripts/django.sh`, `docker-manage.sh` and `bin/dev` do not call them |
| CI（`.github/`）, Makefile, Dockerfiles | No reference |
| History | Both names occur in exactly three commits: `94a23291`（2025-12-10, scripts added）, `3b57b92b`（2025-12-10, #439）and `692ff715`（2026-08-06, backlog document）. **No script, workflow or configuration file has ever referenced them** |
| External / operational | **UNKNOWN**: Render dashboard one-off commands, a Render shell, or local runbooks outside the repository. To confirm with the owner, without exposing values |

## 3. Invocation paths（measured on a local disposable database after PR #3429）

| Path | Result | Evidence |
| --- | --- | --- |
| (a) `python backend/create_user_once.py` | Exit 1, `ImproperlyConfigured`（the script never configures Django）. No regression: the old script called `get_user_model()` at import, which fails the same way（inferred from code） | Executed; test `test_standalone_script_without_django_settings_exits_non_zero_without_leaking` |
| (b) `python manage.py shell < create_user_once.py` | **Exit 0, nothing created, nothing printed（C-1）.** Django 5.2 executes the input with the shell module's globals, so `__name__` is not `"__main__"` and the guard never calls `create_user_once()`. The old script ran at module level on this path and created the user（inferred from code） | Executed（exit 0; output limited to the auto-import notice）; characterization test `test_characterization_piping_the_file_into_shell_creates_nothing` |
| (c) `manage.py shell -c` importing the module and calling `create_user_once()` | Works and creates a superuser. An existing user raises `RuntimeError`, so the command fails | Tests `test_shell_command_import_and_call_is_the_working_path` and `test_shell_command_existing_user_raises_so_manage_py_exits_non_zero`. The process exit code of `manage.py shell` with an uncaught exception was **not measured**（inferred: non-zero） |
| (d) `python manage.py create_initial_user` | User exists → exit 1. Missing flag → exit 1 | Test via `BaseCommand.run_from_argv`（`SystemExit(1)`）: `test_initial_user_command_existing_user_exits_with_status_1` |

## 4. Findings

| ID | Severity（proposed） | Finding | Recommendation（not done here） |
| --- | --- | --- | --- |
| C-1 | Low（fail-closed; operational confusion） | `manage.py shell < create_user_once.py` exits 0 and silently does nothing | One of the following, for Mother Ship to choose: (1) make that path fail loudly; (2) convert the script into a management command; (3) remove `create_user_once.py`. Option (3) is plausible because it duplicates `create_initial_user` with superuser rights |
| C-2 | Info | `create_user_once.py` has no supported invocation documented in the repository. Path (c) is the only one that works | Document the supported command, or remove the script, together with C-1 |
| C-3 | Info（compatibility） | Any external procedure that relied on "already exists → exit 0"（for example a retried deploy hook）will now fail | The owner confirms that no such hook exists（§2 External） |

Existing users are never modified on any path. That covers password, email, superuser / staff / active flags and
last login. It is tested for a regular user（no privilege escalation）and for an existing superuser.

## 5. Tests（`backend/tests/test_create_user_once_security.py`, 27 tests）

- **Authorization:** a missing or non-exact flag（`""`, `"0"`, `"true"`, `"yes"`, `" 1"`, `"1 "`, `"01"`）is refused.
  The command's flag does not authorize the superuser path.
- **Credentials:** a missing or blank username, email or password is refused, and no user is created.
- **Existing user:** refused, and every field is unchanged. A second run after a success keeps the first user.
- **Success:** the user is a superuser and staff, the password is stored hashed, and stdout is exactly
  `bootstrap_user_created`, with no credentials.
- **Invocation and exit status:** paths (a) to (d) in §3.
- **Mutation**（temporary in-place edits, restored and verified identical to `136267c`）: all seven mutants were
  detected.

| Mutant | Detection |
| --- | --- |
| Authorization check removed | 9 failed |
| Authorization accepts any truthy value | 6 failed |
| Only the password is required | 5 failed |
| An existing user is updated and escalated | 4 failed |
| An existing user exits normally（old behaviour） | 4 failed |
| A regular user is created instead of a superuser | 3 failed |
| Credentials are printed | 1 failed |

## 6. Residual risks

1. **The removed credentials stay in git history.** Whether a matching account exists in Production, and its
   rotation or deactivation, are owner operations（SEC-E01）. Nothing in this PR changes that.
2. **External callers are UNKNOWN**（§2）.
3. C-1 and C-2 are recorded, not fixed.
4. The old behaviour is inferred from code. The old scripts were deliberately not executed, because they contain the
   committed credentials.
