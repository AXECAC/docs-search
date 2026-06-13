import requests

# Login as normal user
r = requests.post("http://localhost:8000/auth/login", data={"username": "testpub", "password": "password123"})
token = r.json().get("access_token")

# Call GET /groups
res = requests.get("http://localhost:8000/groups", headers={"Authorization": f"Bearer {token}"})
print(res.status_code)
print(res.text)
