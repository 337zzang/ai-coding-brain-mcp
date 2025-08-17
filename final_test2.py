class UserManager:
    def __init__(self):
        self.users = []

    def add_user(self, name, email=None):
        if name:
            user = {
                "name": name, 
                "id": len(self.users),
                "email": email
            }
            self.users.append(user)
            return user
        return None

    def get_user(self, user_id):
        for user in self.users:
            if user["id"] == user_id:
                return user
        return None