from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, HTMLResponse
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

# Serve HTML files at root
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# Serve other HTML files
@app.get("/{filename}.html", response_class=HTMLResponse)
async def serve_html(filename: str):
    file_path = f"{filename}.html"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="Page not found")

# API Health check
@app.get("/api/health")
def health():
    return {"status": "healthy", "database": "connected"}

# Database
def get_db():
    conn = sqlite3.connect('registrations.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
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

# Certificate generation
@app.get("/api/certificate/{guest_id}")
def generate_certificate(guest_id: str):
    try:
        conn = get_db()
        guest = conn.execute("SELECT * FROM registrations WHERE guest_id = ?", (guest_id,)).fetchone()
        conn.close()
        
        if not guest:
            raise HTTPException(status_code=404, detail="Guest not found")
        
        buffer = BytesIO()
        page_width, page_height = landscape(A4)
        c = canvas.Canvas(buffer, pagesize=landscape(A4))
        
        # Background
        c.setFillColorRGB(0.98, 0.96, 0.92)
        c.rect(0, 0, page_width, page_height, fill=1, stroke=0)
        
        # Border
        c.setStrokeColor(HexColor("#FF6B00"))
        c.setLineWidth(4)
        c.rect(20, 20, page_width - 40, page_height - 40)
        
        c.setStrokeColor(HexColor("#D4AF37"))
        c.setLineWidth(1.5)
        c.rect(30, 30, page_width - 60, page_height - 60)
        
        # Corner decorations
        corner_size = 30
        c.setStrokeColor(HexColor("#FF6B00"))
        c.setLineWidth(2)
        c.line(35, page_height - 35, 35 + corner_size, page_height - 35)
        c.line(35, page_height - 35, 35, page_height - 35 - corner_size)
        c.line(page_width - 35, page_height - 35, page_width - 35 - corner_size, page_height - 35)
        c.line(page_width - 35, page_height - 35, page_width - 35, page_height - 35 - corner_size)
        c.line(35, 35, 35 + corner_size, 35)
        c.line(35, 35, 35, 35 + corner_size)
        c.line(page_width - 35, 35, page_width - 35 - corner_size, 35)
        c.line(page_width - 35, 35, page_width - 35, 35 + corner_size)
        
        # Watermark
        try:
            watermark_path = "era_logo.png"
            if os.path.exists(watermark_path):
                watermark = ImageReader(watermark_path)
                c.saveState()
                c.setFillColorRGB(1, 1, 1, 0.08)
                c.drawImage(watermark, page_width/2 - 150, page_height/2 - 150, 
                           width=300, height=300, preserveAspectRatio=True, mask='auto')
                c.restoreState()
        except:
            pass
        
        # Logos
        logo_y = page_height - 75
        
        try:
            left_logo_path = "era_75_logo.png"
            if os.path.exists(left_logo_path):
                left_logo = ImageReader(left_logo_path)
                c.drawImage(left_logo, 50, logo_y - 35, width=80, height=60, preserveAspectRatio=True)
        except:
            pass
        
        try:
            right_logo_path = "era_logo.png"
            if os.path.exists(right_logo_path):
                right_logo = ImageReader(right_logo_path)
                c.drawImage(right_logo, page_width - 130, logo_y - 35, width=80, height=60, preserveAspectRatio=True)
        except:
            pass
        
        # Title
        title_y = page_height - 85
        c.setFillColor(HexColor("#D4AF37"))
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(page_width / 2, title_y, "CERTIFICATE OF PARTICIPATION")
        
        c.setStrokeColor(HexColor("#D4AF37"))
        c.setLineWidth(2)
        c.line(page_width / 2 - 180, title_y - 15, page_width / 2 + 180, title_y - 15)
        
        # Subtitle
        c.setFillColor(HexColor("#555555"))
        c.setFont("Helvetica", 13)
        c.drawCentredString(page_width / 2, title_y - 42, "This certificate is proudly presented to")
        
        # Guest Name
        c.setFillColor(HexColor("#FF6B00"))
        c.setFont("Helvetica-Bold", 38)
        name = guest['full_name'].upper()
        c.drawCentredString(page_width / 2, title_y - 100, name)
        
        c.setStrokeColor(HexColor("#FF6B00"))
        c.setLineWidth(2)
        c.line(page_width / 2 - 160, title_y - 115, page_width / 2 + 160, title_y - 115)
        
        # Main Text
        c.setFillColor(HexColor("#333333"))
        c.setFont("Helvetica", 13)
        c.drawCentredString(page_width / 2, title_y - 145, "for their valuable participation in the")
        c.drawCentredString(page_width / 2, title_y - 168, "ERA 75th Anniversary Event")
        
        # Guest Details
        detail_y = title_y - 220
        
        c.setFillColor(HexColor("#555555"))
        c.setFont("Helvetica", 11)
        c.drawString(page_width / 2 - 180, detail_y, "Guest ID:")
        c.setFillColor(HexColor("#FF6B00"))
        c.setFont("Helvetica-Bold", 13)
        c.drawString(page_width / 2 - 100, detail_y, guest['guest_id'])
        
        c.setFillColor(HexColor("#555555"))
        c.setFont("Helvetica", 11)
        c.drawString(page_width / 2 - 180, detail_y - 22, "Organization:")
        c.setFillColor(HexColor("#333333"))
        c.setFont("Helvetica", 12)
        c.drawString(page_width / 2 - 100, detail_y - 22, guest['organization'] or 'N/A')
        
        c.setFillColor(HexColor("#555555"))
        c.setFont("Helvetica", 11)
        c.drawString(page_width / 2 - 180, detail_y - 44, "Category:")
        c.setFillColor(HexColor("#333333"))
        c.setFont("Helvetica", 12)
        c.drawString(page_width / 2 - 100, detail_y - 44, guest['category'])
        
        # Date
        c.setFillColor(HexColor("#555555"))
        c.setFont("Helvetica", 11)
        c.drawCentredString(page_width / 2, detail_y - 75, "Date: July 23, 2026")
        
        # Signature
        signature_y = 120
        
        c.setStrokeColor(HexColor("#333333"))
        c.setLineWidth(1)
        c.line(page_width / 2 - 100, signature_y, page_width / 2 + 100, signature_y)
        
        try:
            signature_path = "director_signature.png"
            if os.path.exists(signature_path):
                signature = ImageReader(signature_path)
                c.drawImage(signature, page_width / 2 - 60, signature_y + 5, 
                           width=120, height=40, preserveAspectRatio=True, mask='auto')
            else:
                c.setFillColor(HexColor("#333333"))
                c.setFont("Helvetica", 11)
                c.drawCentredString(page_width / 2, signature_y + 10, "Director General")
        except:
            c.setFillColor(HexColor("#333333"))
            c.setFont("Helvetica", 11)
            c.drawCentredString(page_width / 2, signature_y + 10, "Director General")
        
        c.setFillColor(HexColor("#555555"))
        c.setFont("Helvetica", 10)
        c.drawCentredString(page_width / 2, signature_y - 18, "Director General")
        c.drawCentredString(page_width / 2, signature_y - 32, "Ethiopian Roads Administration")
        
        # Footer divider
        c.setStrokeColor(HexColor("#D4AF37"))
        c.setLineWidth(0.5)
        c.line(page_width / 2 - 60, signature_y - 50, page_width / 2 + 60, signature_y - 50)
        
        # Footer
        c.setFillColor(HexColor("#888888"))
        c.setFont("Helvetica", 8)
        c.drawCentredString(page_width / 2, 30, "Ethiopian Roads Administration - ERA 75th Anniversary Celebration")
        c.drawCentredString(page_width / 2, 18, f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}")
        
        c.save()
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=certificate_{guest_id}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Certificate generation failed: {str(e)}")

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

# Export functions
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

@app.get("/api/export/json")
def export_json():
    try:
        conn = get_db()
        guests = conn.execute("SELECT * FROM registrations ORDER BY registered_at DESC").fetchall()
        conn.close()
        return [dict(row) for row in guests]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/excel")
def export_excel():
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        import io
        
        conn = get_db()
        guests = conn.execute("SELECT * FROM registrations ORDER BY registered_at DESC").fetchall()
        conn.close()
        
        wb = Workbook()
        ws = wb.active
        ws.title = "ERA 75th Registrations"
        
        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="FF6B00", end_color="FF6B00", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        headers = [
            'Guest ID', 'Full Name', 'Gender', 'Phone', 'Email', 
            'Organization', 'Job Title', 'City', 'Category', 
            'Registered At', 'Checked In', 'Checked In At'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = border
        
        for row_idx, guest in enumerate(guests, 2):
            guest_dict = dict(guest)
            data = [
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
            ]
            
            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row_idx, column=col, value=value)
                cell.border = border
                cell.alignment = Alignment(horizontal="left", vertical="center")
                if col == 11:
                    if value == 'Yes':
                        cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                    else:
                        cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        
        for col in range(1, len(headers) + 1):
            column_letter = get_column_letter(col)
            ws.column_dimensions[column_letter].auto_size = True
            if col in [2, 5, 6]:
                ws.column_dimensions[column_letter].width = 25
        
        ws.freeze_panes = 'A2'
        
        summary_ws = wb.create_sheet("Summary")
        summary_ws['A1'] = "ERA 75th Anniversary Event"
        summary_ws['A1'].font = Font(bold=True, size=16, color="FF6B00")
        summary_ws['A3'] = "Registration Summary Report"
        summary_ws['A3'].font = Font(bold=True, size=14)
        
        total = len(guests)
        checked_in = sum(1 for g in guests if g['checked_in'] == 1)
        pending = total - checked_in
        
        summary_data = [
            ['', ''],
            ['Total Registrations', total],
            ['Checked In', checked_in],
            ['Pending', pending],
            ['Check-in Rate', f"{round((checked_in/total*100) if total > 0 else 0, 1)}%"],
            ['', ''],
            ['Generated On', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        for row_idx, (label, value) in enumerate(summary_data, 5):
            summary_ws.cell(row=row_idx, column=1, value=label)
            summary_ws.cell(row=row_idx, column=2, value=value)
            if row_idx > 5:
                summary_ws.cell(row=row_idx, column=1).font = Font(bold=True)
        
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=registrations_export.xlsx"
            }
        )
    except Exception as e:
        return Response(
            content=f"Error: {str(e)}",
            media_type="text/plain",
            status_code=500
        )

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

# Analytics
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
