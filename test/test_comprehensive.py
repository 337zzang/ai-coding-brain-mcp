def simple_func():
    """Updated"""
    return 42

class Calculator:

    def add(self, a, b):
        """New add"""
        return a + b + 1

    def multiply(self, a, b):
        return a * b

    class Inner:

        def method(self):
            return 'updated'

async def async_func():
    """Async updated"""
    return 'async result'