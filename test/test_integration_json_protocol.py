"""
Integration test for the new JSON protocol system
"""
import subprocess
import json
import sys
import time

def test_command(command_data, executor="python/command_executor_v2.py"):
    """Test a command through the executor"""
    print(f"\n🧪 Testing: {command_data['command']} - {command_data['action']}")
    print("-" * 50)
    
    process = subprocess.Popen(
        ['python', executor],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )
    
    stdout, stderr = process.communicate(input=json.dumps(command_data))
    
    if stderr:
        print(f"❌ STDERR: {stderr}")
    
    try:
        response = json.loads(stdout)
        print(f"✅ Status: {response['status']}")
        
        if response['status'] == 'success':
            print(f"📊 Data: {json.dumps(response.get('data', {}), indent=2)}")
        else:
            print(f"❌ Error: {response['error']['message']}")
            if 'traceback' in response['error'].get('details', {}):
                print("Traceback preview:")
                print(response['error']['details']['traceback'][:200] + "...")
        
        return response
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        print(f"Raw output: {stdout[:200]}...")
        return None

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 JSON Protocol Integration Test Suite")
    print("=" * 60)
    
    tests = [
        # Test 1: Execute code
        {
            "name": "Execute simple code",
            "data": {
                "command": "execute",
                "action": "code",
                "payload": {"code": "result = 2 + 2\nprint(f'2 + 2 = {result}')"}
            },
            "expected": lambda r: r['status'] == 'success' and '2 + 2 = 4' in r['data']['stdout']
        },
        
        # Test 2: Unknown command
        {
            "name": "Unknown command handling",
            "data": {
                "command": "unknown",
                "action": "test",
                "payload": {}
            },
            "expected": lambda r: r['status'] == 'error' and r['error']['code'] == 'UNKNOWN_COMMAND'
        },
        
        # Test 3: Plan show (may fail due to no active plan)
        {
            "name": "Plan show command",
            "data": {
                "command": "plan",
                "action": "show",
                "payload": {}
            },
            "expected": lambda r: r['status'] in ['success', 'error']  # May have no plan
        },
        
        # Test 4: Complex code execution
        {
            "name": "Complex code with imports",
            "data": {
                "command": "execute",
                "action": "code",
                "payload": {
                    "code": """
import os
import json

data = {"test": True, "value": 42}
print(json.dumps(data, indent=2))
print(f"Current directory: {os.getcwd()}")
"""
                }
            },
            "expected": lambda r: r['status'] == 'success' and '"test": true' in r['data']['stdout']
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        result = test_command(test['data'])
        
        if result and test['expected'](result):
            print("✅ Test PASSED")
            passed += 1
        else:
            print("❌ Test FAILED")
            failed += 1
    
    print(f"\n\n📊 Test Summary")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success rate: {(passed/len(tests)*100):.1f}%")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
