import requests

# -----------------------------
# 1. Superadmin login
# -----------------------------
login_url = "http://127.0.0.1:8000/admin/login"
login_data = {
    "username": "superadmin@example.com",  # your superadmin email
    "password": "Admin@123"               # your superadmin password
}

login_resp = requests.post(login_url, data=login_data)
if login_resp.status_code != 200:
    print("Login failed:", login_resp.text)
    exit()

token = login_resp.json()["access_token"]
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("✅ Superadmin logged in successfully!")

# -----------------------------
# 2. Create a new organization
# -----------------------------
org_name = "my_org"
create_url = "http://127.0.0.1:8000/org/create"
create_data = {
    "organization_name": org_name,
    "admin_email": "admin@myorg.com",
    "admin_password": "MyOrgPass123"
}

create_resp = requests.post(create_url, json=create_data, headers=headers)
print("\n--- Create Organization ---")
print("Status:", create_resp.status_code)
try:
    print(create_resp.json())
except Exception:
    print("Raw response:", create_resp.text)


# -----------------------------
# 3. Get organization details
# -----------------------------
get_url = f"http://127.0.0.1:8000/org/get?organization_name={org_name}"
get_resp = requests.get(get_url, headers=headers)
print("\n--- Get Organization ---")
print("Status:", get_resp.status_code)
print(get_resp.json())

# -----------------------------
# 4. Update organization name
# -----------------------------
update_url = "http://127.0.0.1:8000/org/update"
update_data = {
    "organization_name": org_name,
    "new_organization_name": "my_org_updated",
    "admin_email": "admin@myorg.com",
    "admin_password": "MyOrgPass123"
}
update_resp = requests.put(update_url, json=update_data, headers=headers)
print("\n--- Update Organization ---")
print("Status:", update_resp.status_code)
print(update_resp.json())

# -----------------------------
# 5. Delete organization
# -----------------------------
delete_url = "http://127.0.0.1:8000/org/delete"
delete_data = {
    "organization_name": "my_org_updated"
}
delete_resp = requests.delete(delete_url, json=delete_data, headers=headers)
print("\n--- Delete Organization ---")
print("Status:", delete_resp.status_code)
print(delete_resp.json())
