from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import secrets

app = FastAPI()

# CORS - Allow everything
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/")
def root():
    return {"message": "ERA 75th API is running"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.post("/api/login")
def login(data: LoginRequest):
    print(f"🔐 Login attempt: username='{data.username}', password='{data.password}'")
    
    # Hardcoded check - case sensitive
    if data.username == "admin" and data.password == "Seruera75":
        token = secrets.token_urlsafe(32)
        print(f"✅ Login successful for {data.username}")
        return {
            "success": True,
            "message": "Login successful",
            "token": token
        }
    else:
        print(f"❌ Login failed for {data.username}")
        return {
            "success": False,
            "message": "Invalid credentials"
        }

@app.get("/api/guests")
def get_guests():
    return [{"guest_id": "TEST-001", "full_name": "Test User"}]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
