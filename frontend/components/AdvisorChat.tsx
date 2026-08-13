"use client";

import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { postAdvisor } from "@/lib/api";
import { useSession } from "@/context/SessionContext";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isError?: boolean;
}

interface AdvisorChatProps {
  businessProfile: Record<string, string> | { business_name: string; industry: string; goals: string };
}

const STARTER_PROMPTS = [
  "What's my best-selling product right now?",
  "Which day should I schedule more staff?",
  "Is there anything I should be worried about?",
  "What's one thing I could do to increase revenue this week?",
];

function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
}

export default function AdvisorChat({ businessProfile }: AdvisorChatProps) {
  const { sessionId } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  async function send(text?: string) {
    const content = (text ?? input).trim();
    if (!content || !sessionId) return;
    const userMsg: Message = { role: "user", content, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setTyping(true);

    try {
      const res = await postAdvisor({
        session_id: sessionId,
        message: content,
        conversation_history: [...messages, userMsg].map((m) => ({ role: m.role, content: m.content })),
        business_profile: { ...businessProfile },
      });
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply, timestamp: new Date() }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "I ran into an issue. Please try again.", timestamp: new Date(), isError: true },
      ]);
    } finally {
      setTyping(false);
    }
  }

  function clearChat() {
    if (window.confirm("Clear conversation history?")) {
      setMessages([]);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Header with clear button */}
      {messages.length > 0 && (
        <div style={{ display: "flex", justifyContent: "flex-end", padding: "10px 16px 0" }}>
          <button
            onClick={clearChat}
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "0.72rem",
              color: "var(--text-muted)",
              background: "none",
              border: "none",
              cursor: "pointer",
              transition: "color 0.15s ease",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "var(--t1)" }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)" }}
          >
            Clear chat
          </button>
        </div>
      )}

      <div style={{
        flex: 1,
        overflowY: "auto",
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        maxHeight: "calc(100vh - 280px)",
      }}>
        {messages.length === 0 && !typing && (
          <>
            <div style={{
              backgroundColor: "var(--surface-warm)",
              border: "1px solid var(--border-warm)",
              borderRadius: "20px",
              borderTopLeftRadius: "4px",
              padding: "16px 18px",
              maxWidth: "min(85%, 600px)",
            }}>
              <p style={{
                fontFamily: "var(--font-body)",
                color: "var(--t2)",
                fontSize: "0.88rem",
                lineHeight: 1.65,
              }}>
                Upload your data and ask me anything about your business. I&apos;ll give you specific, actionable advice based on your actual numbers.
              </p>
            </div>

            {/* Starter prompts */}
            <div className="chip-container">
              {STARTER_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => send(prompt)}
                  style={{
                    backgroundColor: "var(--bg-alt)",
                    border: "1px solid var(--border-warm)",
                    borderRadius: "999px",
                    padding: "12px 18px",
                    fontFamily: "var(--font-body)",
                    fontWeight: 600,
                    fontSize: "0.82rem",
                    color: "var(--accent)",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                    minHeight: "44px",
                    whiteSpace: "nowrap",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = "var(--surface)"
                    e.currentTarget.style.borderColor = "var(--border-accent)"
                    e.currentTarget.style.boxShadow = "var(--shadow-xs)"
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "var(--bg-alt)"
                    e.currentTarget.style.borderColor = "var(--border-warm)"
                    e.currentTarget.style.boxShadow = "none"
                  }}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </>
        )}

        {messages.map((msg, i) => (
          <div key={i} style={{
            display: "flex",
            justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
          }}>
            <div style={{
              maxWidth: "min(85%, 600px)",
              padding: "16px 18px",
              borderRadius: "20px",
              ...(msg.role === "user"
                ? {
                    backgroundColor: "var(--accent)",
                    border: "1px solid var(--accent)",
                    borderTopRightRadius: "4px",
                  }
                : {
                    backgroundColor: "var(--bg-mid)",
                    border: "1px solid var(--border)",
                    borderTopLeftRadius: "4px",
                  }),
            }}>
              <p style={{
                fontFamily: "var(--font-body)",
                fontSize: "0.88rem",
                whiteSpace: "pre-wrap",
                lineHeight: 1.65,
                color: msg.isError
                  ? "var(--red)"
                  : msg.role === "user" ? "#ffffff" : "var(--t1)",
              }}>
                {msg.content}
              </p>
              <p style={{
                fontFamily: "var(--font-body)",
                fontSize: "0.62rem",
                marginTop: "6px",
                opacity: msg.role === "user" ? 0.85 : 1,
                color: msg.role === "user" ? "#ffffff" : "var(--t2)",
              }}>
                {formatTime(msg.timestamp)}
              </p>
            </div>
          </div>
        ))}

        {typing && (
          <div style={{ display: "flex", justifyContent: "flex-start" }}>
            <div style={{
              backgroundColor: "var(--surface-warm)",
              border: "1px solid var(--border-warm)",
              borderRadius: "20px",
              borderTopLeftRadius: "4px",
              padding: "16px 18px",
              display: "flex",
              gap: "6px",
            }}>
              <span className="animate-bounce" style={{ width: "8px", height: "8px", backgroundColor: "var(--accent)", borderRadius: "50%", animationDelay: "0ms" }} />
              <span className="animate-bounce" style={{ width: "8px", height: "8px", backgroundColor: "var(--accent)", borderRadius: "50%", animationDelay: "150ms" }} />
              <span className="animate-bounce" style={{ width: "8px", height: "8px", backgroundColor: "var(--accent)", borderRadius: "50%", animationDelay: "300ms" }} />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div style={{
        borderTop: "1px solid var(--border-warm)",
        padding: "16px",
        display: "flex",
        gap: "12px",
      }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
          placeholder="Ask about your business..."
          rows={1}
          style={{
            flex: 1,
            backgroundColor: "var(--surface-warm)",
            border: "1px solid var(--border-warm)",
            borderRadius: "14px",
            padding: "14px 16px",
            fontFamily: "var(--font-body)",
            color: "var(--text-primary)",
            fontSize: "16px",
            resize: "none",
            outline: "none",
            transition: "border-color 0.15s ease",
            minHeight: "48px",
          }}
          onFocus={(e) => { e.currentTarget.style.borderColor = "var(--border-accent)" }}
          onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border-warm)" }}
        />
        <button
          onClick={() => send()}
          disabled={!input.trim() || typing}
          style={{
            backgroundColor: "var(--accent)",
            color: "#ffffff",
            borderRadius: "14px",
            padding: "14px 16px",
            border: "none",
            cursor: !input.trim() || typing ? "not-allowed" : "pointer",
            opacity: !input.trim() || typing ? 0.5 : 1,
            transition: "all 0.15s ease",
            minHeight: "48px",
            minWidth: "48px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
          onMouseEnter={(e) => {
            if (input.trim() && !typing) {
              e.currentTarget.style.backgroundColor = "var(--lp-accent-dark)"
              e.currentTarget.style.transform = "translateY(-1px)"
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "var(--accent)"
            e.currentTarget.style.transform = "translateY(0)"
          }}
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
