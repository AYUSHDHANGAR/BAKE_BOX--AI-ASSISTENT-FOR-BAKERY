import os
import time
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

models_to_test = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-flash-latest"
]

for m in models_to_test:
    t0 = time.time()
    try:
        res = client.models.generate_content(
            model=m,
            contents="Say 'Radhe Radhe!'"
        )
        print(f"Model {m}: {time.time()-t0:.2f}s -> {res.text.strip()}")
    except Exception as e:
        print(f"Model {m}: Error: {e}")
