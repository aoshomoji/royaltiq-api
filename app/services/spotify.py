import os, time, requests

TOKEN_URL   = "https://accounts.spotify.com/api/token"
TOP_URL     = "https://api.spotify.com/v1/artists/{id}/top-tracks?market=US"
ARTIST_URL = "https://api.spotify.com/v1/artists/{id}"

CLIENT_ID     = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]

_token_cache: dict[str, str | int] = {"access_token": "", "expires": 0}

def _get_app_token() -> str:
    # cached & refreshed automatically
    now = int(time.time())
    if _token_cache["expires"] > now + 60:
        return _token_cache["access_token"]

    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=10,
    ).json()

    _token_cache["access_token"] = resp["access_token"]
    _token_cache["expires"] = now + resp["expires_in"]
    return _token_cache["access_token"]

def fetch_top_tracks(artist_id: str, limit: int = 10) -> list[dict]:
    token = _get_app_token()
    r = requests.get(
        TOP_URL.format(id=artist_id),
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if r.status_code == 404:
        raise ValueError("Artist not found")
    if r.status_code == 429:
        raise ValueError("Rate limited by Spotify; try again later")
    r.raise_for_status()

    return r.json()["tracks"][:limit]

def fetch_artist_meta(artist_id: str) -> dict:
    token = _get_app_token()
    r = requests.get(ARTIST_URL.format(id=artist_id),
                     headers={"Authorization": f"Bearer {token}"},
                     timeout=10)
    r.raise_for_status()
    return r.json()        # contains 'genres': [...]
