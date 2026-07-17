from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import sqlite3
import secrets
import string
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List
import csv
from io import StringIO

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
def get_db():
    conn = sqlite3.connect('registrations.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    # Main registrations table - without extra fields
    conn.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_id TEXT UNIQUE,
            full_name TEXT,
            gender TEXT,
            phone TEXT,
            email TEXT UNIQUE,
            organization TEXT,
            job_title TEXT,
            city TEXT,
            category TEXT,
            registered_at TIMESTAMP,
            checked_in INTEGER DEFAULT 0,
            checked_in_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def generate_guest_id():
    prefix = "ERA75"
    suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"{prefix}-{suffix}"

# Models
class RegistrationCreate(BaseModel):
    full_name: str
    gender: str
    phone: str
    email: str
    organization: Optional[str] = None
    job_title: Optional[str] = None
    city: Optional[str] = None
    category: str

# Root endpoint
@app.get("/")
def root():
    return {"message": "ERA 75th Anniversary API", "status": "running"}

# Health check
@app.get("/api/health")
def health():
    return {"status": "healthy", "database": "connected"}

# Register endpoint
@app.post("/api/register")
def register(data: RegistrationCreate):
    try:
        conn = get_db()
        
        # Check if email exists
        existing = conn.execute("SELECT * FROM registrations WHERE email = ?", (data.email,)).fetchone()
        if existing:
            conn.close()
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Generate guest ID
        guest_id = generate_guest_id()
        
        # Insert into database
        conn.execute('''
            INSERT INTO registrations 
            (guest_id, full_name, gender, phone, email, organization, job_title, city, category, registered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (guest_id, data.full_name, data.gender, data.phone, data.email, 
              data.organization, data.job_title, data.city, data.category, datetime.now()))
        conn.commit()
        conn.close()
        
        return {
            "guest_id": guest_id,
            "full_name": data.full_name,
            "email": data.email,
            "category": data.category,
            "message": "Registration successful"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get all guests
@app.get("/api/guests")
def get_guests():
    try:
        conn = get_db()
        guests = conn.execute("SELECT * FROM registrations ORDER BY registered_at DESC").fetchall()
        conn.close()
        return [dict(row) for row in guests]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get specific guest
@app.get("/api/guest/{guest_id}")
def get_guest(guest_id: str):
    try:
        conn = get_db()
        guest = conn.execute("SELECT * FROM registrations WHERE guest_id = ?", (guest_id,)).fetchone()
        conn.close()
        if not guest:
            raise HTTPException(status_code=404, detail="Guest not found")
        return dict(guest)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Check-in endpoint
@app.post("/api/checkin/{guest_id}")
def check_in(guest_id: str):
    try:
        conn = get_db()
        guest = conn.execute("SELECT * FROM registrations WHERE guest_id = ?", (guest_id,)).fetchone()
        if not guest:
            conn.close()
            raise HTTPException(status_code=404, detail="Guest not found")
        
        if guest['checked_in'] == 1:
            conn.close()
            raise HTTPException(status_code=400, detail="Guest already checked in")
        
        conn.execute('''
            UPDATE registrations 
            SET checked_in = 1, checked_in_at = ? 
            WHERE guest_id = ?
        ''', (datetime.now(), guest_id))
        conn.commit()
        conn.close()
        
        return {"message": "Guest checked in successfully", "guest_id": guest_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Bulk check-in
@app.post("/api/guests/bulk-checkin")
def bulk_checkin(guest_ids: List[str]):
    try:
        conn = get_db()
        now = datetime.now()
        for guest_id in guest_ids:
            conn.execute('''
                UPDATE registrations 
                SET checked_in = 1, checked_in_at = ? 
                WHERE guest_id = ? AND checked_in = 0
            ''', (now, guest_id))
        conn.commit()
        conn.close()
        return {"message": f"Checked in {len(guest_ids)} guests"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Bulk delete
@app.post("/api/guests/bulk-delete")
def bulk_delete(guest_ids: List[str]):
    try:
        conn = get_db()
        placeholders = ','.join(['?'] * len(guest_ids))
        conn.execute(f"DELETE FROM registrations WHERE guest_id IN ({placeholders})", guest_ids)
        conn.commit()
        conn.close()
        return {"message": f"Deleted {len(guest_ids)} guests"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Export to CSV
@app.get("/api/export/csv")
def export_csv():
    try:
        conn = get_db()
        guests = conn.execute("SELECT * FROM registrations ORDER BY registered_at DESC").fetchall()
        conn.close()
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Guest ID', 'Full Name', 'Gender', 'Phone', 'Email', 
            'Organization', 'Job Title', 'City', 'Category', 
            'Registered At', 'Checked In', 'Checked In At'
        ])
        
        for guest in guests:
            guest_dict = dict(guest)
            writer.writerow([
                guest_dict.get('guest_id', ''),
                guest_dict.get('full_name', ''),
                guest_dict.get('gender', ''),
                guest_dict.get('phone', ''),
                guest_dict.get('email', ''),
                guest_dict.get('organization', '') or '',
                guest_dict.get('job_title', '') or '',
                guest_dict.get('city', '') or '',
                guest_dict.get('category', ''),
                guest_dict.get('registered_at', ''),
                'Yes' if guest_dict.get('checked_in', 0) == 1 else 'No',
                guest_dict.get('checked_in_at', '') or ''
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=registrations_export.csv"
            }
        )
    except Exception as e:
        return Response(
            content=f"Error: {str(e)}",
            media_type="text/plain",
            status_code=500
        )

# Export JSON
@app.get("/api/export/json")
def export_json():
    try:
        conn = get_db()
        guests = conn.execute("SELECT * FROM registrations ORDER BY registered_at DESC").fetchall()
        conn.close()
        return [dict(row) for row in guests]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Statistics
@app.get("/api/stats")
def get_stats():
    try:
        conn = get_db()
        total = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
        vip = conn.execute("SELECT COUNT(*) FROM registrations WHERE category = 'VIP'").fetchone()[0]
        guest = conn.execute("SELECT COUNT(*) FROM registrations WHERE category = 'Guest'").fetchone()[0]
        staff = conn.execute("SELECT COUNT(*) FROM registrations WHERE category = 'Staff'").fetchone()[0]
        media = conn.execute("SELECT COUNT(*) FROM registrations WHERE category = 'Media'").fetchone()[0]
        checked_in = conn.execute("SELECT COUNT(*) FROM registrations WHERE checked_in = 1").fetchone()[0]
        
        # Get today's registrations
        today = datetime.now().strftime('%Y-%m-%d')
        today_count = conn.execute("SELECT COUNT(*) FROM registrations WHERE DATE(registered_at) = ?", (today,)).fetchone()[0]
        
        conn.close()
        
        return {
            "total": total,
            "vip": vip,
            "guest": guest,
            "staff": staff,
            "media": media,
            "checked_in": checked_in,
            "pending": total - checked_in,
            "today": today_count,
            "check_in_rate": round((checked_in / total * 100) if total > 0 else 0, 1)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics - Daily
@app.get("/api/analytics/daily")
def get_daily_stats():
    try:
        conn = get_db()
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        results = conn.execute('''
            SELECT DATE(registered_at) as date, COUNT(*) as count 
            FROM registrations 
            WHERE DATE(registered_at) >= ? 
            GROUP BY DATE(registered_at) 
            ORDER BY date
        ''', (thirty_days_ago,)).fetchall()
        conn.close()
        return [{"date": row['date'], "count": row['count']} for row in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics - Categories
@app.get("/api/analytics/categories")
def get_category_breakdown():
    try:
        conn = get_db()
        results = conn.execute('''
            SELECT category, COUNT(*) as count 
            FROM registrations 
            GROUP BY category 
            ORDER BY count DESC
        ''').fetchall()
        conn.close()
        return [{"category": row['category'], "count": row['count']} for row in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics - Check-ins
@app.get("/api/analytics/checkins")
def get_checkin_analytics():
    try:
        conn = get_db()
        total = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
        checked = conn.execute("SELECT COUNT(*) FROM registrations WHERE checked_in = 1").fetchone()[0]
        
        results = conn.execute('''
            SELECT strftime('%H', checked_in_at) as hour, COUNT(*) as count 
            FROM registrations 
            WHERE checked_in = 1 AND checked_in_at IS NOT NULL
            GROUP BY strftime('%H', checked_in_at)
            ORDER BY hour
        ''').fetchall()
        conn.close()
        return {
            "total_guests": total,
            "checked_in": checked,
            "pending": total - checked,
            "check_in_rate": round((checked / total * 100) if total > 0 else 0, 1),
            "by_hour": [{"hour": row['hour'], "count": row['count']} for row in results]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Search
@app.get("/api/search")
def search_guests(q: str):
    try:
        conn = get_db()
        query = f"%{q}%"
        results = conn.execute('''
            SELECT * FROM registrations 
            WHERE full_name LIKE ? OR email LIKE ? OR guest_id LIKE ? OR phone LIKE ? OR organization LIKE ?
            ORDER BY registered_at DESC
        ''', (query, query, query, query, query)).fetchall()
        conn.close()
        return [dict(row) for row in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
