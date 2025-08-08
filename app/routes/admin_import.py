from math import sqrt
from fastapi import APIRouter, Depends, HTTPException
from supabase import create_client
from ..deps.auth import get_current_user
from ..schemas import ImportRequest
from ..services.spotify import (
    fetch_top_tracks,
    fetch_artist_meta,
)
import os

router = APIRouter()

# Supabase service-role client (bypasses RLS for write, still adds user_id)
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"],
)

def est_streams(popularity: int) -> int:
    """Cubic mapping 0-100 → ~1M streams."""
    return int((popularity / 100) ** 3 * 1_000_000)

def est_earnings(streams: int) -> float:
    return round(streams * 0.0038, 2)          # USD

def valuation_score(earnings: float) -> float:
    return round(min(100, sqrt(earnings / 1_000) * 10), 1)

@router.post("/admin/import")
def import_tracks(req: ImportRequest, user=Depends(get_current_user)):
    """
    Import an artist’s top tracks from Spotify.
    Adds/updates rows in 'catalogs', one per (track_id, user_id).
    """
    # 1) Fetch from Spotify API
    try:
        tracks_raw  = fetch_top_tracks(req.artist_id)         # max 10
        artist_meta = fetch_artist_meta(req.artist_id)        # for genre + name
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Spotify fetch failed")

    primary_genre = (artist_meta.get("genres") or [None])[0]
    artist_name   = artist_meta.get("name", "Unknown Artist")

    # 2) Transform → Supabase rows
    rows = []
    for t in tracks_raw:
        popularity = t["popularity"]
        streams    = est_streams(popularity)
        earnings   = est_earnings(streams)

        rows.append({
            "track_id": t["id"],
            "title": t["name"],
            "artist": artist_name,
            "genre":  primary_genre,
            "popularity": popularity,
            "spotify_streams": streams,
            "youtube_views": 0,
            "estimated_earnings": earnings,
            "valuation_score": valuation_score(earnings),
            "user_id": user.id,
        })
    # 3) Upsert with conflict target (id, user_id)
    supabase.table("catalogs").upsert(
        rows,
        on_conflict="track_id,user_id"                # respects the UNIQUE constraint
    ).execute()

    return {"status": "ok", "inserted": len(rows)}
