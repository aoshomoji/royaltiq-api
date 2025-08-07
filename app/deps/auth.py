import os
from fastapi import Header, HTTPException
from supabase import create_client

SUPABASE_URL            = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE   = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.split(" ", 1)[1]

    # Supabase validates the JWT; v2 SDK returns .user or None
    user_resp = supabase.auth.get_user(token)
    user = getattr(user_resp, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid JWT")

    return type("AuthUser", (), dict(id=user.id, email=getattr(user, "email", None)))

