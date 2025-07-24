#!/bin/bash
# Flow 시스템 정리 스크립트

echo "🗑️ Flow 시스템 정리 시작..."

# FlowManager 삭제
echo "Deleting FlowManagers..."
rm -f python/ai_helpers_new/flow_manager.py
rm -f python/ai_helpers_new/folder_flow_manager.py
rm -f python/ai_helpers_new/simple_flow_manager.py
rm -f python/ai_helpers_new/flow_integration.py

# Service 삭제
echo "Deleting Services..."
rm -f python/ai_helpers_new/service/flow_service.py
rm -f python/ai_helpers_new/service/cached_flow_service.py
rm -f python/ai_helpers_new/service/folder_based_flow_service.py
rm -f python/ai_helpers_new/service/plan_service.py
rm -f python/ai_helpers_new/service/task_service.py

# Repository 삭제
echo "Deleting Repositories..."
rm -f python/ai_helpers_new/repository/folder_based_repository.py
rm -f python/ai_helpers_new/repository/simplified_repository.py

# 유틸리티 삭제
echo "Deleting Utilities..."
rm -f python/ai_helpers_new/flow_batch.py
rm -f python/ai_helpers_new/flow_context_wrapper.py
rm -f python/ai_helpers_new/flow_search.py
rm -f python/ai_helpers_new/plan_auto_complete.py
rm -f python/ai_helpers_new/migrate_flows.py
rm -f python/ai_helpers_new/migrate_to_folder_flow.py
rm -f python/ai_helpers_new/workflow_commands.py

# 폴더 삭제
echo "Deleting folders..."
rm -rf python/ai_helpers_new/infrastructure
rm -rf python/ai_helpers_new/commands
rm -rf python/ai_helpers_new/presentation

echo "✅ 정리 완료!"
