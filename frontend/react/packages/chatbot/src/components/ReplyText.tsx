import { Fragment } from "react";

const bullet = /^\s*[-*+]\s+(.+)$/;

const supportEmail = "info@eduling.org";

function replyLinks(text: string) {
  return text.split(/(\binfo@eduling\.org\b)/gi).map((part, index) =>
    part.toLowerCase() === supportEmail ? (
      <a key={index} className="eduling-email-link" href={`mailto:${supportEmail}`}>
        {part}
      </a>
    ) : part,
  );
}

function emphasis(text: string) {
  return text.split(/(\*\*[^*\n]+\*\*|__[^_\n]+__)/g).map((part, index) =>
    index % 2 ? <strong key={index}>{replyLinks(part.slice(2, -2))}</strong> :
      <Fragment key={index}>{replyLinks(part)}</Fragment>,
  );
}

export function ReplyText({ text }: { text: string }) {
  const blocks: { list: boolean; lines: string[] }[] = [];
  for (const line of text.split(/\r?\n/)) {
    const match = bullet.exec(line);
    const list = !!match;
    const last = blocks.at(-1);
    if (last?.list === list) {
      last.lines.push(match?.[1] ?? line);
    } else {
      blocks.push({ list, lines: [match?.[1] ?? line] });
    }
  }

  return (
    <div className="eduling-reply">
      {blocks.map(({ list, lines }, index) => {
        if (list) {
          return (
            <ul key={index}>
              {lines.map((line, item) => <li key={item}>{emphasis(line)}</li>)}
            </ul>
          );
        }
        const paragraph = lines.join("\n").trim();
        return paragraph && <p key={index}>{emphasis(paragraph)}</p>;
      })}
    </div>
  );
}
