from google import genai
from config.settings import GEMINI_API_KEY

client = genai.Client(
    api_key=GEMINI_API_KEY
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain deadlock in operating systems."
)

print(response.text)