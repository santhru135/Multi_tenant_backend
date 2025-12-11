import requests

# 1️⃣ Login as admin to get access token
login_url = "http://127.0.0.1:8000/admin/login"
login_data = {
    "username": "admin@myorg.com",  # replace with your admin email
    "password": "MyOrgPass123",      # replace with your admin password
    "grant_type": "password"         # required by OAuth2PasswordRequestForm
}

login_response = requests.post(login_url, data=login_data)
print("Login status:", login_response.status_code)
print("Login response:", login_response.json())

if login_response.status_code != 200:
    print("Login failed. Check credentials and field names.")
    exit()

# Extract the access token
access_token = login_response.json().get("access_token")
if not access_token:
    print("No access token returned.")
    exit()

print("✅ Access token received:", access_token)

# 2️⃣ Use token to create a new organization
create_org_url = "http://127.0.0.1:8000/org/create"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
org_data = {
    "organization_name": "my_org",          # desired org name
    "admin_email": "admin@myorg.com",       # admin for this org
    "admin_password": "MyOrgPass123"        # password for the org admin
}

org_response = requests.post(create_org_url, json=org_data, headers=headers)
print("Create Org status:", org_response.status_code)
print("Create Org response:", org_response.json())
