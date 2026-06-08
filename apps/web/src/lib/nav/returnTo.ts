import { sanitizeNext } from "@/lib/nav/login";

type SearchParamsLike = Record<string, string | string[] | undefined>;

function stripRscParamFromInternalPath(value: string): string {
  if (!value.startsWith("/")) return value;

  try {
    const url = new URL(value, "http://dummy");
    url.searchParams.delete("_rsc");
    return url.pathname + url.search;
  } catch {
    return value;
  }
}

export function normalizeReturnToParam(
  searchParams?: SearchParamsLike | Promise<SearchParamsLike>,
): Promise<string | null> | string | null {
  const resolve = async () => {
    const sp = (await searchParams) ?? {};
    const raw = sp["returnTo"];
    const first = Array.isArray(raw) ? raw[0] : raw;

    if (typeof first !== "string") return null;

    const cleaned = stripRscParamFromInternalPath(first);
    return sanitizeNext(cleaned);
  };

  return resolve();
}
