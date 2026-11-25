// docs/product/deep-dive-answer-generation-contract.md / POST /api/deep-dive/ask/
//
// Backend Authority契約: readiness/question_type/facts_used/sources_used/
// limitations/unanswered_aspectsはすべてBackendが確定した値をそのまま扱う。
// このクライアントは型を付けてBFF routeを呼ぶだけで、値の再解釈・再判定は行わない。

export type DeepDiveReadiness = "full" | "limited" | "not_ready";

export type DeepDiveFactUsed = {
  type: string;
  id: number;
  label: string;
};

export type DeepDiveSourceUsed = {
  id: number;
  title: string;
  publisher: string;
  source_type: string;
  url: string;
};

export type DeepDiveAnswer = {
  answer: string;
  readiness: DeepDiveReadiness;
  question_type: string[];
  facts_used: DeepDiveFactUsed[];
  sources_used: DeepDiveSourceUsed[];
  limitations: string | null;
  unanswered_aspects: string[];
};

export type DeepDiveAskError = Error & {
  status?: number;
  body?: unknown;
};

export async function askDeepDive(shrineId: number | string, question: string): Promise<DeepDiveAnswer> {
  const res = await fetch("/api/deep-dive/ask/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ shrine_id: Number(shrineId), question }),
  });

  const contentType = res.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await res.json() : null;

  if (!res.ok) {
    const error = new Error("deep_dive_ask_failed") as DeepDiveAskError;
    error.status = res.status;
    error.body = body;
    throw error;
  }

  return body as DeepDiveAnswer;
}
