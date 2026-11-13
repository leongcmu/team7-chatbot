# Eduling content-maintenance workflow

## Purpose
Help a maintainer update public Eduling FAQ, course, blog and commercial records safely.

## When to use
Whenever the client approves a new article, changes app links, or changes subscription terms.

## Steps
1. Confirm the information with an authorized Eduling contact and record the source.
2. Update the appropriate JSON under `data/`. Keep record IDs stable.
3. Set `status` to `approved` only after review; otherwise keep pending.
4. For blog posts, include a real direct article URL, a short factual summary, and topic tags.
5. For premium-only claims, record explicit client approval before enabling recommendations.
6. Run `python scripts/validate_content.py` and `pytest -q`.
7. Review the resulting diff and obtain client sign-off before deployment.
8. Record the review date and owner in the project board.

## Safety
Never insert private learner data, payment details, API keys, or unverified prices.
