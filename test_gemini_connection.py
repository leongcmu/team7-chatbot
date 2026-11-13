
"""Test Gemini connectivity independently of the Eduling agent."""

import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL")

print("API key found:", bool(api_key))
print("Configured model:", model)

if not api_key or not model:
    raise RuntimeError(
        "Missing GEMINI_API_KEY or GEMINI_MODEL in .env"
    )

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model=model,
        contents="Reply with exactly: CONNECTION_OK",
    )

    print("Gemini response:", response.text)

except Exception as exc:
    print("Gemini connection failed.")
    print("Error type:", type(exc).__name__)
    print("Error code:", getattr(exc, "code", "unknown"))
    print("Error message:", getattr(exc, "message", "unknown"))