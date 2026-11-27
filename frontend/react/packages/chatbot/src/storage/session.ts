import type { Message } from "@eduling/contracts";
export interface Session {
  version: 1;
  sessionId?: string;
  updatedAt: number;
  messages: Message[];
}
function validMessage(m: Message): boolean {
  return (
    !!m &&
    typeof m.id === "string" &&
    ["user", "assistant"].includes(m.role) &&
    typeof m.text === "string" &&
    m.text.length <= 20000 &&
    (m.links === undefined ||
      (Array.isArray(m.links) && m.links.every(
        (link) => link && typeof link.label === "string" &&
          typeof link.url === "string" &&
          (link.summary === undefined || typeof link.summary === "string"),
      ))) &&
    (m.supportForm === undefined ||
      (!!m.supportForm &&
        ["en", "zh", "es"].includes(m.supportForm.language) &&
        typeof m.supportForm.question === "string" &&
        m.supportForm.question.length <= 2000)) &&
    (m.courses === undefined ||
      (Array.isArray(m.courses) &&
        m.courses.length <= 3 &&
        m.courses.every(
          (c) =>
            c &&
            typeof c.id === "string" &&
            typeof c.title === "string" &&
            typeof c.description === "string" &&
            [c.level, c.goal, c.url].every(
              (v) => v === undefined || typeof v === "string",
            ) &&
            (c.mock === undefined || typeof c.mock === "boolean"),
        ))) &&
    (m.suggestions === undefined ||
      (Array.isArray(m.suggestions) &&
        m.suggestions.length <= 10 &&
        m.suggestions.every(
          (s) =>
            s &&
            typeof s.label === "string" &&
            typeof s.value === "string" &&
            (s.id === undefined || typeof s.id === "string"),
        )))
  );
}
export const RETENTION_MS = 24 * 60 * 60 * 1000;
export function loadSession(key: string): Session | undefined {
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return;
    const s = JSON.parse(raw);
    if (
      s.version !== 1 ||
      (s.sessionId !== undefined &&
        (typeof s.sessionId !== "string" || !/^[A-Za-z0-9_-]{12,128}$/.test(s.sessionId))) ||
      !Number.isFinite(s.updatedAt) ||
      Date.now() - s.updatedAt > RETENTION_MS ||
      s.updatedAt > Date.now() ||
      !Array.isArray(s.messages) ||
      s.messages.length > 100 ||
      !s.messages.every(validMessage)
    ) {
      sessionStorage.removeItem(key);
      return;
    }
    return s;
  } catch {
    return;
  }
}
export function saveSession(key: string, s: Session) {
  try {
    sessionStorage.setItem(key, JSON.stringify(s));
  } catch {
    /* Storage may be disabled; in-memory chat still works. */
  }
}
export function clearSession(key: string) {
  try {
    sessionStorage.removeItem(key);
  } catch {
    /* Best effort. */
  }
}
