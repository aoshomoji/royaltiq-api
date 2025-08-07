from fastapi import Depends, HTTPException, status, Header
import jwt, os

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

def get_current_user(authorization: str = Header(...)):
    """
    Extracts and validates the Supabase JWT.
    Returns a simple object with `.id`, `.email`.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        return type("AuthUser", (), dict(id=payload["sub"], email=payload.get("email")))
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid JWT")
