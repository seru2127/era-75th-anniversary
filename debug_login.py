import requests
import json

print("=" * 50)
print("TESTING LOGIN")
print("=" * 50)

# Test data
data = {
    "username": "admin",
    "password": "Seruera75"
}

print(f"1. Sending data: {data}")

try:
    # Send request
    response = requests.post(
        'http://localhost:8000/api/login',
        json=data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"2. Status code: {response.status_code}")
    print(f"3. Response text: {response.text}")
    
    if response.status_code == 200:
        print(f"4. Response JSON: {response.json()}")
    else:
        print(f"4. Error response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to backend. Make sure it's running on port 8000")
except Exception as e:
    print(f"❌ Error: {e}")
