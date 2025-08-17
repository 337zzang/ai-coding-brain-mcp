class DataManager:
    def __init__(self):
        self.items = []

    def add_item(self, name):
        item = {"name": name}
        self.items.append(item)
        return item