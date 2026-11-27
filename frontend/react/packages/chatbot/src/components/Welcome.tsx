import type { QuickAction } from "@eduling/contracts";
import { copy } from "../i18n";
import { quickActions } from "../config/quickActions";
import star from "../assets/star.svg";
import avatar from "../assets/avatar.svg";
export function Welcome({
  c,
  disabled,
  onAction,
}: {
  c: typeof copy.en;
  disabled: boolean;
  onAction: (text: string, action: QuickAction) => void;
}) {
  return (
    <div className="eduling-welcome">
      <span className="eduling-avatar">
        <img width={24} height={24} src={avatar} alt="" />
      </span>
      <h1>{c.hero}</h1>
      <p>{c.intro}</p>
      <div className="eduling-actions">
        {quickActions.map((a, i) => (
          <button
            key={a}
            onClick={() => onAction(c.actions[i], a)}
            disabled={disabled}
          >
            <img width={24} height={24} src={star} alt="" />
            <span>
              <strong>{c.actions[i]}</strong>
              <small>{c.descriptions[i]}</small>
            </span>
          </button>
        ))}
      </div>
      <small>{c.hint}</small>
    </div>
  );
}
