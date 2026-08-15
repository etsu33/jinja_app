"use client";

import { useState } from "react";

import { askDeepDive, type DeepDiveAnswer, type DeepDiveAskError } from "@/lib/api/deepDive";

type Props = {
  shrineId: number;
};

type ErrorKind = "validation" | "not_found" | "system";

const QUESTION_MAX_LENGTH = 2000;

// docs/product/deep-dive-answer-generation-contract.md §11 API Responsibility:
// Frontendはreadiness/question_type/Fact選択/Source選択/confidence/verificationの
// いずれも判断しない。ここではBackend response(DeepDiveAnswer)をそのまま表示するのみ。

function DeepDiveSourceList({ sources }: { sources: DeepDiveAnswer["sources_used"] }) {
  if (sources.length === 0) return null;

  return (
    <div className="mt-3">
      <p className="text-xs font-semibold text-[var(--kt-color-text-muted)]">出典</p>
      <ul className="mt-1 space-y-2">
        {sources.map((source) => (
          <li
            key={source.id}
            className="rounded-[var(--kt-radius-panel)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] p-2"
          >
            <p className="text-sm font-semibold text-[var(--kt-color-text-primary)] break-words">{source.title}</p>
            <p className="mt-0.5 text-xs text-[var(--kt-color-text-muted)] break-words">
              {[source.publisher, source.source_type].filter(Boolean).join(" ・ ")}
            </p>
            {source.url ? (
              <a
                href={source.url}
                target="_blank"
                rel="noreferrer noopener"
                className="mt-0.5 block break-all text-xs text-sky-700 underline"
              >
                {source.url}
              </a>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

function DeepDiveUnansweredAspects({ aspects }: { aspects: string[] }) {
  if (aspects.length === 0) return null;

  return (
    <p className="mt-2 text-xs leading-5 text-[var(--kt-color-text-muted)]">
      回答できなかった内容: {aspects.join(" / ")}
    </p>
  );
}

function DeepDiveResultView({ result }: { result: DeepDiveAnswer }) {
  if (result.readiness === "not_ready") {
    // Not Readyは正常なProduct State(Knowledge不足)。errorではないため、
    // 赤/枠付きにせず、控えめなslateテキストで理由を表示するのみ。
    return <p className="mt-3 text-xs leading-5 text-slate-400">{result.limitations}</p>;
  }

  return (
    <div className="mt-3 rounded-[var(--kt-radius-panel)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-3">
      <p className="whitespace-pre-wrap break-words text-sm leading-6 text-[var(--kt-color-text-primary)]">
        {result.answer}
      </p>

      {result.readiness === "limited" && result.limitations ? (
        <p className="mt-2 text-xs leading-5 text-slate-500">{result.limitations}</p>
      ) : null}

      <DeepDiveUnansweredAspects aspects={result.unanswered_aspects} />
      <DeepDiveSourceList sources={result.sources_used} />
    </div>
  );
}

const ERROR_MESSAGES: Record<ErrorKind, string> = {
  validation: "質問の内容を確認してください。",
  not_found: "神社情報を取得できませんでした。",
  system: "通信に失敗しました。時間をおいて再度お試しください。",
};

export function ShrineDeepDivePrompt({ shrineId }: Props) {
  const [question, setQuestion] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<DeepDiveAnswer | null>(null);
  const [errorKind, setErrorKind] = useState<ErrorKind | null>(null);

  const trimmedQuestion = question.trim();
  // 空質問はAPI自体は正常に処理できるが(unclassifiable -> unanswered応答)、
  // 不要なnetwork requestを避けるためFrontend側でのみ送信を止める
  // (Backend Authority変更ではない、UX上のvalidationのみ)。
  const canSubmit = trimmedQuestion.length > 0 && !submitting;

  async function handleSubmit() {
    if (!canSubmit) return;

    setSubmitting(true);
    setErrorKind(null);

    try {
      const response = await askDeepDive(shrineId, trimmedQuestion);
      setResult(response);
    } catch (err) {
      const status = (err as DeepDiveAskError)?.status;
      if (status === 400) {
        setErrorKind("validation");
      } else if (status === 404) {
        setErrorKind("not_found");
      } else {
        setErrorKind("system");
      }
      setResult(null);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="rounded-[var(--kt-radius-card)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-4">
      <h2 className="text-base font-semibold text-[var(--kt-color-text-primary)]">この神社について質問する</h2>
      <p className="mt-1 text-xs leading-5 text-[var(--kt-color-text-muted)]">
        確認できている情報の範囲でお答えします。
      </p>

      <input
        type="text"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        maxLength={QUESTION_MAX_LENGTH}
        placeholder="例：誰を祀っていますか？ / なぜ創建されたのですか？"
        className="mt-3 w-full rounded-[var(--kt-radius-panel)] border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] px-3 py-2 text-sm text-slate-800 outline-none placeholder:text-slate-400 focus:border-[var(--kt-color-border-focus)]"
      />

      <button
        type="button"
        disabled={!canSubmit}
        onClick={handleSubmit}
        className="mt-3 w-full rounded-2xl bg-[var(--kt-color-text-primary)] px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? "回答を生成中..." : "質問する"}
      </button>

      {errorKind ? <p className="mt-3 text-xs font-semibold text-rose-700">{ERROR_MESSAGES[errorKind]}</p> : null}

      {!errorKind && result ? <DeepDiveResultView result={result} /> : null}
    </section>
  );
}

export default ShrineDeepDivePrompt;
