class DataProcessor:
    def __init__(self):
        self.value = 0
        self.print_enabled = True

    def process(self, value):
        """Process the value and print result"""
        self.value = value
        if self.print_enabled:
            print(f"Processing value: {value}")
        return value * 2

    def print_status(self):
        """Print current status"""
        print(f"Current value: {self.value}")
        print("Status: Active")

# Usage
processor = DataProcessor()
result = processor.process(10)
print(f"Result: {result}")

# Comment about print
# This is where we print the final output
