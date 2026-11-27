import { useEffect, useId, useRef, useState } from "react";
import { createMockAdapter } from "@eduling/mocks";
import { copy } from "../i18n";
import { clearSession, loadSession, saveSession } from "../storage/session";
import type {
  ChatRequest,
  Message,
  QuickAction,
} from "@eduling/contracts";
import type { EdulingChatbotProps } from "../EdulingChatbot";
export function useConversation({
  adapter,
  maxLength = 2000,
  defaultOpen = false,
  storageKey = "eduling-chatbot:v1",
  onOpenChange,
}: EdulingChatbotProps & { maxLength?: number }) {
  const [open, setOpen] = useState(defaultOpen),
    [expanded, setExpanded] = useState(false),
    [messages, setMessages] = useState<Message[]>([]),
    [draft, setDraft] = useState(""),
    [pending, setPending] = useState(false),
    [error, setError] = useState(false),
    [ready, setReady] = useState(false);
  const defaultAdapter = useRef(createMockAdapter());
  const transport = adapter ?? defaultAdapter.current;
  const controller = useRef<AbortController | null>(null),
    lastRequest = useRef<ChatRequest | null>(null),
    busy = useRef(false),
    generation = useRef(0),
    launcher = useRef<HTMLButtonElement>(null),
    input = useRef<HTMLTextAreaElement>(null),
    scroller = useRef<HTMLDivElement>(null);
  const sessionId = useRef<string>(null);
  const id = useId();
  const c = copy.en;
  useEffect(() => {
    const s = storageKey ? loadSession(storageKey) : undefined;
    sessionId.current = s?.sessionId ?? crypto.randomUUID();
    setMessages(s?.messages ?? []);
    setReady(true);
    return () => {
      generation.current++;
      controller.current?.abort();
      busy.current = false;
    };
  }, [storageKey]);
  useEffect(() => {
    if (ready && storageKey)
      saveSession(storageKey, {
        version: 1,
        sessionId: sessionId.current ?? undefined,
        updatedAt: Date.now(),
        messages: messages.slice(-100),
      });
  }, [messages, ready, storageKey]);
  useEffect(() => {
    if (open) input.current?.focus();
  }, [open]);
  useEffect(() => {
    const container = scroller.current;
    if (container)
      container.scrollTo?.({
        top: messages.length ? container.scrollHeight : 0,
        behavior: messages.length ? "smooth" : "auto",
      });
  }, [messages, pending, open]);
  function toggle(next: boolean) {
    setOpen(next);
    onOpenChange?.(next);
    if (!next) queueMicrotask(() => launcher.current?.focus());
  }
  async function deliver(req: ChatRequest) {
    if (busy.current) return;
    busy.current = true;
    const token = ++generation.current;
    controller.current = new AbortController();
    setPending(true);
    setError(false);
    lastRequest.current = req;
    try {
      const response = await transport.send(req, controller.current.signal);
      if (token !== generation.current) return;
      setMessages((prev) => [
        ...prev,
        { ...response, id: crypto.randomUUID(), role: "assistant" },
      ]);
      lastRequest.current = null;
    } catch {
      if (token === generation.current && !controller.current?.signal.aborted)
        setError(true);
    } finally {
      if (token === generation.current) {
        busy.current = false;
        setPending(false);
      }
    }
  }
  function send(text: string, action?: QuickAction, selectionId?: string) {
    if (!ready || busy.current || error || !text.trim() || text.length > maxLength)
      return;
    const next: Message[] = [
      ...messages,
      { id: crypto.randomUUID(), role: "user", text: text.trim() },
    ];
    setMessages(next);
    setDraft("");
    void deliver({
      requestId: crypto.randomUUID(),
      sessionId: sessionId.current ?? undefined,
      messages: next,
      language: "en",
      action,
      selectionId,
    });
  }
  function reset() {
    generation.current++;
    controller.current?.abort();
    busy.current = false;
    lastRequest.current = null;
    sessionId.current = crypto.randomUUID();
    setPending(false);
    setError(false);
    setMessages([]);
    setDraft("");
    if (storageKey) clearSession(storageKey);
    input.current?.focus();
  }
  return {
    open,
    expanded,
    setExpanded,
    messages,
    draft,
    setDraft,
    pending,
    error,
    ready,
    c,
    id,
    launcher,
    input,
    scroller,
    toggle,
    send,
    reset,
    deliver,
    lastRequest,
  };
}
