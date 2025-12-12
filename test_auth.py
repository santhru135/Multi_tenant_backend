import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_login():
    print("Testing login...")
    login_data = {
        "username": "testadmin@example.com",
        "password": "Test@1234"
    }
    
    try:
        # Test login
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"Login status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("\nLogin successful!")
            print(f"Access token: {token_data.get('access_token')[:50]}...")
            
            # Save token for future use
            with open("test_token.json", "w") as f:
                json.dump(token_data, f)
            print("\nToken saved to test_token.json")
            
            # Test protected endpoint
            test_protected_endpoint(token_data['access_token'])
            
        else:
            print(f"Login failed. Response: {response.text}")
            
    except Exception as e:
        print(f"Error during login: {str(e)}")

def test_protected_endpoint(access_token: str):
    print("\nTesting protected endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/users/me",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        print(f"Protected endpoint status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"Error testing protected endpoint: {str(e)}")

if __name__ == "__main__":
    test_login()
