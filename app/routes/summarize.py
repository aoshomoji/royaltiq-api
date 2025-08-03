from fastapi import APIRouter
from pydantic import BaseModel
import openai
import os
import requests
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class CatalogMetadata(BaseModel):
    id: str
    title: str
    artist: str
    genre: str
    spotify_streams: int
    youtube_views: int
    earnings_last_12mo: float

@router.post("/summarize")
async def summarize_catalog(data: CatalogMetadata):
    prompt = f"""
    Summarize this music catalog clearly for a potential investor:

    Title: {data.title}
    Artist: {data.artist}
    Genre: {data.genre}
    Spotify Streams: {data.spotify_streams}
    YouTube Views: {data.youtube_views}
    Earnings Last 12 Months: ${data.earnings_last_12mo}

    Provide a concise summary of the artist’s style, catalog performance, and investment potential.
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

