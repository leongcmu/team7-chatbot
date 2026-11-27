# Eduling Assistant — VS Code / FastAPI handoff starter

## Purpose
A lightweight Gemini/LangChain **tool-calling agent** with six client-specific tools, deterministic commercial actions, curated Eduling content, and a FastAPI contract for the team's frontend. Built from the team's midpoint notebook. This is a **prototype**, not a security-audited production deployment.

## Architecture
`React → POST /chat → multilingual input guard → local embedding search → bounded approved evidence → Gemini agent ↔ six tools → evidence checks → verified actions → JSON`.

The backend converts approved FAQ/course/article text and each visitor question
into normalized MiniLM embedding vectors, then ranks records by cosine similarity.
Record vectors are built once per process and cached locally under `.model_cache/`.
Pending records remain in the index as rejection targets but cannot become approved
evidence. If the local model cannot load, the lexical retriever remains a degraded
fallback. Retrieval consumes no Gemini quota and sends no visitor text externally.

Before generation, the backend searches approved FAQ, course, and blog records
and adds relevant app/subscription facts deterministically. This bounded context
is merged with any evidence returned by agent tool calls, so a missed tool call
does not discard already-approved facts. Missing records never prove that a
course, feature, article, or commercial claim is unavailable.

After generation, validation checks factual product clauses against the actual
evidence rather than requiring broad word-for-word similarity. Course
availability, prices, commercial comparisons, and URLs retain dedicated strict
checks. Exact price and URL allowlists are built from approved knowledge-base
records rather than duplicated in code. For follow-up questions, relevant prior approved context may be reused,
while tool calls, tool failures, and tool evidence are scoped to the current turn.

## Run locally (Python 3.11 recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env      # Windows: copy .env.example .env
# Edit .env to add your Gemini API key and a model ID available to your account.
python scripts/validate_content.py
python -m scripts.evaluate_retrieval  # downloads/caches the embedding model once
pytest -q
uvicorn backend.main:app --reload
```

With FastAPI running, open another terminal from the repository root and run
the React frontend with Node 22.12+ and pnpm 11.25.0.

```bash
cd frontend/react
pnpm install --frozen-lockfile
pnpm build
pnpm dev
```

Open the URL printed by Vite, typically http://127.0.0.1:5173. Vite proxies
`/api/chat` to FastAPI at http://127.0.0.1:8000/chat. FastAPI docs are at
http://127.0.0.1:8000/docs. For deployment, route `/api/*` to FastAPI with the
`/api` prefix stripped, or set `VITE_CHAT_API_BASE_URL` before building and
add the frontend origin to FastAPI's `ALLOWED_ORIGINS`.

The original static demo is also available via `python -m http.server 5500 --directory frontend`.

## Knowledge-base records

- `data/faqs.json`: company, features, pricing, educator, support, IELTS/TOEFL,
  app, and social records.
- `data/courses.json`: course overview and course-difference records.
- `data/blog_posts.json`: approved article records (currently empty).
- `data/commercial.json`: verified app-store, shop, and commercial-policy data.

Only `approved` content can become answer evidence. Pending records are embedded
only so matching questions are recognized and safely rejected rather than being
misrouted to an unrelated approved record.

## API contract
POST `/chat`:
```json
{"message":"What IELTS courses do you have?","session_id":"visitor_example_123"}
```
Returns `answer`, `status`, `actions`, `related_articles`, `request_id`. Actions are typed `download_ios`, `download_android`, `subscribe_website`. Blog cards are limited to two verified articles. The `session_id` is a prototype identifier, not secure authentication.

## Client decisions
- Every course-related question: provide iOS and Android download links.
- Subscription action: explicit premium/purchase interest or a **verified** premium-only feature.
- Shop link: https://www.eduling.ai/shop . The client reports website subscriptions cost less, but comparison wording is **disabled** until plan scope is approved.
- Blog source: https://www.eduling.ai/news . `blog_posts.json` starts empty: add approved real article records before promising recommendations.
- English-answer chatbot with multilingual injection detection. Short answers;
  approved prices and links come only from the curated knowledge base.

## Important limitations before production
- Deterministic multilingual input rules do not guarantee that every prompt
  injection will be detected.
- The lexical retriever is only an offline/service-failure fallback. Its labeled
  baseline is intentionally retained for comparison with semantic selection.
- `InMemorySaver` is per-process and not persistent. Sessions can be lost on restart; session IDs are not authentication. Add retention limits, expiry, and isolation controls before public traffic.
- Apply upstream rate limits, request timeouts, token budgets, bounded concurrency, privacy-aware logging, and abuse monitoring before deployment.
- A floating Wix widget needs testing of iframe restrictions, mobile layout, and HTTPS/CORS.
- Never commit `.env`; use host secrets for deployment. Confirm model access and quota with your own key.
- A normal request uses one generation call. The agent may add a call only when a genuinely missing part requires
  a tool. `MAX_AGENT_STEPS` defaults to 4 as a graph bound, not a billing guarantee.
- `MODEL_MAX_RETRIES` defaults to 2 for transient Gemini failures.

For local troubleshooting, set `DIAGNOSTIC_LOGGING=true`. Server logs then include
tool names, approved evidence IDs/sources/scores, validation outcome, fallback reason,
pre-retrieval/tool-selection status, current-turn versus prior-context evidence,
and latency. Internal outcomes distinguish
no evidence, partial evidence, validation failure, and model/service failure.
Logs intentionally omit visitor messages, session IDs, prompts, and secrets.

## Test and presentation checklist
- `pytest -q` for offline retrieval, commercial-action, guardrail, and mocked API checks.
- `python -m scripts.evaluate_retrieval` evaluates local embedding search over the
  13 records plus three rewordings each; add `--lexical` to reproduce the spelling
  baseline. Current top-1 results are 50/52 (96.2%) for embeddings versus 37/52
  (71.2%) for the strict lexical baseline. The two remaining prompts are genuinely
  ambiguous between closely related approved records.
- `python -m scripts.compare_guardrails` collects the guarded/unguarded English,
  Chinese, and human-handoff comparison with public synthetic prompts.
- Run one real Gemini multi-tool question and capture tool names and evidence IDs privately.
- Evaluate factuality, blog relevance, action correctness, answer length, latency, and guarded vs. unguarded behavior.
- Compare the same questions against Wix. Document results, not only test plans.
- Follow [the demo runbook](docs/demo_runbook.md) and record the backup video before
  presentation day.
- Complete author bios/GitHub links, a recent research paper, responsible AI section, and real project board history for course submission.

## Source and attribution
Derived from `notebooks/Eduling_Midpoint_Agent_Prototype.ipynb` supplied by the project team. Frameworks: FastAPI, LangChain, LangGraph, Sentence Transformers, and Google Gemini API. No external tutorial code copied into this starter.
