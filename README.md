# Eduling Assistant — VS Code / FastAPI handoff starter

> **Confidentiality:** Client identity and branding require permission before publication in a public repository. Keep this repository private until approved.

## Purpose
A lightweight Gemini/LangChain **tool-calling agent** with six client-specific tools, deterministic commercial actions, curated Eduling content, and a FastAPI contract for the team's frontend. Built from the team's midpoint notebook. This is a **prototype**, not a security-audited production deployment.

## Architecture
`HTML/CSS/JS → POST /chat → input guard → bounded approved evidence → Gemini agent ↔ six tools → evidence checks → verified actions → JSON`.

The backend uses Python fuzzy/keyword retrieval, not a local embedding model or vector database. JSON files are manually curated. The LLM is accessed through the Gemini API, so no large generative model runs on the server.

Before generation, the backend searches approved FAQ, course, and blog records
and adds relevant app/subscription facts deterministically. This bounded context
is merged with any evidence returned by agent tool calls, so a missed tool call
does not discard already-approved facts. Missing records never prove that a
course, feature, article, or commercial claim is unavailable.

After generation, validation checks factual product clauses against the actual
evidence rather than requiring broad word-for-word similarity. Course
availability, prices, commercial comparisons, and URLs retain dedicated strict
checks. For follow-up questions, relevant prior approved context may be reused,
while tool calls, tool failures, and tool evidence are scoped to the current turn.

## Run locally (Python 3.11 recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env      # Windows: copy .env.example .env
# Edit .env to add your Gemini API key and a model ID available to your account.
python scripts/validate_content.py
pytest -q
uvicorn backend.main:app --reload
```

API docs: http://127.0.0.1:8000/docs . Frontend: from `frontend/`, run `python -m http.server 5500`, then open http://localhost:5500 .

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
- English-only chatbot. Short answers, no hardcoded price amounts.

## Important limitations before production
- Current lexical guardrails do not guarantee semantic grounding or stop all prompt injection.
- Fuzzy thresholds are provisional and must be calibrated against labeled questions.
- `InMemorySaver` is per-process and not persistent. Sessions can be lost on restart; session IDs are not authentication. Add retention limits, expiry, and isolation controls before public traffic.
- Apply upstream rate limits, request timeouts, token budgets, bounded concurrency, privacy-aware logging, and abuse monitoring before deployment.
- A floating Wix widget needs testing of iframe restrictions, mobile layout, and HTTPS/CORS.
- Never commit `.env`; use host secrets for deployment. Confirm model access and quota with your own key.
- `MAX_AGENT_STEPS` is a graph recursion bound, not a strict number of billable model calls.

For local troubleshooting, set `DIAGNOSTIC_LOGGING=true`. Server logs then include
tool names, approved evidence IDs/sources/scores, validation outcome, fallback reason,
pre-retrieval/tool-selection status, current-turn versus prior-context evidence,
and latency. Internal outcomes distinguish
no evidence, partial evidence, validation failure, and model/service failure.
Logs intentionally omit visitor messages, session IDs, prompts, and secrets.

## Test and presentation checklist
- `pytest -q` for offline retrieval, commercial-action, guardrail, and mocked API checks.
- Run one real Gemini multi-tool question and capture tool names and evidence IDs privately.
- Evaluate factuality, blog relevance, action correctness, answer length, latency, and guarded vs. unguarded behavior.
- Compare the same questions against Wix. Document results, not only test plans.
- Complete author bios/GitHub links, a recent research paper, responsible AI section, and real project board history for course submission.

## Source and attribution
Derived from `notebooks/Eduling_Midpoint_Agent_Prototype.ipynb` supplied by the project team. Frameworks: FastAPI, LangChain, LangGraph, Google Gemini API. No external tutorial code copied into this starter.
