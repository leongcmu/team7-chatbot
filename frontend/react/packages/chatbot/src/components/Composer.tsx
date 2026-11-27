import { useLayoutEffect } from "react";
import type { useConversation } from "../hooks/useConversation";
import arrow from "../assets/arrow.svg";
type Props = Pick<
  ReturnType<typeof useConversation>,
  | "c"
  | "draft"
  | "setDraft"
  | "send"
  | "input"
  | "ready"
  | "pending"
  | "error"
  | "reset"
> & { maxLength: number; live: boolean };
export function Composer({
  c,
  draft,
  setDraft,
  send,
  input,
  ready,
  pending,
  error,
  reset,
  maxLength,
  live,
}: Props) {
  useLayoutEffect(() => {
    const textarea = input.current;
    if (!textarea) return;

    function resize() {
      if (!textarea) return;
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }

    resize();
    if (typeof ResizeObserver === "undefined") return;
    let width = textarea.clientWidth;
    const observer = new ResizeObserver(() => {
      if (textarea.clientWidth === width) return;
      width = textarea.clientWidth;
      resize();
    });
    observer.observe(textarea);
    return () => observer.disconnect();
  }, [draft, input]);

  return (
    <footer className="eduling-footer">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(draft);
        }}
      >
        <textarea
          ref={input}
          aria-label={c.placeholder}
          placeholder={c.placeholder}
          value={draft}
          rows={1}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (
              e.key === "Enter" &&
              !e.shiftKey &&
              !e.nativeEvent.isComposing
            ) {
              e.preventDefault();
              send(draft);
            }
          }}
        />
        <button
          className="eduling-send"
          aria-label={c.send}
          disabled={
            !ready || pending || error || !draft.trim() || draft.length > maxLength
          }
        >
          <img width={24} height={24} src={arrow} alt="" />
        </button>
      </form>
      {draft.length > maxLength && <p role="alert">{live ? c.liveLimit : c.limit}</p>}
      <div className="eduling-meta">
        {!live && <small>{c.notice}</small>}
        <button onClick={reset}>{c.reset}</button>
      </div>
    </footer>
  );
}
