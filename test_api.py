import requests
import json

r = requests.post("http://localhost:8000/auth/login", data={"username": "admin", "password": "password"})
token = r.json().get("access_token")

res = requests.get("http://localhost:8000/documents", headers={"Authorization": f"Bearer {token}"})
print(json.dumps(res.json(), indent=2))
