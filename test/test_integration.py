class DataProcessor:
    def __init__(self):
        self.data = []

    def add_item(self, item):
        """Add item to data list"""
        self.data.append(item)

    def process_all(self):
        """Process all items"""
        results = []
        for item in self.data:
            if isinstance(item, int):
                results.append(item * 2)
            elif isinstance(item, str):
                results.append(item.upper())
        return results
