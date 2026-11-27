export type Language = "en" | "zh" | "es";
export type LanguageMode = "auto" | Language;
export type QuickAction = "explore" | "find" | "browse" | "language";
export interface Course {
  id: string;
  title: string;
  description: string;
  level?: string;
  goal?: string;
  url?: string;
  mock?: boolean;
}
export interface Suggestion {
  label: string;
  value: string;
  id?: string;
}
export type ChatAction = "download_ios" | "download_android" | "subscribe_website";

export interface ChatLink {
  action?: ChatAction;
  url: string;
  label: string;
  summary?: string;
}
export interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  links?: ChatLink[];
  courses?: Course[];
  suggestions?: Suggestion[];
  supportForm?: { language: Language; question: string };
}
export interface ChatRequest {
  requestId: string;
  sessionId?: string;
  messages: Message[];
  language: Language;
  action?: QuickAction;
  selectionId?: string;
}
export interface ChatResponse {
  text: string;
  links?: ChatLink[];
  courses?: Course[];
  suggestions?: Suggestion[];
  supportForm?: { language: Language; question: string };
}
export interface MessageAdapter {
  send(request: ChatRequest, signal: AbortSignal): Promise<ChatResponse>;
}
