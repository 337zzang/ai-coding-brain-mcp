class Manager:
    def add(self, name, email=None):
        user = {"name": name, "email": email}
        return user