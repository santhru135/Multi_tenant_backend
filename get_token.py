import requests

url = "http://127.0.0.1:8000/admin/login"
data = {
    "username": "superadmin@example.com",
    "password": "Admin@123"
}

response = requests.post(url, data=data)
print(response.status_code)
print(response.json())
