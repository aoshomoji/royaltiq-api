from fastapi import APIRouter
from pydantic import BaseModel
import openai
import os
import requests
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

router = APIRouter()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class CatalogMetadata(BaseModel):
    id: str
    title: str
    artist: str
    genre: Optional[str] = None
    spotify_streams: Optional[int] = 0
    youtube_views: Optional[int] = 0
    earnings_last_12mo: Optional[float] = 0.0
    valuation_score: Optional[float] = 0.0

@router.post("/explanation")
async def explain_score(data: CatalogMetadata):
    prompt = f"""
    You are RoyaltIQ’s valuation assistant. Return a clear, investor-facing Markdown explanation **without any chit-chat**.

    Rules:
    • **Do NOT** start with words like “Certainly”, “Sure”, “Of course”, “Here’s”.
    • Begin immediately with the heading **Platform Performance** (or another relevant H2).
    • Use Markdown headings (##), bold for key numbers, and bullet lists.
    • Keep it under ~200 words unless the user data requires more detail.

    Data:
    - Title: {data.title}
    - Artist: {data.artist}
    - Valuation score: {data.valuation_score}
    - Streams (Spotify): {data.spotify_streams}
    - Views (YouTube): {data.youtube_views}
    - Earnings last 12 mo (USD): {data.earnings_last_12mo}

    """

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a music investment analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        explanation = response.choices[0].message.content.strip()

        # Save generated explanation back to Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }

        requests.patch(
            f"{supabase_url}/rest/v1/catalogs?id=eq.{data.id}",
            headers=headers,
            json={"explanation": explanation}
        )

        # Return the explanation explicitly
        return {"explanation": explanation}

    except Exception as e:
        return {"error": str(e)}

