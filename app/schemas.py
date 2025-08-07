from pydantic import BaseModel, Field

class ImportRequest(BaseModel):
    artist_id: str = Field(..., example="3TVXtAsR1Inumwj472S9r4")
