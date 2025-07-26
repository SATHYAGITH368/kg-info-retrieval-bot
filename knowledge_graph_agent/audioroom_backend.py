from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from datetime import datetime, timedelta
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "APIdKmdjpJgVAL9"  # Use your actual LiveKit API key
API_SECRET = "KuLFbf70286ElY0hitWro2k6yEf7RWvgTaeND4KfvcaD"
LIVEKIT_HOST = "ag-ui-4rqnwaym.livekit.cloud"  # Just the host, no wss://

@app.get("/get-token")
def get_token(identity: str = None, room: str = "my-room"):
    if not identity:
        identity = f"user_{uuid.uuid4().hex[:8]}"

    expiration = datetime.utcnow() + timedelta(hours=1)

    payload = {
        "jti": str(uuid.uuid4()),
        "iss": API_KEY,
        "sub": identity,
        "nbf": int(datetime.utcnow().timestamp()),
        "exp": int(expiration.timestamp()),
        "video": {
            "roomJoin": True,
            "room": room
        }
    }

    # Generate JWT token
    token = jwt.encode(payload, API_SECRET, algorithm="HS256")

    return {"token": token, "identity": identity} what changes I have to make give final code after that
