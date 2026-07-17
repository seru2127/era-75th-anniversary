from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# CORS
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
    return {"message": "API is running"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.post("/api/login")
def login(data: LoginRequest):
    print(f"Login attempt: {data.username} / {data.password}")
    
    if data.username == "admin" and data.password == "Seruera75":
        return {"success": True, "message": "Login successful", "token": "test-token-123"}
    else:
        return {"success": False, "message": "Invalid credentials"}

@app.get("/api/guests")
def get_guests():
    return [{"guest_id": "TEST-001", "full_name": "Test User"}]
