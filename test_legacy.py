class TestManager:
    def process(self, data):
        if data:
            result = {"processed": data}
            return result
        return None