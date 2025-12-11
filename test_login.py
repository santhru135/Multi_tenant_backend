import requests

login_url = "http://127.0.0.1:8000/admin/login"

# Use form data, not JSON
login_data = {
    "username": "superadmin@example.com",
    "password": "Admin@123",  # the real plain password
    "grant_type": "password"  # optional depending on backend
}

response = requests.post(login_url, data=login_data)  # note 'data='
print("Login status:", response.status_code)
print("Login response:", response.json())
