#!/usr/bin/env python3
"""Run Context System unit tests"""

import subprocess
import sys
import os

# Add project to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Run tests
print("🧪 Running Context System Unit Tests...")
print("="*60)

result = subprocess.run(
    [sys.executable, "-m", "unittest", "tests.test_context_system", "-v"],
    cwd=project_root,
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)

print("\n" + "="*60)
if result.returncode == 0:
    print("✅ All tests passed!")
else:
    print("❌ Some tests failed!")
    sys.exit(1)
