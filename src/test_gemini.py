import os

from dotenv import load_dotenv
from google import genai

# Load variables from .env
load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Check your .env file."
    )

print("Gemini API key loaded successfully.")
print("Key length:", len(api_key))

# Create Gemini client
client = genai.Client(api_key=api_key)

# Simple connection test
response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Reply with exactly: NetSage AI connection successful."
)

print(response.text)