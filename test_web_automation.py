
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'python', 'api'))

from web_automation_integrated import REPLBrowserWithRecording

print("Web Automation Test Start")
print("=" * 50)

# 1. headless option test
print("\n1. headless option test")
browser = REPLBrowserWithRecording(headless=False)
print("OK: REPLBrowserWithRecording created (headless=False)")

# 2. browser not started test
print("\n2. browser not started test")
result = browser.goto("https://www.google.com")
if not result.get('ok') and 'start()' in result.get('error', ''):
    print("OK: Browser not started detection successful")
    print(f"   Error: {result.get('error')}")
else:
    print("FAIL: Browser not started detection failed")

# 3. browser start
print("\n3. browser start")
start_result = browser.start()
if start_result.get('ok'):
    print("OK: Browser started")
else:
    print(f"FAIL: Browser start failed: {start_result.get('error')}")
    exit(1)

# 4. page navigation
print("\n4. page navigation test")
goto_result = browser.goto("https://www.google.com")
if goto_result.get('ok'):
    print("OK: Google page loaded")
    print("   (Check if browser window is visible)")
else:
    print(f"FAIL: Page navigation failed: {goto_result.get('error')}")

# Wait 3 seconds
import time
print("\nWaiting 3 seconds...")
time.sleep(3)

# 5. selector escape test
print("\n5. selector escape test")
test_selector = "input[name='q']"  # Google search box
type_result = browser.type(test_selector, "Hello World")
if type_result.get('ok'):
    print("OK: Selector with single quote handled")
else:
    print(f"FAIL: Selector handling failed: {type_result.get('error')}")

# 6. browser stop
print("\n6. browser stop")
stop_result = browser.stop()
if stop_result.get('ok'):
    print("OK: Browser stopped")
else:
    print(f"FAIL: Browser stop failed: {stop_result.get('error')}")

print("\n" + "=" * 50)
print("Test completed!")
