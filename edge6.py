class APIHandler:
    @property
    def status(self):
        return "active"

    @staticmethod
    def validate_input(data):
        if data is None:
            raise ValueError("Data cannot be None")
        return isinstance(data, (str, int, float, list, dict))