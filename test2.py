class Manager:
    def __init__(self):
        self.data = []

    def add_item(self, name):
        item = {"name": name}
        self.data.append(item)
        return item