import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def main():
    groq_key = os.getenv("GROQ_API_KEY")
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {"Authorization": f"Bearer {groq_key}"}
        res = await client.get("https://api.groq.com/openai/v1/models", headers=headers)
        if res.status_code == 200:
            models = [m["id"] for m in res.json().get("data", [])]
            print("Available Groq Models:", models)
        else:
            print("Groq models error:", res.status_code, res.text)

if __name__ == "__main__":
    asyncio.run(main())
