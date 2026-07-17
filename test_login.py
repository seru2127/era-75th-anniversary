import requests
import json

# Test login
data = {
    "username": "admin",
    "password": "Seruera75"
}

print(f"Sending: {data}")

try:
    response = requests.post('http://localhost:8000/api/login', json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
