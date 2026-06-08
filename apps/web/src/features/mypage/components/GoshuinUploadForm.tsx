"use client";

import { FormEvent, useEffect, useMemo, useState, useRef } from "react";
import { useSearchParams } from "next/navigation";
import Image from "next/image";
import { uploadMyGoshuin } from "@/lib/api/goshuin";
import { getShrinePrivate, type Shrine } from "@/lib/api/shrines";

type Props = { onUploaded?: (g: any) => void };

export default function GoshuinUploadForm({ onUploaded }: Props) {
  
  const sp = useSearchParams();

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const shrineId = useMemo(() => {
    const q = sp.get("shrine");
    const n = Number(q);
    return Number.isFinite(n) && n > 0 ? n : null;
  }, [sp]);

  

  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isPublic, setIsPublic] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [shrine, setShrine] = useState<Shrine | null>(null);
  const [shrineLoading, setShrineLoading] = useState(false);

  useEffect(() => {
    let alive = true;

    (async () => {
      if (!shrineId) {
        if (alive) setShrine(null);
        return;
      }
      setShrineLoading(true);
      try {
        const s = await getShrinePrivate(shrineId);
        if (alive) setShrine(s);
      } catch {
        if (alive) setShrine(null);
      } finally {
        if (alive) setShrineLoading(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, [shrineId]);

  useEffect(() => {
    if (!file) return setPreviewUrl(null);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    
    if (loading) return;

    setError(null);
    setSuccess(null);

    if (!shrineId) return setError("神社が未選択です。「神社を選ぶ（地図）」から選択してください。");
    if (!file) return setError("画像ファイルを選択してください。");
    if (!file.type.startsWith("image/")) return setError("画像ファイルのみアップロードできます。");

    const maxBytes = 5 * 1024 * 1024;
    if (file.size > maxBytes) return setError("ファイルサイズは 5MB 以下を推奨しています。");

    try {
      setLoading(true);

      const created = await uploadMyGoshuin({ shrineId, title: "", isPublic, file });

      let patched = created as any;
      const hasShrineName = typeof patched?.shrine_name === "string" && patched.shrine_name.trim().length > 0;

      if (!hasShrineName) {
        try {
          const s = shrine ?? (await getShrinePrivate(shrineId));
          patched = {
            ...patched,
            shrine_id: patched.shrine_id ?? shrineId,
            shrine_name: patched.shrine_name ?? s?.name_jp ?? null,
            shrine: patched.shrine ?? s ?? null,
          };
        } catch {
          patched = { ...patched, shrine_id: patched.shrine_id ?? shrineId, shrine_name: patched.shrine_name ?? null };
        }
      }

      setSuccess("御朱印をアップロードしました。");
      setFile(null);
      setIsPublic(false);
      onUploaded?.(patched);
    } catch {
      setError("アップロードに失敗しました。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2 rounded-2xl border border-stone-200/20 bg-stone-50/30 p-4">
        <p className="text-xs font-medium text-stone-500">アップロード対象</p>

        {!shrineId ? (
          <>
            <p className="text-sm font-medium text-stone-900">未選択</p>
            <p className="text-xs text-stone-500">神社詳細ページから登録してください。</p>
          </>
        ) : (
          <>
            <p className="text-sm font-medium text-stone-900">
              {shrineLoading ? "読み込み中…" : (shrine?.name_jp ?? "神社名を取得できませんでした")}
            </p>
            {shrine?.address ? <p className="text-xs text-stone-500">{shrine.address}</p> : null}
          </>
        )}
      </div>

      <label className="inline-flex items-center gap-2 text-sm text-stone-700">
        <input
          type="checkbox"
          checked={isPublic}
          onChange={(e) => setIsPublic(e.target.checked)}
          className="h-4 w-4 rounded border-stone-300 text-emerald-800 focus:ring-stone-200"
        />
        公開する
      </label>

      <div className="rounded-xl border border-stone-200/20 bg-stone-50/20 p-4">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="w-full rounded-xl border border-stone-200/30 bg-stone-50/30 px-4 py-3 text-sm font-medium text-stone-700 transition hover:bg-stone-100/40 disabled:opacity-40"
          disabled={loading}
        >
          画像を選択
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          aria-label="御朱印画像"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />

        {file ? <p className="mt-2 text-xs text-stone-500">選択中: {file.name}</p> : null}
      </div>

      {previewUrl && (
        <Image
          src={previewUrl}
          alt="preview"
          width={400}
          height={400}
          unoptimized
          className="rounded-2xl border border-stone-200/20"
        />
      )}

      <button
        type="submit"
        disabled={!file || !shrineId || loading}
        className="rounded-full border border-emerald-700/20 bg-emerald-800 px-4 py-2 text-sm text-white transition hover:bg-emerald-900 disabled:opacity-40"
      >
        {loading ? "アップロード中..." : "アップロード"}
      </button>

      {success && <p className="text-sm text-emerald-800">{success}</p>}
      {error && <p className="text-sm text-rose-700">{error}</p>}
    </form>
  );
}
