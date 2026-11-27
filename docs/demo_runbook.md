# Dec. 3 demo runbook

## Before recording

1. Copy `.env.example` to `.env`, set a working Gemini key/model, and keep the
   file uncommitted.
2. Run `python scripts/validate_content.py` and `python -m pytest -q`.
3. Run `python -m scripts.evaluate_retrieval --output embedding-evaluation.json`.
   The 52 prompts use the cached local embedding model and consume no API quota.
4. Run `python -m scripts.compare_guardrails > guardrail-comparison.jsonl` to save the
   guarded-versus-unguarded slide.
5. Start FastAPI and the static frontend, then confirm the health endpoint.

## Backup video shot list

Record one continuous working run showing:

1. “Do you have IELTS prep?” returning the approved IELTS/TOEFL answer and both
   verified app actions.
2. “Can I talk to a real person?” returning the approved support route.
3. A Chinese instruction-override attempt being blocked.
4. A made-up course request falling back without claiming the course is absent.
5. Server diagnostics showing call path, evidence IDs, latency, and validation
   outcome without displaying visitor text, session IDs, or secrets.

Keep the video locally and test playback from the presentation laptop. Do not
record `.env`, the API key, browser developer storage, or private client data.
