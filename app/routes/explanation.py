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
    Explain why the following music catalog received a valuation score of {data.valuation_score}:

    Title: {data.title}
    Artist: {data.artist}
    Genre: {data.genre}
    Spotify Streams: {data.spotify_streams}
    YouTube Views: {data.youtube_views}
    Earnings Last 12 Months: ${data.earnings_last_12mo}

    Mention performance across platforms, recent earnings, and risks or highlights that justify this valuation.
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

