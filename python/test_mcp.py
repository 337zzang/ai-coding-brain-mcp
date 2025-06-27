
import sys
import json

def test_mcp():
    return {
        "success": True,
        "python_path": sys.executable,
        "message": "MCP test successful"
    }

if __name__ == "__main__":
    result = test_mcp()
    print(json.dumps(result))
