class Calculator:
    def advanced_calc(self, x, y, operation="add"):
        def add():
            return x + y
        def subtract():
            return x - y
        def multiply():
            return x * y

        operations = {"add": add, "sub": subtract, "mul": multiply}
        return operations.get(operation, add)()