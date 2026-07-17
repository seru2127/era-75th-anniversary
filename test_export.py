from fastapi import FastAPI
from fastapi.responses import Response
import sqlite3
import csv
from io import StringIO

app = FastAPI()

@app.get("/api/export/test")
def test_export():
    try:
        conn = sqlite3.connect('registrations.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations")
        data = cursor.fetchall()
        conn.close()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Guest ID', 'Name', 'Email'])
        
        for row in data:
            writer.writerow(row)
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=test.csv"}
        )
    except Exception as e:
        return Response(content=f"Error: {str(e)}", media_type="text/plain", status_code=500)
