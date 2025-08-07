import os
from fastapi import Header, HTTPException
from supabase import create_client, Client as SupabaseClient

SUPABASE_URL         = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_current_user(authorization: str = Header(...)):
    """
    Validate the Supabase JWT by asking Supabase itself.
    Returns a lightweight object with `.id` and `.email`.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.split(" ", 1)[1]
    user_resp = supabase.auth.get_user(token)   # Supabase checks signature & expiry

    if user_resp.error or not user_resp.user:
        raise HTTPException(status_code=401, detail="Invalid JWT")

    user = user_resp.user
    return type("AuthUser", (), dict(id=user.id, email=user.email))
