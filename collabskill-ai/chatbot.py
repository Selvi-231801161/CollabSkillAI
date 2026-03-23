import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("API key not found. Check your .env file.")

client = OpenAI(api_key=api_key)

def ask_bot(user_input):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for a skill exchange platform."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content
