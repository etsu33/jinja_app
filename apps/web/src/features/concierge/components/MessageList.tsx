import { useEffect, useRef } from "react";
import type { ConciergeMessage } from "@/lib/api/concierge";

type Props = {
  messages: ConciergeMessage[];
};

export default function MessageList({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // 自動スクロール（新規メッセージ追加時）
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [messages.length]);

  return (
    <div className="space-y-2">
      {messages.map((m) => {
        const isUser = m.role === "user";

        return (
          <div key={m.id} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
            <div
              className={[
                "inline-block max-w-[80%] rounded-2xl px-3 py-2 text-[13px] leading-relaxed",
                isUser
                  ? "bg-[var(--kt-color-message-own-background)] text-[var(--kt-color-message-own-text)]"
                  : "bg-[var(--kt-color-surface-default)] text-[var(--kt-color-text-primary)] border border-[var(--kt-color-border-default)]",
              ].join(" ")}
            >
              {m.content}
            </div>
          </div>
        );
      })}
      {/* 自動スクロール用のアンカー */}
      <div ref={bottomRef} />
    </div>
  );
}
