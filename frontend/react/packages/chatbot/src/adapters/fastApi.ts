import type { ChatAction, MessageAdapter } from "@eduling/contracts";

interface FastApiResponse {
  answer: string;
  status: "answered" | "fallback" | "blocked" | "unavailable";
  actions: { type: ChatAction; label: string; url: string }[];
  related_articles: { title: string; url: string; summary: string }[];
}

export function createFastApiAdapter(baseUrl: string): MessageAdapter {
  return {
    async send(request, signal) {
      const message = request.messages.at(-1);
      if (message?.role !== "user" || !request.sessionId) {
        throw new Error("A user message and session ID are required.");
      }

      const response = await fetch(`${baseUrl.replace(/\/+$/, "")}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: message.text,
          session_id: request.sessionId,
        }),
        signal,
      });
      if (!response.ok) {
        throw new Error(`Chat request failed (${response.status}).`);
      }
      const result: FastApiResponse = await response.json();
      return {
        text: result.answer,
        links: [
          ...result.actions.map(({ type, label, url }) => ({ action: type, label, url })),
          ...result.related_articles.map(({ title, url, summary }) => ({
            label: title,
            url,
            summary,
          })),
        ],
      };
    },
  };
}
