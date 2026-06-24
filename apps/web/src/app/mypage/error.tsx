"use client";
export default function Error({ error }: { error: Error & { digest?: string } }) {
  return <div className="p-6 text-sm text-rose-700">エラーが発生しました：{error.message}</div>;
}
