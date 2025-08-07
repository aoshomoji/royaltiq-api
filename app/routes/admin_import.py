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

# ---------- simple heuristics ----------
def heuristic_earnings(popularity: int) -> int:
    """
    Example: popularity 0-100 → $ popularity × 1 000
    Refine later with real revenue model.
    """
    return popularity * 1_000

def heuristic_score(earnings: int) -> float:
    """
    Example valuation score 0-100 based on earnings.
    """
    return round(earnings / 10_000, 1)
# ---------------------------------------

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
        popularity = t["popularity"]            # 0-100
        earnings   = heuristic_earnings(popularity)

        rows.append({
            "track_id": t["id"],                      # Spotify track ID (text UUID-like)
            "title": t["name"],
            "artist": artist_name,
            "genre": primary_genre,
            "popularity": popularity,
            "spotify_streams": 0,               # Spotify public API hides counts
            "youtube_views": 0,
            "estimated_earnings": earnings,
            "valuation_score": heuristic_score(earnings),
            "user_id": user.id,                 # 🔑 tag owner for RLS
        })

    # 3) Upsert with conflict target (id, user_id)
    supabase.table("catalogs").upsert(
        rows,
        on_conflict="track_id,user_id"                # respects the UNIQUE constraint
    ).execute()

    return {"status": "ok", "inserted": len(rows)}
