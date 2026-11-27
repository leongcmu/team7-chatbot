import type { useConversation } from "../hooks/useConversation";
import avatar from "../assets/avatar.svg";
import expand from "../assets/expand.svg";
import close from "../assets/close.svg";
type Props = Pick<
  ReturnType<typeof useConversation>,
  | "c"
  | "expanded"
  | "setExpanded"
  | "toggle"
>;
export function ChatHeader({
  c,
  expanded,
  setExpanded,
  toggle,
}: Props) {
  return (
    <header className="eduling-header">
      <span className="eduling-avatar">
        <img width={24} height={24} src={avatar} alt="" />
      </span>
      <div className="eduling-identity">
        <strong>Eduling AI</strong>
        <small>{c.companion}</small>
      </div>
      <button
        className="eduling-icon"
        aria-label={expanded ? c.restore : c.expand}
        aria-pressed={expanded}
        onClick={() => setExpanded(!expanded)}
      >
        <img width={24} height={24} src={expand} alt="" />
      </button>
      <button
        className="eduling-icon"
        aria-label={c.close}
        onClick={() => toggle(false)}
      >
        <img width={24} height={24} src={close} alt="" />
      </button>
    </header>
  );
}
