
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'python', 'api'))

from web_automation_integrated import REPLBrowserWithRecording
import traceback

print("Detailed Web Automation Test")
print("=" * 50)

try:
    # Create browser instance
    print("\n1. Creating browser instance...")
    browser = REPLBrowserWithRecording(headless=False)
    print("OK: Browser instance created")

    # Test browser not started
    print("\n2. Testing browser not started...")
    result = browser.goto("https://www.google.com")
    print(f"Result: {result}")
    if result is None:
        print("ERROR: goto returned None")
    elif not result.get('ok'):
        print(f"OK: Expected error - {result.get('error')}")

    # Start browser
    print("\n3. Starting browser...")
    start_result = browser.start()
    print(f"Start result: {start_result}")

    if start_result and start_result.get('ok'):
        print("OK: Browser started successfully")

        # Test navigation
        print("\n4. Testing navigation...")
        goto_result = browser.goto("https://www.google.com")
        print(f"Goto result: {goto_result}")

        if goto_result and goto_result.get('ok'):
            print("OK: Navigation successful")

            # Test typing
            print("\n5. Testing typing with escaped selector...")
            type_result = browser.type("input[name='q']", "test")
            print(f"Type result: {type_result}")

        # Stop browser
        print("\n6. Stopping browser...")
        stop_result = browser.stop()
        print(f"Stop result: {stop_result}")

except Exception as e:
    print(f"\nERROR: {e}")
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test completed!")
