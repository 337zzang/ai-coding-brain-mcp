import json
import sys

# 간단한 테스트 요청 생성
test_request = {
    "jsonrpc": "2.0",
    "id": 999,
    "method": "execute",
    "params": {
        "code": "print('Hello from test!')"
    }
}

# JSON 요청 전송
json.dump(test_request, sys.stdout)
sys.stdout.write('\n')
sys.stdout.flush()
