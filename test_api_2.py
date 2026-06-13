import requests
import json

# Login as admin to get a public document
r = requests.post("http://localhost:8000/auth/login", data={"username": "admin", "password": "admin1234"})
token = r.json().get("access_token")

res = requests.get("http://localhost:8000/documents", headers={"Authorization": f"Bearer {token}"})
print("Admin sees:", [d['title'] for d in res.json()])

# Register a new user
requests.post("http://localhost:8000/auth/register", json={"username": "testpub", "password": "password123", "role": "user"})

# Login as new user
r = requests.post("http://localhost:8000/auth/login", data={"username": "testpub", "password": "password123"})
token2 = r.json().get("access_token")

res2 = requests.get("http://localhost:8000/documents", headers={"Authorization": f"Bearer {token2}"})
print("New user sees:", [d['title'] for d in res2.json()])
