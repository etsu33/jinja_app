// apps/web/src/lib/analytics/urlSanitizer.ts
//
// PostHog へ送る URL 系 property から、許可していない query parameter を除く。
//
// 背景：posthog-js は全イベントの `$current_url` にクエリ込みの URL を入れ、
// identify 後は `$set_once`（`$initial_current_url` など）にも最初の URL を入れる。
// `/shrines?q=<検索語>` のような URL がそのまま送られると、検索語を
// 「イベント名を問わず送信しない」という計測ルール（docs/analytics/direction-events.md、
// consultation-history-events.md）に反する。
//
// 方式は許可リスト：`utm_*` だけを残し、それ以外の parameter はすべて除く。
// 新しい parameter が増えても、明示的に許可しない限り送られない。
import type { BeforeSendFn, CaptureResult, Properties } from "posthog-js";

/** query parameter を除く対象の property 名。`properties` / `$set` / `$set_once` の全部に適用する。 */
export const URL_PROPERTY_KEYS = ["$current_url", "$initial_current_url", "$referrer"] as const;

const ALLOWED_QUERY_PARAM_PREFIX = "utm_";

export function isAllowedQueryParam(name: string): boolean {
  return name.startsWith(ALLOWED_QUERY_PARAM_PREFIX);
}

function filterQueryString(query: string): string {
  const kept = new URLSearchParams();
  new URLSearchParams(query).forEach((value, name) => {
    if (isAllowedQueryParam(name)) kept.append(name, value);
  });
  const serialized = kept.toString();
  return serialized ? `?${serialized}` : "";
}

/**
 * URL から `utm_*` 以外の query parameter を除く。
 *
 * - 文字列でない値、`?` を含まない値（`$direct` など）はそのまま返す
 * - 絶対 URL として読めない値も、`?` から `#`（無ければ末尾）までを同じ規則で絞る
 */
export function stripDisallowedQueryParams(value: string): string {
  const queryStart = value.indexOf("?");
  if (queryStart === -1) return value;

  const hashStart = value.indexOf("#");
  // `#` が `?` より前にあるなら、`?` はフラグメントの一部で query ではない。
  if (hashStart !== -1 && hashStart < queryStart) return value;

  const queryEnd = hashStart === -1 ? value.length : hashStart;
  const query = value.slice(queryStart + 1, queryEnd);

  return `${value.slice(0, queryStart)}${filterQueryString(query)}${value.slice(queryEnd)}`;
}

/** property の集合のうち URL_PROPERTY_KEYS の値だけを絞った、新しいオブジェクトを返す。 */
export function sanitizeUrlProperties<T extends Properties | undefined>(properties: T): T {
  if (!properties) return properties;

  let next: Properties | null = null;
  for (const key of URL_PROPERTY_KEYS) {
    const value = properties[key];
    if (typeof value !== "string") continue;

    const sanitized = stripDisallowedQueryParams(value);
    if (sanitized === value) continue;

    next ??= { ...properties };
    next[key] = sanitized;
  }

  return (next ?? properties) as T;
}

/**
 * posthog-js の `before_send` に渡す関数。
 *
 * `properties` 直下に加えて、`$set` / `$set_once`（トップレベルと `properties` 内の両方）も絞る。
 * イベント自体は落とさない。
 */
export const sanitizeCaptureResult: BeforeSendFn = (captureResult: CaptureResult | null) => {
  if (!captureResult) return captureResult;

  const properties = sanitizeUrlProperties(captureResult.properties);
  const nestedSet = properties?.$set as Properties | undefined;
  const nestedSetOnce = properties?.$set_once as Properties | undefined;

  return {
    ...captureResult,
    properties: {
      ...properties,
      ...(nestedSet ? { $set: sanitizeUrlProperties(nestedSet) } : {}),
      ...(nestedSetOnce ? { $set_once: sanitizeUrlProperties(nestedSetOnce) } : {}),
    },
    ...(captureResult.$set ? { $set: sanitizeUrlProperties(captureResult.$set) } : {}),
    ...(captureResult.$set_once ? { $set_once: sanitizeUrlProperties(captureResult.$set_once) } : {}),
  };
};
