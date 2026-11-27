import { MessageList } from "./components/MessageList";
import { Composer } from "./components/Composer";
import { ChatHeader } from "./components/ChatHeader";
import type { MessageAdapter } from "./adapters";
import { useMemo, type CSSProperties } from "react";
import { createFastApiAdapter } from "./adapters/fastApi";
import { useConversation } from "./hooks/useConversation";
import { Welcome } from "./components/Welcome";
import type { Course } from "./types";
import chat from "./assets/chat.svg";
import "./styles/chatbot.css";
export interface EdulingChatbotProps {
  /** FastAPI base URL. An explicitly supplied adapter takes precedence. */
  apiBaseUrl?: string;
  adapter?: MessageAdapter;
  defaultOpen?: boolean;
  /** Same key preserves session across same-origin routes in this browser tab. false disables storage. */
  storageKey?: string | false;
  onOpenChange?: (open: boolean) => void;
  onCourseClick?: (course: Course) => void;
  /** Set --eduling-* custom properties here. */
  style?: CSSProperties;
}
export function EdulingChatbot({
  apiBaseUrl,
  adapter,
  defaultOpen = false,
  storageKey = "eduling-chatbot:v1",
  onOpenChange,
  onCourseClick,
  style,
}: EdulingChatbotProps) {
  const fastApi = useMemo(
    () => apiBaseUrl === undefined ? undefined : createFastApiAdapter(apiBaseUrl),
    [apiBaseUrl],
  );
  const live = !adapter && !!fastApi;
  const {
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
  } = useConversation({
    adapter: adapter ?? fastApi,
    maxLength: live ? 1500 : 2000,
    defaultOpen,
    storageKey,
    onOpenChange,
  });
  return (
    <div
      className="eduling-chatbot"
      style={style}
      data-api-configured={live}
    >
      <button
        ref={launcher}
        className="eduling-launcher"
        hidden={open}
        aria-expanded={open}
        aria-controls={id}
        onClick={() => toggle(true)}
      >
        {c.launcher}
        <img width={24} height={24} src={chat} alt="" />
      </button>
      {open && (
        <section
          id={id}
          role="dialog"
          aria-label="Eduling AI"
          lang="en"
          className={`eduling-panel${expanded ? " eduling-expanded" : ""}`}
          onKeyDown={(e) => {
            if (e.key === "Escape") {
              e.stopPropagation();
              toggle(false);
            }
          }}
        >
          <ChatHeader
            c={c}
            expanded={expanded}
            setExpanded={setExpanded}
            toggle={toggle}
          />
          <div className="eduling-messages" ref={scroller}>
            <Welcome
              c={c}
              disabled={!ready || pending || error}
              onAction={send}
            />
            <MessageList
              c={c}
              messages={messages}
              pending={pending}
              error={error}
              send={send}
              onCourseClick={onCourseClick}
            />
            {pending && <p role="status">{c.loading}</p>}
            {error && (
              <div role="alert">
                <p>{c.error}</p>
                <button
                  onClick={() =>
                    lastRequest.current && void deliver(lastRequest.current)
                  }
                >
                  {c.retry}
                </button>
              </div>
            )}
          </div>
          <Composer
            c={c}
            draft={draft}
            setDraft={setDraft}
            send={send}
            input={input}
            ready={ready}
            pending={pending}
            error={error}
            reset={reset}
            maxLength={live ? 1500 : 2000}
            live={live}
          />
        </section>
      )}
    </div>
  );
}
