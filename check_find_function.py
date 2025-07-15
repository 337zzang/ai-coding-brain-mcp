
import re
def find_function(directory: str, function_name: str):
    escaped_name = re.escape(function_name)
    pattern = f"def\\s+{escaped_name}\\s*\\("
    print(f"Pattern: {pattern}")
    return pattern

result = find_function(".", "test**function")
print(f"Result: {result}")
