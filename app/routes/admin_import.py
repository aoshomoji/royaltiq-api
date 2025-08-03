from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class ArtistImportRequest(BaseModel):
    artist_id: str

@router.post("/admin/import")
async def import_artist_top_tracks(payload: ArtistImportRequest):
    artist_id = payload.artist_id

    # Step 1: Simulate fetching top tracks from Spotify
    # You would use Spotify API or mock logic here
    mock_tracks = [
        {
            "title": "Track A",
            "artist": "Mock Artist",
            "popularity": 72,
            "spotify_streams": 1500000,
            "youtube_views": 400000,
        },
        {
            "title": "Track B",
            "artist": "Mock Artist",
            "popularity": 65,
            "spotify_streams": 950000,
            "youtube_views": 220000,
        },
    ]

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    for track in mock_tracks:
        track["estimated_earnings"] = round(track["popularity"] * 5000)
        track["valuation_score"] = round((track["estimated_earnings"] / 100000) * 10, 2)

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/catalogs",
            headers=headers,
            json=track
        )

        if response.status_code >= 400:
            raise HTTPException(status_code=500, detail=f"Failed to import track: {track['title']}")

    return {"message": f"Imported {len(mock_tracks)} tracks for artist {artist_id}."}
