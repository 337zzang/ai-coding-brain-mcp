"""
Test script for command_executor
"""
import subprocess
import json


def test_command(command_data):
    """Test a command through command_executor"""
    process = subprocess.Popen(
        ['python', 'python/command_executor.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )
    
    stdout, stderr = process.communicate(input=json.dumps(command_data))
    
    if stderr:
        print(f"STDERR: {stderr}")
    
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {"error": f"Invalid JSON response: {stdout}"}


# Test cases
print("🧪 Testing Command Executor\n")

# Test 1: Plan show
print("1. Testing plan show:")
result = test_command({
    "command": "plan",
    "action": "show",
    "payload": {}
})
print(json.dumps(result, indent=2))

# Test 2: Execute code
print("\n2. Testing execute code:")
result = test_command({
    "command": "execute",
    "action": "code",
    "payload": {
        "code": "print('Hello from command executor!')"
    }
})
print(json.dumps(result, indent=2))

# Test 3: Unknown command
print("\n3. Testing unknown command:")
result = test_command({
    "command": "unknown",
    "action": "test",
    "payload": {}
})
print(json.dumps(result, indent=2))
