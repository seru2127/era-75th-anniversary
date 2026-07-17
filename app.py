from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import secrets
import string
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List
import csv
from io import StringIO, BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (images)
app.mount("/static", StaticFiles(directory="."), name="static")

# Serve HTML files at root
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return content

# Serve other HTML files
@app.get("/{filename}.html", response_class=HTMLResponse)
async def serve_html(filename: str):
    file_path = f"{filename}.html"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="Page not found")

# Serve image files directly
@app.get("/{filename}.png")
async def serve_png(filename: str):
    file_path = f"{filename}.png"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Image not found")

# ... rest of your API endpoints ...
