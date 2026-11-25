"use client";

import axios from "axios";
import { useCallback, useEffect, useRef, useState } from "react";

import { ConciergeThreadsResponseError, fetchThreadsStrict } from "@/lib/api/concierge";

// 「あとで見返すために保存」(save_prompt) の保存確認フロー。
//
// backend は /api/concierge/chat/ の全リクエストで thread を永続化しており
// (認証済みなら thread.user に紐づく)、保存専用 API は存在しない。
// ここでは新たな永続化を行わず、ユーザー所有の履歴一覧
// (GET /api/concierge-threads/ = IsAuthenticated + filter(user=user)) に
// 対象 thread が含まれることを確認できた場合にのみ「保存済み」とする。
// thread 詳細 API は anon cookie 一致でも 200 を返すため、所有確認には使わない。
//
// 制約: 一覧 API は最新 50 件のみ返すため、それより古い thread は確認できず error になる。

export type ConciergeThreadSaveStatus = "idle" | "saving" | "saved" | "error";

// server_unavailable: backend が 5xx を返した（API 失敗）
// invalid_response : 2xx だが一覧の形式で読めなかった（parse 失敗）
// network          : 応答自体が得られなかった、またはその他の失敗
export type ConciergeThreadSaveError =
  | "no_thread"
  | "not_owned"
  | "unauthenticated"
  | "server_unavailable"
  | "invalid_response"
  | "network";

export type ConciergeThreadSaveState = {
  status: ConciergeThreadSaveStatus;
  error: ConciergeThreadSaveError | null;
  historyHref: string | null;
};

const IDLE: ConciergeThreadSaveState = { status: "idle", error: null, historyHref: null };

export function buildConciergeHistoryHref(threadId: number): string {
  return `/mypage/history/${threadId}`;
}

function classifySaveError(err: unknown): ConciergeThreadSaveError {
  if (err instanceof ConciergeThreadsResponseError) return "invalid_response";
  if (axios.isAxiosError(err)) {
    const status = err.response?.status;
    if (status === 401) return "unauthenticated";
    if (typeof status === "number" && status >= 500) return "server_unavailable";
  }
  return "network";
}

type Options = {
  threadId: number | null | undefined;
  canSave: boolean;
  onAuthRequired: () => void;
};

export function useConciergeThreadSave({ threadId, canSave, onAuthRequired }: Options) {
  const [state, setState] = useState<ConciergeThreadSaveState>(IDLE);
  const inFlightRef = useRef(false);
  const savedThreadIdRef = useRef<number | null>(null);
  const currentThreadIdRef = useRef<number | null>(null);

  const normalizedThreadId = typeof threadId === "number" && threadId > 0 ? threadId : null;
  currentThreadIdRef.current = normalizedThreadId;

  // 別の相談結果へ切り替わったら前の保存状態を持ち越さない。
  useEffect(() => {
    if (savedThreadIdRef.current !== normalizedThreadId) {
      savedThreadIdRef.current = null;
      setState(IDLE);
    }
  }, [normalizedThreadId]);

  const save = useCallback(async () => {
    if (!canSave) {
      onAuthRequired();
      return;
    }

    // 二重送信防止: 確認中 / 確認済みの thread には再リクエストしない。
    if (inFlightRef.current) return;
    if (normalizedThreadId != null && savedThreadIdRef.current === normalizedThreadId) return;

    if (normalizedThreadId == null) {
      setState({ status: "error", error: "no_thread", historyHref: null });
      return;
    }

    const targetId = normalizedThreadId;
    inFlightRef.current = true;
    setState({ status: "saving", error: null, historyHref: null });

    let next: ConciergeThreadSaveState;
    try {
      const threads = await fetchThreadsStrict();
      const owned = threads.some((t) => Number(t.id) === targetId);
      next = owned
        ? { status: "saved", error: null, historyHref: buildConciergeHistoryHref(targetId) }
        : { status: "error", error: "not_owned", historyHref: null };
    } catch (err) {
      next = { status: "error", error: classifySaveError(err), historyHref: null };
    } finally {
      inFlightRef.current = false;
    }

    // 確認中に別の thread へ切り替わっていたら結果を捨てる。
    if (currentThreadIdRef.current !== targetId) return;
    if (next.status === "saved") savedThreadIdRef.current = targetId;
    setState(next);
  }, [canSave, normalizedThreadId, onAuthRequired]);

  return { state, save };
}
