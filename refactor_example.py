class UserManager:
    def __init__(self):
        self.user = None
        self.user_cache = {}

    def get_user(self, user_id):
        """Get user by ID"""
        if user_id in self.user_cache:
            return self.user_cache[user_id]

        # Fetch user from database
        user = self.fetch_from_db(user_id)
        if user:
            self.user_cache[user_id] = user
            print(f"Loaded user: {user['name']}")
        return user

    def update_user(self, user):
        """Update user data"""
        self.user = user
        print(f"Updated user: {user}")
