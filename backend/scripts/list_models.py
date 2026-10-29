import os
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

for m in client.models.list():
    if "flash" in m.name.lower():
        print(m.name)
