import sys
sys.path.append(r'C:\Users\82106\Desktop\ai-coding-brain-mcp\python')
from workflow_wrapper import wf

result = wf('/status')
print(f'Type: {type(result)}')
print(f'ok: {result.get("ok")}')
print(f'data: {result.get("data")}')

# 자세한 정보 출력
if result.get("ok"):
    data = result.get("data", {})
    if isinstance(data, dict):
        print(f'progress: {data.get("progress")}%')
        print(f'completed: {data.get("completed")}')
        print(f'total: {data.get("total")}')
        print('raw output (first 100 chars):')
        print(data.get('raw', '')[:100])
