from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import requests, os, uuid
from dotenv import load_dotenv
from deps.auth import get_current_user
load_dotenv()

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class ArtistImportRequest(BaseModel):
    artist_id: str

@router.post("/admin/import")
def import_tracks(payload: ArtistImportRequest, user = Depends(get_current_user)):
    artist_id = payload.artist_id

    mock_tracks = [
        {
            "id": str(uuid.uuid4()),
            "title": f"Track A ({artist_id[:6]})",
            "artist": "Mock Artist",
            "genre": "Pop",
            "popularity": 36,
            "spotify_streams": 1_500_000,
            "youtube_views": 400_000,
        },
        {
            "id": str(uuid.uuid4()),
            "title": f"Track B ({artist_id[:6]})",
            "artist": "Mock Artist",
            "genre": "Pop",
            "popularity": 42,
            "spotify_streams": 2_100_000,
            "youtube_views": 600_000,
        },
    ]

    for track in mock_tracks:
        track["estimated_earnings"] = round(track["popularity"] * 5_000)
        track["valuation_score"]   = round((track["estimated_earnings"] / 100_000) * 10, 2)
        track["user_id"]           = user.id

    headers = {
        "apikey": SERVICE_ROLE,
        "Authorization": f"Bearer {SERVICE_ROLE}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }

    for track in mock_tracks:
        resp = requests.post(f"{SUPABASE_URL}/rest/v1/catalogs", headers=headers, json=track)
        if resp.status_code >= 400:
            raise HTTPException(status_code=500, detail=f"Failed to import track {track['title']}")

    return {"message": f"Imported {len(mock_tracks)} tracks for artist {artist_id}."}
