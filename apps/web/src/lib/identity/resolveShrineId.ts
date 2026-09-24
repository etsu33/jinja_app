// apps/web/src/lib/identity/resolveShrineId.ts
//
// Shared frontend Shrine identity resolver (F-4 implementation of the
// F-3 / F-3.1 contract).
//
//   SHRINE_IDENTITY_AUTHORITY = Shrine.id
//   PUBLIC_IDENTITY_KEY       = shrine_id
//
// Contract records:
//   docs/audit/shared-shrine-identity-resolver-design.md  (F-3, F-3.1, F-4)
//   docs/audit/shrine-identity-compass-concierge-contract.md
//
// This module is the single identity-resolution implementation for the Web
// app. Consumers must not re-implement normalization, alias precedence, or
// conflict handling locally.
//
// Deliberately NOT accepted as Shrine identity by either policy:
//   generic `id`  -- COMPATIBILITY_FIELD, never identity authority (R-2 / F-1)
//   place_id / placeId / place.id -- shadow identity, F-6 scope
//   name / address / coordinates / anchors -- never identity
//
// Never throws.

/** Identity policy. There is no default -- every call states its policy. */
export type ShrineIdentityPolicy = "public_strict" | "registered_compat";

/**
 * F-3.1: resolution status is preserved, never collapsed into `null`.
 *
 * Callers with a non-identity fallback (e.g. the Concierge `place_id` ->
 * /shrines/resolve path) MUST branch on `status`, because "no identity was
 * asserted" (`absent`) and "an identity was asserted but is unusable"
 * (`invalid` / `conflict`) require opposite behavior.
 */
export type ShrineIdentityResolution =
  | { status: "resolved"; shrineId: number }
  | { status: "absent"; shrineId: null }
  | { status: "invalid"; shrineId: null }
  | { status: "conflict"; shrineId: null };

const ABSENT: ShrineIdentityResolution = { status: "absent", shrineId: null };
const INVALID: ShrineIdentityResolution = { status: "invalid", shrineId: null };
const CONFLICT: ShrineIdentityResolution = { status: "conflict", shrineId: null };

/** Allowed identity field paths per policy, in declaration order. */
const PUBLIC_STRICT_PATHS: readonly (readonly string[])[] = [["shrine_id"]];
const REGISTERED_COMPAT_PATHS: readonly (readonly string[])[] = [["shrine_id"], ["shrineId"], ["shrine", "id"]];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function readPath(input: unknown, path: readonly string[]): unknown {
  let current: unknown = input;
  for (const key of path) {
    if (!isRecord(current)) return undefined;
    current = current[key];
  }
  return current;
}

/**
 * Normalizes one allowed identity value to a positive integer Shrine PK.
 *
 * ACCEPT: 42, "42"
 * REJECT: 0, negatives, floats, blank/non-numeric strings, NaN, +/-Infinity,
 *         boolean, null, undefined, everything else.
 *
 * `boolean` is rejected explicitly and first: `Number(true) === 1` would
 * otherwise silently turn `true` into Shrine 1. The backend identity reader
 * guards the same case (concierge_chat_candidates._candidate_shrine_id).
 */
function normalizeShrineIdValue(value: unknown): number | null {
  if (typeof value === "boolean") return null;

  if (typeof value === "number") {
    return Number.isSafeInteger(value) && value > 0 ? value : null;
  }

  if (typeof value === "string") {
    const trimmed = value.trim();
    // Digits only: rejects "", "abc", "1.5", "-1", "+1", "1e3", "0x2a",
    // "NaN", "Infinity" without relying on Number()'s coercion quirks.
    if (!/^\d+$/.test(trimmed)) return null;
    const parsed = Number(trimmed);
    return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : null;
  }

  return null;
}

function allowedPathsFor(policy: ShrineIdentityPolicy): readonly (readonly string[])[] | null {
  switch (policy) {
    case "public_strict":
      return PUBLIC_STRICT_PATHS;
    case "registered_compat":
      return REGISTERED_COMPAT_PATHS;
    default:
      return null;
  }
}

/**
 * Authoritative resolver (F-3.1).
 *
 * Status contract:
 *   absent   -- no policy-allowed identity field is present
 *   invalid  -- a policy-allowed identity field is present but unusable
 *   conflict -- two or more allowed aliases normalize to different IDs
 *   resolved -- at least one allowed field is present and all agree
 *
 * Presence rule: a field is "present" when it exists with a value that is
 * neither `undefined` nor `null`. `shrine_id: null` is therefore `absent`,
 * not `invalid` -- the backend emits exactly that for unregistered,
 * place_id-only candidates (concierge_candidate_normalize.normalize_candidate
 * blanks `shrine_id` to `None`), and those must keep their place_id path.
 *
 * Status precedence: absent -> invalid -> conflict -> resolved. `invalid` is
 * evaluated before `conflict`/`resolved`, so a garbage alias next to a good
 * one fails closed rather than being silently dropped.
 */
export function resolveShrineIdentity(input: unknown, policy: ShrineIdentityPolicy): ShrineIdentityResolution {
  const paths = allowedPathsFor(policy);
  // Unknown policy: fail closed rather than silently widening to `absent`,
  // which would re-enable a caller's non-identity fallback.
  if (paths === null) return INVALID;

  if (!isRecord(input)) return ABSENT;

  let presentCount = 0;
  let sawUnusable = false;
  const normalized = new Set<number>();

  for (const path of paths) {
    const raw = readPath(input, path);
    if (raw === undefined || raw === null) continue;

    presentCount += 1;
    const value = normalizeShrineIdValue(raw);
    if (value === null) {
      sawUnusable = true;
      continue;
    }
    normalized.add(value);
  }

  if (presentCount === 0) return ABSENT;
  if (sawUnusable) return INVALID;
  if (normalized.size > 1) return CONFLICT;

  const [only] = normalized;
  return { status: "resolved", shrineId: only };
}

/**
 * Convenience wrapper. Delegates to `resolveShrineIdentity` -- there is
 * exactly ONE identity-resolution implementation.
 *
 * Callers that have a non-identity fallback (place_id, history matching)
 * must use `resolveShrineIdentity` instead, so they can distinguish
 * `absent` from `invalid` / `conflict`.
 */
export function resolveShrineId(input: unknown, policy: ShrineIdentityPolicy): number | null {
  return resolveShrineIdentity(input, policy).shrineId;
}
