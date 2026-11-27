import React from "react";
import { afterEach, describe, it, expect, vi } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { EdulingChatbot } from "./EdulingChatbot";
import { createMockAdapter } from "@eduling/mocks";
import { loadSession, RETENTION_MS } from "./storage/session";
afterEach(() => {
  cleanup();
  sessionStorage.clear();
  vi.restoreAllMocks();
});
describe("Phase 1 widget", () => {
  it("opens, has exactly three actions, expands and closes without losing chat", async () => {
    render(<EdulingChatbot adapter={createMockAdapter({ delayMs: 0 })} />);
    fireEvent.click(screen.getByRole("button", { name: "Ask Eduling AI" }));
    expect(document.querySelectorAll(".eduling-actions button")).toHaveLength(
      3,
    );
    fireEvent.click(screen.getByRole("button", { name: /Find my course/i }));
    await screen.findByText("What would you like to improve?");
    fireEvent.click(
      screen.getByRole("button", { name: "Speaking & conversation" }),
    );
    await screen.findByText("What’s your English level?");
    fireEvent.click(screen.getByRole("button", { name: "B1" }));
    await screen.findByText("Chat with EdulingAI — sample");
    fireEvent.click(screen.getByRole("button", { name: "Expand chat" }));
    expect(document.querySelector(".eduling-expanded")).not.toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Close chat" }));
    fireEvent.click(screen.getByRole("button", { name: "Ask Eduling AI" }));
    expect(screen.getByText("Chat with EdulingAI — sample")).toBeDefined();
  });
  it("keeps welcome and module controls above free-text conversation in the same scroll area", async () => {
    render(
      <EdulingChatbot
        defaultOpen
        adapter={createMockAdapter({ delayMs: 0 })}
      />,
    );
    const welcome = document.querySelector(".eduling-welcome");
    const scrollArea = document.querySelector(".eduling-messages");
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "hello" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await screen.findByText(/I couldn’t verify an answer/);
    expect(document.querySelector(".eduling-welcome")).toBe(welcome);
    expect(welcome?.parentElement).toBe(scrollArea);
    expect(screen.getByRole("log").parentElement).toBe(scrollArea);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toContain(
      "A little guidance.",
    );
    expect(document.querySelectorAll(".eduling-actions button")).toHaveLength(
      3,
    );
    fireEvent.click(screen.getByRole("button", { name: /Browse courses/i }));
    await screen.findByText("Chat with EdulingAI — sample");
    expect(document.querySelectorAll(".eduling-user")).toHaveLength(2);
    expect(screen.getByText("hello", {selector:"p"})).toBeDefined();
    expect(document.querySelector(".eduling-welcome")).toBe(welcome);
  });
  it("restores legacy conversations with the English UI and can reset", () => {
    sessionStorage.setItem("eduling-chatbot:v1", JSON.stringify({
      version: 1,
      updatedAt: Date.now(),
      mode: "zh",
      language: "zh",
      messages: [{ id: "saved", role: "assistant", text: "Saved reply" }],
    }));
    render(<EdulingChatbot defaultOpen />);
    expect(screen.queryByRole("combobox")).toBeNull();
    expect(screen.getByText("Saved reply")).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "New conversation" }));
    expect(screen.queryByText("Saved reply")).toBeNull();
  });
  it("retries the same request without duplicating the user message", async () => {
    const base = createMockAdapter({ delayMs: 0, failOnce: true });
    const send = vi.fn(base.send);
    render(
      <EdulingChatbot defaultOpen adapter={{ send }} storageKey={false} />,
    );
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "hello" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));
    await screen.findByRole("alert");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(send).toHaveBeenCalledTimes(2));
    await screen.findByText(/I couldn’t verify an answer/);
    expect(send.mock.calls[0][0].requestId).toBe(
      send.mock.calls[1][0].requestId,
    );
    expect(document.querySelectorAll(".eduling-user")).toHaveLength(1);
  });
  it("reset aborts an in-flight reply so it cannot reappear", async () => {
    let resolve!: (value: { text: string }) => void;
    render(
      <EdulingChatbot
        defaultOpen
        adapter={{
          send: () =>
            new Promise((r) => {
              resolve = r;
            }),
        }}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Explore Eduling/ }));
    fireEvent.click(screen.getByRole("button", { name: "New conversation" }));
    resolve({ text: "stale reply" });
    await new Promise((r) => setTimeout(r, 0));
    expect(screen.queryByText("stale reply")).toBeNull();
    expect(document.querySelectorAll(".eduling-actions button")).toHaveLength(
      3,
    );
  });
  it("rejects messages longer than the FastAPI limit", () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    render(<EdulingChatbot defaultOpen apiBaseUrl="https://example.com" />);
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "x".repeat(1501) },
    });
    expect(screen.getByRole("alert").textContent).toContain("1,500");
    expect(
      (
        screen.getByRole("button", {
          name: "Send message",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(fetch).not.toHaveBeenCalled();
    fetch.mockRestore();
  });
  it("sends chat to FastAPI, renders links, and rotates the session on reset", async () => {
    const fetch = vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      Response.json({
        answer: "Here are some options.\n* **Test preparation**\n* General English\n\nContact info@eduling.org for help.",
        status: "answered",
        actions: [
          { type: "download_ios", label: "iPhone", url: "https://apps.apple.com/example" },
          { type: "download_android", label: "Android", url: "https://play.google.com/example" },
          { type: "subscribe_website", label: "View website subscriptions", url: "https://www.eduling.ai/shop" },
        ],
        related_articles: [{
          title: "Course overview",
          url: "https://example.com/courses",
          summary: "An introduction to the courses.",
        }],
      }),
    );
    render(<EdulingChatbot defaultOpen apiBaseUrl="/api" />);

    async function send(message: string) {
      fireEvent.change(screen.getByRole("textbox"), { target: { value: message } });
      fireEvent.click(screen.getByRole("button", { name: "Send message" }));
      await waitFor(() => expect(screen.queryByRole("status")).toBeNull());
      const [url, init] = fetch.mock.calls.at(-1)!;
      expect(url).toBe("/api/chat");
      expect(init?.method).toBe("POST");
      const body = JSON.parse(String(init?.body));
      expect(body.message).toBe(message);
      return body.session_id;
    }

    const first = await send("What courses do you offer?");
    expect(first).toMatch(/^[A-Za-z0-9_-]{12,128}$/);
    expect(screen.getByText("Here are some options.")).toBeDefined();
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(screen.getByText("Test preparation").tagName).toBe("STRONG");
    expect(screen.getByRole("link", { name: "info@eduling.org" }).getAttribute("href"))
      .toBe("mailto:info@eduling.org");
    const subscription = screen.getByRole("link", { name: "View website subscriptions" });
    expect(subscription.classList.contains("eduling-subscription")).toBe(true);
    expect(subscription.getAttribute("href")).toBe("https://www.eduling.ai/shop");
    expect(screen.getByText("Eduling: Language Courses")).toBeDefined();
    expect(screen.getByRole("link", { name: "Download on the App Store" }).getAttribute("href"))
      .toBe("https://apps.apple.com/example");
    expect(screen.getByRole("link", { name: "Get it on Google Play" }).getAttribute("href"))
      .toBe("https://play.google.com/example");
    expect(screen.getByRole("link", { name: "Course overview" })).toBeDefined();
    expect(await send("What about speaking?")).toBe(first);
    fireEvent.click(screen.getByRole("button", { name: "New conversation" }));
    expect(await send("How do I get started?")).not.toBe(first);
  });
  it("discards expired and malformed storage", () => {
    sessionStorage.setItem(
      "test",
      JSON.stringify({
        version: 1,
        updatedAt: Date.now() - RETENTION_MS - 1,
        messages: [],
      }),
    );
    expect(loadSession("test")).toBeUndefined();
    expect(sessionStorage.getItem("test")).toBeNull();
    sessionStorage.setItem("test", "broken");
    expect(loadSession("test")).toBeUndefined();
  });
});

it("renders a support fallback form for free text and simulates submission locally", async () => {
  const fetch = vi.spyOn(globalThis, "fetch");
  render(
    <EdulingChatbot defaultOpen adapter={createMockAdapter({ delayMs: 0 })} />,
  );
  fireEvent.change(screen.getByRole("textbox"), {
    target: { value: "Is there a student discount?" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send message" }));
  await screen.findByText(/I couldn’t verify a current student discount/);
  expect(screen.getByLabelText("Message").getAttribute("name")).toBe("message");
  fireEvent.change(screen.getByLabelText("Name"), {
    target: { value: "Test Learner" },
  });
  fireEvent.change(screen.getByLabelText("Email"), {
    target: { value: "test@example.com" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Submit", exact: true }));
  await screen.findByText(
    "Mock submission complete. Nothing was sent to Eduling support.",
  );
  expect(fetch).not.toHaveBeenCalled();
  expect(sessionStorage.getItem("eduling-chatbot:v1")).not.toContain(
    "test@example.com",
  );
  fetch.mockRestore();
});

 it('keeps Explore Eduling separate from the free-text support fallback',async()=>{
 render(<EdulingChatbot defaultOpen adapter={createMockAdapter({delayMs:0})}/>);
 fireEvent.click(screen.getByRole('button',{name:/Explore Eduling/}));
 await screen.findByText('This is a mock preview. I cannot verify Eduling information or prices. No live support request has been submitted.');
 expect(screen.queryByRole('button',{name:'Submit',exact:true})).toBeNull();
 });
