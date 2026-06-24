"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { ChangeEvent, FormEvent } from "react";

import { getGoriyakuTags } from "@/lib/api/tags";
import { isApiError } from "@/lib/api/errors";
import { createShrineSubmission } from "@/lib/api/shrineSubmissions";
import { fetchShrineSuggest } from "@/lib/api/shrinesSuggest";
import { track } from "@/lib/analytics/track";
import type {
  ShrineSubmissionFieldErrors,
  ShrineSubmissionFormValues,
  ShrineSubmissionResponse,
  ShrineSubmissionTag,
} from "@/features/shrine-submission/types";

type Props = {
  onSubmitted: (submission: ShrineSubmissionResponse) => void;
  onRequireAuth: () => void;
};

type ShrineCandidate = {
  id: number;
  name: string;
  address: string;
};

const NAME_SUGGESTION_MIN_LENGTH = 2;
const NAME_SUGGESTION_DEBOUNCE_MS = 300;

function normalizeCandidate(value: unknown): ShrineCandidate | null {
  if (!value || typeof value !== "object") return null;

  const row = value as Record<string, unknown>;
  const id = typeof row.id === "number" ? row.id : null;
  const name = typeof row.name === "string" ? row.name : typeof row.name_jp === "string" ? row.name_jp : null;
  const address = typeof row.address === "string" ? row.address : "";

  if (!id || !name) return null;

  return {
    id,
    name,
    address,
  };
}

export function ShrineSubmissionForm({ onSubmitted, onRequireAuth }: Props) {
  const router = useRouter();

  const [form, setForm] = useState<ShrineSubmissionFormValues>({
    name: "",
    address: "",
    note: "",
  });
  const [errors, setErrors] = useState<ShrineSubmissionFieldErrors>({});
  const [tags, setTags] = useState<ShrineSubmissionTag[]>([]);
  const [tagsLoading, setTagsLoading] = useState(true);
  const [selectedTags, setSelectedTags] = useState<number[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [duplicateQuery, setDuplicateQuery] = useState<string | null>(null);
  const [duplicateCandidates, setDuplicateCandidates] = useState<ShrineCandidate[]>([]);
  const [nameSuggestions, setNameSuggestions] = useState<ShrineCandidate[]>([]);
  const [isSuggesting, setIsSuggesting] = useState(false);

  useEffect(() => {
    let active = true;
    setTagsLoading(true);

    getGoriyakuTags()
      .then((nextTags) => {
        if (!active) return;
        setTags(nextTags);
      })
      .catch(() => {
        if (!active) return;
        setErrors((prev) => ({
          ...prev,
          tags: "ご利益タグを取得できませんでした。未選択でも投稿でき、あとから審査時に補正されます。",
        }));
      })
      .finally(() => {
        if (active) {
          setTagsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const name = form.name.trim();

    if (isSubmitting || duplicateQuery || name.length < NAME_SUGGESTION_MIN_LENGTH) {
      setIsSuggesting(false);
      setNameSuggestions([]);
      return;
    }

    let active = true;
    setIsSuggesting(true);

    const timer = window.setTimeout(async () => {
      try {
        const response = await fetchShrineSuggest(name);
        if (!active) return;
        const next = response.results.map((candidate) => ({
          id: candidate.id,
          name: candidate.name,
          address: candidate.address,
        }));
        setNameSuggestions(next);
      } catch {
        if (!active) return;
        setNameSuggestions([]);
      } finally {
        if (active) {
          setIsSuggesting(false);
        }
      }
    }, NAME_SUGGESTION_DEBOUNCE_MS);

    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [duplicateQuery, form.name, isSubmitting]);

  const selectedTagNames = useMemo(
    () => tags.filter((tag) => selectedTags.includes(tag.id)).map((tag) => tag.name),
    [selectedTags, tags],
  );

  const tagStatusText = selectedTagNames.length > 0 ? `${selectedTagNames.length}件選択中` : "未選択でもOK";

  const clearErrors = (...keys: string[]) => {
    setErrors((prev) => {
      const next = { ...prev };
      for (const key of keys) {
        delete next[key];
      }
      return next;
    });
  };

  const isDuplicateMessage = (message?: string) => {
    if (!message) return false;
    return message.includes("重複") || message.includes("既に存在");
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.currentTarget;
    setForm((prev) => ({ ...prev, [name]: value }));
    clearErrors(name, "non_field_errors", "general");
    setDuplicateQuery(null);
    setDuplicateCandidates([]);
  };

  const toggleTag = (id: number) => {
    if (isSubmitting) return;

    setSelectedTags((prev) => (prev.includes(id) ? prev.filter((tagId) => tagId !== id) : [...prev, id]));
    clearErrors("tags", "non_field_errors", "general");
    setDuplicateQuery(null);
    setDuplicateCandidates([]);
  };

  const handleOpenDuplicateCandidates = () => {
    if (duplicateCandidates.length === 1) {
      router.push(`/shrines/${duplicateCandidates[0].id}`);
      return;
    }

    if (duplicateQuery) {
      router.push(`/shrines?q=${encodeURIComponent(duplicateQuery)}`);
    }
  };

  const handleOpenNameSuggestions = () => {
    const name = form.name.trim();

    if (nameSuggestions.length === 1) {
      router.push(`/shrines/${nameSuggestions[0].id}`);
      return;
    }

    if (nameSuggestions.length > 1 && name) {
      router.push(`/shrines?q=${encodeURIComponent(name)}`);
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isSubmitting) return;

    const name = form.name.trim();
    const address = form.address.trim();
    const note = form.note.trim();

    const nextErrors: ShrineSubmissionFieldErrors = {};

    if (!name) {
      nextErrors.name = "神社名は必須です。";
    }

    if (!address) {
      nextErrors.address = "住所は必須です。";
    }

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }

    setIsSubmitting(true);
    setDuplicateQuery(null);
    setDuplicateCandidates([]);
    clearErrors("name", "address", "tags", "note", "general");

    try {
      const created = await createShrineSubmission({
        name,
        address,
        goriyaku_tags: selectedTagNames,
        note,
      });
      track("shrine_submission_complete", {
        q: name,
        name: created.name ?? name,
        status: created.status ?? "pending",
      });
      onSubmitted(created);
      router.replace(`/shrines?q=${encodeURIComponent(name)}&submitted=1&status=pending`);
    } catch (err: unknown) {
      if (isApiError(err)) {
        if (err.status === 400 && err.body && typeof err.body === "object") {
          const body = err.body as Record<string, unknown>;
          const next: ShrineSubmissionFieldErrors = {};

          for (const [key, value] of Object.entries(body)) {
            if (Array.isArray(value) && typeof value[0] === "string") {
              next[key] = value[0];
            } else if (typeof value === "string") {
              next[key] = value;
            }
          }

          const backendMessage = next.non_field_errors ?? next.general ?? "入力内容を確認してください。";
          const duplicate = body.code === "duplicate_candidate" || isDuplicateMessage(backendMessage);
          const candidates = Array.isArray(body.candidates)
            ? body.candidates
                .map(normalizeCandidate)
                .filter((candidate): candidate is ShrineCandidate => candidate !== null)
            : [];

          setErrors({
            ...next,
            general: duplicate ? "この神社はすでに登録されている可能性があります。" : backendMessage,
          });

          if (duplicate) {
            setDuplicateQuery(name);
            setDuplicateCandidates(candidates);
          }

          return;
        }

        if (err.status === 401 || err.status === 403) {
          onRequireAuth();
          return;
        }
      }

      setErrors((prev) => ({
        ...prev,
        general: "投稿に失敗しました。時間をおいて再度お試しください。",
      }));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      {errors.general && (
        <div
          className={`space-y-3 rounded-2xl border p-4 ${duplicateQuery ? "border-red-300 bg-red-50" : "border-red-200 bg-white"}`}
        >
          <div className="space-y-1">
            <p className="text-sm font-semibold text-red-700">
              {duplicateQuery ? "この神社はすでに登録されている可能性があります。" : errors.general}
            </p>
            {duplicateQuery && (
              <p className="text-xs text-red-700">重複の可能性が高いため、投稿前に候補を確認してください。</p>
            )}
          </div>

          {duplicateQuery && (
            <>
              <p className="text-sm text-slate-700">同じ神社がすでに登録されている場合、追加投稿は不要です。</p>

              {duplicateCandidates.length > 0 && (
                <div className="space-y-2 rounded-xl border border-red-200 bg-white p-4">
                  <p className="text-xs font-semibold text-red-700">
                    {duplicateCandidates.length === 1 ? "確認が必要な候補" : "確認が必要な候補"}
                  </p>
                  {duplicateCandidates.map((candidate) => (
                    <div
                      key={candidate.id}
                      className="rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-sm text-slate-700"
                    >
                      <p className="font-medium text-slate-900">{candidate.name}</p>
                      <p className="mt-1 text-xs font-medium text-slate-700">{candidate.address || "住所未登録"}</p>
                      <p className="mt-1 text-[11px] text-red-700">
                        住所が一致する場合は、既存の神社の可能性が高いです。
                      </p>
                    </div>
                  ))}
                </div>
              )}

              <div className="pt-1">
                <button
                  type="button"
                  className="rounded-xl border border-red-200 bg-white px-4 py-2 text-sm font-medium text-red-700"
                  onClick={handleOpenDuplicateCandidates}
                >
                  {duplicateCandidates.length === 1 ? "既存神社の詳細を見る" : "候補一覧を見る"}
                </button>
              </div>
            </>
          )}
        </div>
      )}

      <div className="space-y-2">
        <label htmlFor="name" className="text-sm font-medium text-slate-900">
          神社名
        </label>
        <input
          id="name"
          name="name"
          value={form.name}
          onChange={handleChange}
          disabled={isSubmitting}
          className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900"
          placeholder="例: 明治神宮"
        />
        {errors.name && <p className="text-xs text-red-600">{errors.name}</p>}

        {!duplicateQuery && (isSuggesting || nameSuggestions.length > 0) && (
          <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
            <div>
              <p className="text-sm font-semibold text-slate-800">既存の神社候補</p>
              <p className="text-xs font-medium text-slate-700">
                同じ名前でも場所が違う神社があります。住所が近いか確認してください。違う神社なら、そのまま投稿できます。
              </p>
            </div>

            {isSuggesting && <p className="text-xs text-slate-700 font-medium">候補を確認しています...</p>}

            {!isSuggesting && nameSuggestions.length > 0 && (
              <>
                <div className="space-y-2">
                  {nameSuggestions.map((candidate) => (
                    <div
                      key={candidate.id}
                      className="rounded-lg border border-slate-200 bg-white/90 px-3 py-3 text-sm text-slate-700"
                    >
                      <p className="font-medium text-slate-900">{candidate.name}</p>
                      <p className="mt-1 text-xs font-medium text-slate-700">{candidate.address || "住所未登録"}</p>
                      <p className="mt-1 text-[11px] text-slate-500">
                        住所が近い場合は、この神社と同じ可能性があります。
                      </p>
                    </div>
                  ))}
                </div>

                <div className="space-y-2">
                  <button
                    type="button"
                    className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700"
                    onClick={handleOpenNameSuggestions}
                  >
                    {nameSuggestions.length === 1 ? "この神社と同じか確認する" : "候補を一覧で見る"}
                  </button>
                  {nameSuggestions.length === 1 && (
                    <p className="text-xs font-medium text-slate-700">住所が違う場合は、そのまま神社を追加できます。</p>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <label htmlFor="address" className="text-sm font-medium text-slate-900">
          住所 <span className="text-xs font-normal text-slate-500">任意</span>
        </label>
        <input
          id="address"
          name="address"
          value={form.address}
          onChange={handleChange}
          disabled={isSubmitting}
          className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900"
          placeholder="例: 東京都渋谷区代々木神園町1-1"
        />
        {errors.address && <p className="text-xs text-red-600">{errors.address}</p>}
      </div>

      <div className="space-y-4 rounded-2xl border border-emerald-100 bg-emerald-50/40 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-semibold text-slate-900">ご利益タグ</p>
              <span className="rounded-full bg-white px-2 py-0.5 text-[11px] font-semibold text-emerald-700 ring-1 ring-emerald-100">
                任意
              </span>
              <span className="rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-slate-500 ring-1 ring-slate-100">
                参考情報
              </span>
            </div>
            <p className="text-xs font-medium leading-relaxed text-slate-700">
              1つでも選ぶと、他の人に見つけてもらいやすくなります。未選択でも投稿できます。
            </p>
            <p className="text-[11px] leading-relaxed text-slate-500">
              選んだタグは公開前の確認時に参考情報として扱います。
            </p>
          </div>
          <span
            className={`shrink-0 rounded-full px-2.5 py-1 text-[11px] font-semibold ${
              selectedTagNames.length > 0
                ? "bg-emerald-600 text-white"
                : "bg-white text-slate-500 ring-1 ring-slate-200"
            }`}
          >
            {tagStatusText}
          </span>
        </div>

        {errors.tags && <p className="text-xs text-red-600">{errors.tags}</p>}

        {tagsLoading ? (
          <p className="rounded-xl border border-dashed border-emerald-200 bg-white px-3 py-2 text-xs font-medium text-slate-700">
            ご利益タグを読み込んでいます...
          </p>
        ) : tags.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => {
              const active = selectedTags.includes(tag.id);
              return (
                <button
                  key={tag.id}
                  type="button"
                  disabled={isSubmitting}
                  onClick={() => toggleTag(tag.id)}
                  aria-pressed={active}
                  className={`rounded-full border px-3.5 py-2 text-xs font-semibold shadow-sm transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-60 ${
                    active
                      ? "border-emerald-600 bg-emerald-600 text-white shadow-emerald-100 ring-2 ring-emerald-100"
                      : "border-slate-200 bg-white text-slate-700 hover:border-emerald-200 hover:bg-emerald-50 hover:text-emerald-700"
                  }`}
                >
                  {tag.name}
                </button>
              );
            })}
          </div>
        ) : (
          <p className="rounded-xl border border-dashed border-emerald-200 bg-white px-3 py-2 text-xs font-medium text-slate-700">
            選択できるご利益タグがありません。未選択でも投稿できます。
          </p>
        )}

        {selectedTagNames.length > 0 ? (
          <div className="rounded-xl bg-white px-3 py-2 text-xs font-medium text-emerald-700 ring-1 ring-emerald-100">
            選択中: {selectedTagNames.join("、")}
          </div>
        ) : !tagsLoading && !errors.tags && tags.length > 0 ? (
          <p className="rounded-xl bg-white px-3 py-2 text-xs font-medium text-slate-600 ring-1 ring-slate-100">
            未選択でも投稿できます。迷う場合は空欄のままで大丈夫です。
          </p>
        ) : null}
      </div>

      <div className="space-y-2">
        <label htmlFor="note" className="text-sm font-medium text-slate-900">
          補足文 <span className="text-xs font-normal text-slate-500">任意</span>
        </label>
        <textarea
          id="note"
          name="note"
          value={form.note}
          onChange={handleChange}
          disabled={isSubmitting}
          className="min-h-32 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900"
          placeholder="由緒、地元での呼び名、所在地の補足などがあれば書いてください。"
        />
        {errors.note && <p className="text-xs text-red-600">{errors.note}</p>}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full rounded-xl bg-emerald-600 px-4 py-3 text-sm text-white disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSubmitting ? "申請中..." : "神社を追加する"}
      </button>
    </form>
  );
}
