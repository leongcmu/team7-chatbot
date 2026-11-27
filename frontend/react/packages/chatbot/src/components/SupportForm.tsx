import { useId, useState } from "react";
import { supportCopy } from "../i18n/support";
/** Local UI fixture only. Contact details never leave this component or enter history. */
export function SupportForm({
  question,
}: {
  question: string;
}) {
  const c = supportCopy.en;
  const id = useId();
  const [submitted, setSubmitted] = useState(false);
  return (
    <div className="eduling-support">
      <p>{c.intro}</p>
      {submitted ? (
        <p role="status">{c.success}</p>
      ) : (
        <form
          aria-label={c.intro}
          onSubmit={(e) => {
            e.preventDefault();
            setSubmitted(true);
          }}
        >
          <label className="eduling-sr" htmlFor={`${id}-name`}>
            {c.name}
          </label>
          <input
            id={`${id}-name`}
            name="name"
            placeholder={c.name}
            autoComplete="name"
            required
            maxLength={100}
          />
          <label className="eduling-sr" htmlFor={`${id}-email`}>
            {c.email}
          </label>
          <input
            id={`${id}-email`}
            name="email"
            type="email"
            placeholder={c.email}
            autoComplete="email"
            required
            maxLength={254}
          />
          <label className="eduling-sr" htmlFor={`${id}-message`}>
            {c.message}
          </label>
          <textarea
            id={`${id}-message`}
            name="message"
            placeholder={c.message}
            defaultValue={question}
            required
            maxLength={2000}
            rows={4}
          />
          <button type="submit">{c.submit}</button>
          <small>{c.notice}</small>
        </form>
      )}
    </div>
  );
}
