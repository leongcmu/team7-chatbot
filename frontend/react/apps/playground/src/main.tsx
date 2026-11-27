import React from "react";
import { PlaygroundPage } from "./pages/PlaygroundPage";
import { createRoot } from "react-dom/client";
import { EdulingChatbot } from "@eduling/chatbot";
import "@eduling/chatbot/styles.css";
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <PlaygroundPage />
    <EdulingChatbot
      apiBaseUrl={import.meta.env.VITE_CHAT_API_BASE_URL || "/api"}
      storageKey="eduling-chatbot:live:v1"
      defaultOpen
    />
  </React.StrictMode>,
);
