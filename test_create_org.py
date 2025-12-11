import requests

# Replace this token with the one obtained from login
access_token = "PASTE_YOUR_ACCESS_TOKEN_HERE"

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

print("Status code:", response.status_code)
print("Response:", response.json())
