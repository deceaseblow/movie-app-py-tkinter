import os
import json
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DB = os.path.join(BASE_DIR, "..", "db", "users.json")


class AuthService:
    def __init__(self):
        if not os.path.exists(USER_DB):
            with open(USER_DB, "w") as f:
                json.dump({}, f)

    def create_account(self, data):
        username = data.get("username")
        password = data.get("password")
        with open(USER_DB, "r+") as f:
            users = json.load(f)
            if username in users:
                return {"status": "fail", "message": "Username already exists"}
            user_id = str(uuid.uuid4())
            users[username] = {"password": password, "id": user_id}
            f.seek(0)
            f.truncate()
            json.dump(users, f)
        return {"status": "success", "message": "Account created", "user_id": user_id}

    def authenticate(self, data):
        username = data.get("username")
        password = data.get("password")
        with open(USER_DB, "r") as f:
            users = json.load(f)
        user_info = users.get(username)
        if user_info and user_info.get("password") == password:
            return {"status": "success", "message": "Login successful", "user_id": user_info["id"]}
        return {"status": "fail", "message": "Invalid credentials"}
