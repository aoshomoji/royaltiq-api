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

@router.post("/summary")
async def summarize_catalog(data: CatalogMetadata):
    prompt = f"""
    Write a concise, investor-friendly summary of the catalog **without any pre-amble**.
    Return Markdown. Sections:

    1. **Artist & Style** – one sentence.
    2. **Catalog Performance** – bullet list of key metrics.
    3. **Investment Potential** – 1-2 sentences.

    Use the data below. Avoid phrases like “Sure”, “Here is”, etc.

    Data:
    - Title: {data.title}
    - Artist: {data.artist}
    - Genre: {data.genre}
    - Spotify streams: {data.spotify_streams}
    - YouTube views: {data.youtube_views}
    - Earnings last 12 mo (USD): {data.earnings_last_12mo}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are an investment analyst for music catalogs."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        summary = response.choices[0].message.content.strip()

        # Save generated summary back to Supabase
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
            json={"summary": summary}
        )

        # Return the summary explicitly
        return {"summary": summary}

    except Exception as e:
        return {"error": str(e)}

