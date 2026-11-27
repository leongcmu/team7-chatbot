import { SupportForm } from "./SupportForm";
import type { useConversation } from "../hooks/useConversation";
import type { EdulingChatbotProps } from "../EdulingChatbot";
import avatar from "../assets/avatar.svg";
import { CourseCard } from "./CourseCard";
import { ReplyText } from "./ReplyText";
import { DownloadCard, downloadAction } from "./DownloadCard";

type Props = Pick<
  ReturnType<typeof useConversation>,
  "c" | "messages" | "pending" | "error" | "send"
> & { onCourseClick?: EdulingChatbotProps["onCourseClick"] };
export function MessageList({
  c,
  messages,
  pending,
  error,
  send,
  onCourseClick,
}: Props) {
  return (
    <div
      role="log"
      aria-live="polite"
      aria-relevant="additions"
      aria-label="Conversation"
    >
      {messages.map((m) => {
        const links = m.links?.filter(({ url }) => /^https?:\/\//i.test(url)) ?? [];
        const downloads = links.filter(downloadAction);
        return (
          <article key={m.id} className={`eduling-message eduling-${m.role}`}>
            <span className="eduling-sr">
              {m.role === "user" ? "You" : "Eduling AI"}:{" "}
            </span>
            {m.role === "assistant" && (
              <div className="eduling-assistant">
                <span className="eduling-avatar">
                  <img width={24} height={24} src={avatar} alt="" />
                </span>
                <small>Eduling AI</small>
              </div>
            )}
            {m.role === "assistant" ? <ReplyText text={m.text} /> : <p>{m.text}</p>}
            {downloads.length > 0 && <DownloadCard links={downloads} />}
            {links.filter((link) => !downloadAction(link)).map((link) => {
              const subscription = link.action === "subscribe_website" ||
                (link.action === undefined && link.label === "View website subscriptions");
              return (
                <div key={link.url} className="eduling-reply-link">
                  <a
                    className={subscription ? "eduling-subscription" : undefined}
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {link.label}
                    {subscription && <span aria-hidden="true">↗</span>}
                  </a>
                  {link.summary && <p>{link.summary}</p>}
                </div>
              );
            })}
            {m.supportForm && (
              <SupportForm
                question={m.supportForm.question}
              />
            )}
            {m.courses?.map((course) => (
              <CourseCard
                key={course.id}
                course={course}
                c={c}
                onCourseClick={onCourseClick}
              />
            ))}
            {m.suggestions && (
              <div className="eduling-suggestions">
                {m.suggestions.map((s) => (
                  <button
                    key={s.value}
                    disabled={pending || error}
                    onClick={() => send(s.value, undefined, s.id)}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}
