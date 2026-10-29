import os
import time
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

models = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.8-flash"
]

for m in models:
    t0 = time.time()
    try:
        res = client.models.generate_content(
            model=m,
            contents="Say 'Radhe Radhe ji! Shri Ram Baker's BAKEBOX mein swagat hai!'"
        )
        print(f"Model {m}: {time.time()-t0:.2f}s -> {res.text.strip()}")
    except Exception as e:
        print(f"Model {m}: Error: {e}")
