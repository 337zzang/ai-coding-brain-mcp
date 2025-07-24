# CachedFlowService 테스트
import ai_helpers_new as h
from ai_helpers_new.service.cached_flow_service import CachedFlowService

print("\n🧪 CachedFlowService 테스트\n")

# 1. 서비스 초기화
service = CachedFlowService()
print("✅ 서비스 초기화 성공")

# 2. Flow 목록 조회
flows = service.list_flows()
print(f"\n현재 Flow 수: {len(flows)}")
for flow in flows[:3]:
    print(f"  - {flow.id}: {flow.name}")

# 3. 특정 Flow 조회
test_flow = service.get_flow("ai-coding-brain-mcp")
if test_flow:
    print(f"\n✅ Flow 조회 성공: {test_flow.id}")
    print(f"   Plans: {len(test_flow.plans)}")
else:
    print("❌ Flow 조회 실패")

# 4. 캐시 통계
stats = service.get_cache_stats()
print(f"\n캐시 통계: {stats}")

# 5. 마이그레이션 테스트 (dry run)
print("\n마이그레이션 대상 확인:")
import os
for f in os.listdir(".ai-brain"):
    if f.endswith('.json') and f not in ['flows.json', 'index.json'] and not f.startswith('checkpoint_'):
        print(f"  - {f}")

print("\n✅ 테스트 완료!")
