import requests

base_url = "http://localhost:8000"

# 1) 회원가입 (관리자)
admin_signup_data = {
    "username": "admin",
    "email": "admin@example.com",
    "password": "securepass123",
    "full_name": "Admin User",
    "is_admin": True
}
requests.post(f"{base_url}/auth/signup", json=admin_signup_data)

# 2) 로그인 (관리자)
admin_auth_response = requests.post(
    f"{base_url}/auth/login",
    json={"username": "admin", "password": "securepass123"},
)
admin_token = admin_auth_response.json()["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}

signup_data = {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepass123",
    "full_name": "John Doe"
}
response = requests.post(f"{base_url}/auth/signup", json=signup_data)

login_data={"username": "john_doe", "password": "securepass123"}
auth_response = requests.post(f"{base_url}/auth/login", json=login_data)
token = auth_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

book_data = {
    "title": "Python Programming",
    "author": "John Smith",
    "isbn": "978-0123456789",
    "category": "Programming",
    "total_copies": 5
}
requests.post(f"{base_url}/books", json=book_data, headers=admin_headers)

search_response = requests.get(f"{base_url}/books?category=Programming&available=true")

borrow_response = requests.post(f"{base_url}/loans", json={"book_id": 1, "user_id": 1}, headers=headers)

loans_response = requests.get(f"{base_url}/users/me/loans", headers=headers)

print("Search:", search_response.json())
print("Borrow:", borrow_response.json())
print("My loans:", loans_response.json())