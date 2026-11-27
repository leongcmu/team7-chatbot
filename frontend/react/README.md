# Eduling React Chatbot

A pnpm monorepo containing an importable React + TypeScript widget. **No Eduling website recreation.** `apps/playground` is a deliberately minimal component preview, not a website demo.

## Run

Node >=22.12, pnpm 11.25.0 (Corepack can activate the packageManager version).

```sh
pnpm install --frozen-lockfile
pnpm typecheck
pnpm build
pnpm test
pnpm dev
```

Start FastAPI using the [repository setup](../../README.md#run-locally-python-311-recommended), then open the Vite URL printed by `pnpm dev`. Build the library before running the playground; it consumes the package's public dist exports, not a source alias.

## Layout

- `packages/contracts`: shared message, course, request/response and adapter types; no React dependency.
- `packages/mocks`: centralized fixtures, scripted scenarios and mock adapter; no UI imports.
- `packages/chatbot`: `@eduling/chatbot`, React and React DOM as peers (18.2 or 19).
- `apps/playground`: independent widget test surface only.
- `dist/index.js`, `dist/index.d.ts`, `dist/chatbot.css`: ESM, public type declarations, CSS with bundled fonts. SVG icons are bundled as data URLs. No remote font or asset requests.

## Integrate into a React host

For a host in this workspace, add `"@eduling/chatbot": "workspace:*"`. For a separate repository, build and pack:

```sh
pnpm build
pnpm --filter @eduling/contracts pack
pnpm --filter @eduling/mocks pack
pnpm --filter @eduling/chatbot pack
# In the host repository, install all three generated tarballs together.
```

Mount one instance in the persistent app layout:

```tsx
'use client';
import { EdulingChatbot } from '@eduling/chatbot';
import '@eduling/chatbot/styles.css';

export function Assistant() {
  return <EdulingChatbot apiBaseUrl="/api" storageKey="eduling-chat:v1" />;
}
```

For Next.js, put this wrapper in a Client Component and import the stylesheet from the root layout if your version requires global styles there. The package performs no browser-storage access during server rendering. Keep the widget outside route-remounted content where possible.

The playground connects to FastAPI through Vite's `/api` proxy. The widget
appends `/chat` to `apiBaseUrl`. Without an API base URL or explicit adapter,
the reusable widget runs with local scripted fixtures.

### Public API

| Prop | Default / behavior |
| --- | --- |
| `adapter?: MessageAdapter` | Overrides the configured transport |
| `apiBaseUrl?: string` | Base URL for the FastAPI adapter |
| `defaultOpen?: boolean` | false; otherwise starts on welcome/restored conversation |
| `storageKey?: string \| false` | `eduling-chatbot:v1`; false disables persistence |
| `onOpenChange?(open)` | Observes launcher/close/Escape |
| `onCourseClick?(course)` | Observes valid HTTP(S) non-mock course links |
| `style?: CSSProperties` | Scoped CSS custom properties, e.g. `--eduling-z-index` |

```tsx
import { createMockAdapter, type MessageAdapter } from '@eduling/chatbot';
const adapter = createMockAdapter({ delayMs: 500, failOnce: true });
// Use this stable instance to preview loading/error/retry.
<EdulingChatbot adapter={adapter} />;
```

An adapter implements `send(request, signal): Promise<ChatResponse>`. Requests carry a stable `requestId` reused on retry, history, English as the request language and optional quick-action intent. Implementations must honor AbortSignal and return structured text/cards/suggestions; no HTML is rendered. Types are exported from the package root.

### Styling and accessibility

All rules are scoped beneath `.eduling-chatbot`; no body/reset or host element styles are installed. Internal form controls explicitly set typography. Prefixing prevents outgoing style leakage, but this is not Shadow DOM: aggressive host `!important` rules can still override the component. Variables: `--eduling-brand`, `--eduling-action`, `--eduling-ink`, `--eduling-muted`, `--eduling-border`, `--eduling-surface`, `--eduling-z-index`. Mount outside transformed/overflow-clipped ancestors for fixed positioning. CSP hosts must allow `font-src data:` and `img-src data:` for the bundled fonts and icons.

The panel is a non-modal dialog. It focuses the composer when opened, restores focus to the launcher on close, closes on Escape, and provides labeled controls and live status/error announcements. Enter sends; Shift+Enter adds a line; IME composition is respected. Empty messages cannot be sent. The limit is 1,500 characters for FastAPI and 2,000 for the mock. Mobile uses dynamic viewport height and a scrollable message area; check virtual-keyboard behavior on target devices before production integration.

### Session policy

Session storage is confined to the current origin and browser tab, with a 24-hour maximum age since the last saved change, a 100-message persisted limit and a versioned schema. Refresh and same-origin route changes restore history. Recommendation goal/level selections remain in the transcript. New conversation aborts pending replies and overwrites the stored transcript with an empty one. Blocked/full/malformed storage degrades to in-memory chat. Cross-origin pages, cross-device history and account synchronization are excluded. This is a prototype policy, pending Linh's final retention decision.


## Design and scope

Source: [Figma](https://www.figma.com/design/jcrQXfKiR0VoArJZYV5PAX/Eduling-AI-%E2%80%94-Chatbot-MVP?node-id=4-350). Read welcome `4:10`, course `4:118`, header `3:44`, launcher `21:2959`, and support fallback `4:350`. Uses Nunito, cyan #49BFDA, action #087D94, pale surface #F0F9FB, rounded 24px shell and Figma SVG assets. Desktop target is 420×820, capped to viewport; expand fills the available viewport. The welcome screen shows Explore Eduling, Find my course, and Browse courses.

Implemented: launcher, welcome, conversation, three actions, guided mock goal/CEFR flow, sample cards, English interface copy, loading/retry, expand/restore/close, session reset and responsive layout.



### Continuous home and conversation

The welcome heading and three quick actions stay at the top of the same scrollable conversation area after sending text or selecting a module. Messages append below them; only the chat area scrolls to the latest reply. Scroll upward to revisit the welcome/actions and earlier messages without clearing the conversation or navigating.


## Architecture and extension boundaries

```text
apps/playground/src/pages/       Preview pages (never a simulated Eduling website)
packages/contracts/src/          Shared transport/domain types, no React or browser code
packages/mocks/src/fixtures/     All simulated courses, dialogue and language examples
packages/mocks/src/scenarios/    Scripted scenario rules consuming contracts + fixtures
packages/mocks/src/mockAdapter.ts  Mock delay/failure/cancellation boundary
packages/chatbot/src/components/  Header, Welcome, MessageList, CourseCard, Composer
packages/chatbot/src/hooks/      Conversation state, send/retry/reset and scrolling
packages/chatbot/src/adapters/   Transport interface and FastAPI adapter
packages/chatbot/src/config/     Product quick-action identifiers, independent of mock data
packages/chatbot/src/storage/    Browser session storage and validation
packages/chatbot/src/i18n/       English interface copy
packages/chatbot/src/styles/     Scoped widget styling
```

Dependency direction: `contracts ← mocks ← chatbot ← playground`, with chatbot also consuming contracts directly. The widget retains its default mock adapter and `createMockAdapter` re-export for compatibility. Mock scenarios never import UI translations. User-facing interface copy belong in `chatbot/i18n`, while simulated assistant reply content belongs in `mocks/fixtures`. `Suggestion.id` is optional for legacy custom adapters; current goal/level options carry stable IDs via `ChatRequest.selectionId`, so the scripted flow does not depend on the language of the current interface. Legacy text inputs remain supported.

`EdulingChatbot.tsx` composes UI; `useConversation` owns request cancellation, retry request IDs, history and storage lifecycle. Child components render the data they receive and do not call models or load catalog data. The welcome/actions and message list still share one scroll container.

The FastAPI adapter sends the latest user message and the conversation's session
ID. Follow-up turns reuse that ID, and starting a new conversation rotates it.
The widget renders backend answer text, verified action links and related articles.
Provider credentials stay in the backend. FastAPI controls the language of
generated answers independently of the widget's interface language.

### Mock support fallback

Free-text questions outside the scripted course/language flows now return a support fallback card with Name, Email, Message and Submit. A student-discount question uses the matching discount explanation; other questions use a generic unverified-answer explanation. The form pre-fills the question, uses required fields and browser email validation, and shows an explicit local-only completion message. No API, email, support ticket or storage of contact details is involved. Form values live only in the mounted component; the transcript stores the support-card descriptor and original question, so refreshing restores an unsubmitted form.
