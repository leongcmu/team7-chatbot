import { supportReplies } from "../fixtures/support.js";
import type { ChatRequest, ChatResponse } from "@eduling/contracts";
import { dialogue } from "../fixtures/dialogue.js";
import { sampleCourse } from "../fixtures/courses.js";
import { languageExample } from "../fixtures/language.js";
export function respond(req: ChatRequest): ChatResponse {
  const c = dialogue[req.language];
  const last = req.messages.at(-1)?.text ?? "";
  const previous = req.messages.at(-2);
  if (req.action === "find")
    return {
      text: c.goal,
      suggestions: c.goals.map((x, i) => ({
        id: `goal:${i}`,
        label: x,
        value: x,
      })),
    };
  if (
    req.selectionId?.startsWith("goal:") ||
    previous?.suggestions?.some(
      (s) => s.value === last && s.id?.startsWith("goal:"),
    ) ||
    Object.values(dialogue).some((l) => l.goals.includes(last))
  )
    return {
      text: c.level,
      suggestions: [...["A1", "A2", "B1", "B2", "C1", "C2"], c.unsure].map(
        (x, i) => ({ id: `level:${i}`, label: x, value: x }),
      ),
    };
  if (
    req.action === "browse" ||
    req.selectionId?.startsWith("level:") ||
    /^(A[12]|B[12]|C[12])$/.test(last) ||
    Object.values(dialogue).some((l) => l.unsure === last)
  )
    return {
      text: c.results,
      courses: [
        {
          ...sampleCourse,
          description: c.results,
          level: /^[ABC][12]$/.test(last) ? last : undefined,
        },
      ],
    };
  if (req.action === "explore") return { text: c.fallback };
  if (req.action === "language") return { text: c.language };
  if (/since.*for|for.*since/i.test(last))
    return { text: languageExample[req.language] };
  return {
    text: /student.*discount|学生.*优惠|descuento.*estudiante/i.test(last)
      ? supportReplies[req.language].discount
      : supportReplies[req.language].general,
    supportForm: { language: req.language, question: last },
  };
}
