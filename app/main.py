from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import summarize, explain

app = FastAPI()

# Allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Or restrict to ["POST"]
    allow_headers=["*"],  # Or restrict to ["Content-Type"]
)

app.include_router(summarize.router)
app.include_router(explain.router)
