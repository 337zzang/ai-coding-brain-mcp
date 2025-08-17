class UserService:
    def __init__(self):
        self.users = []
        self.config = {"max_users": 100}

    def add_user(self, username, email=None, role="user"):
        # 향상된 사용자 추가 함수
        if len(self.users) < self.config["max_users"]:
            user = {
                "username": username,
                "email": email,
                "role": role,
                "id": len(self.users),
                "created": "2025-08-14",
                "status": "active"
            }
            self.users.append(user)

            # 로깅
            print(f"사용자 추가됨: {username}")

            return user
        return None

    def get_user_by_id(self, user_id):
        for user in self.users:
            if user["id"] == user_id:
                return user
        return None