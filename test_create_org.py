import requests

access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTNhNzAwYzkwOTNiMjZkYjMzM2ZiNTAiLCJvcmciOiJzeXN0ZW0iLCJpc19zdXBlcmFkbWluIjp0cnVlLCJleHAiOjE3NjU0Mzk5Mjl9.vohOIkxhPrF9NgoQe7sUTWiFStN_CqCSZD4fgU9J5k8"

url = "http://127.0.0.1:8000/org/create"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
data = {
    "organization_name": "my_org",
    "admin_email": "admin@myorg.com",
    "admin_password": "MyOrgPass123"
}

response = requests.post(url, json=data, headers=headers)
print(response.status_code)
print(response.json())
