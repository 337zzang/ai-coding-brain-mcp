"""
영속적 히스토리 관리 시스템
========================
대화를 넘어서 히스토리를 유지하는 관리자
"""

import json
import os
from datetime import datetime


class PersistentHistoryManager:
    """프로젝트별 독립적인 히스토리 관리자"""
    
    def __init__(self):
        # 현재 프로젝트의 memory 폴더 사용
        self.memory_dir = os.path.join(os.getcwd(), "memory")
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # 프로젝트별 파일 경로
        self.history_file = os.path.join(self.memory_dir, "workflow_history.json")
        self.checkpoint_dir = os.path.join(self.memory_dir, "checkpoints")
        self.session_file = os.path.join(self.memory_dir, "session_state.json")
        
        # 체크포인트 디렉토리 생성
        os.makedirs(self.checkpoint_dir, exist_ok=True)
    
    def add_action(self, action, details=None, data=None):
        """액션을 히스토리에 추가 (파일에 즉시 저장)"""
        # 기존 히스토리 로드
        history = self._load_history()
        
        # 새 엔트리 추가
        entry = {
            "id": len(history) + 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "details": details,
            "conversation_id": self._get_conversation_id()
        }
        
        # 데이터가 있으면 체크포인트로 저장
        if data:
            checkpoint_file = os.path.join(self.checkpoint_dir, f"checkpoint_{entry['id']}.json")
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            entry["checkpoint"] = checkpoint_file
        
        history.append(entry)
        
        # 즉시 파일에 저장
        self._save_history(history)
        
        print(f"✅ 히스토리 추가: [{entry['id']}] {action}")
        return entry['id']
    
    def get_last_checkpoint(self, action_type=None):
        """마지막 체크포인트 데이터 가져오기"""
        history = self._load_history()
        
        # 역순으로 검색
        for entry in reversed(history):
            if action_type and entry.get('action') != action_type:
                continue
            
            if 'checkpoint' in entry and os.path.exists(entry['checkpoint']):
                with open(entry['checkpoint'], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"📌 체크포인트 로드: {entry['action']} ({entry['timestamp']})")
                return data
        
        return None
    
    def show_history(self, limit=10, show_summary=True):
        """최근 히스토리 표시 (개선된 버전)"""
        history = self._load_history()
        
        print(f"\n📜 전체 히스토리: {len(history)} 항목")
        print(f"{'='*60}")
        
        # 대화별로 그룹화
        conversations = {}
        for entry in history:
            conv_id = entry.get('conversation_id', 'unknown')
            if conv_id not in conversations:
                conversations[conv_id] = []
            conversations[conv_id].append(entry)
        
        print(f"💬 총 {len(conversations)} 개의 대화에서 작업 수행")
        
        # 마지막 세션 요약 표시
        if show_summary:
            summary = self.get_last_session_summary()
            if summary:
                print(f"\n🔍 마지막 세션 요약:")
                print(f"   시작: {summary['start_time']} | 종료: {summary['end_time']}")
                print(f"   작업 수: {summary['total_actions']} | 체크포인트: {'있음' if summary['has_checkpoints'] else '없음'}")
                if summary['major_actions']:
                    print(f"   주요 작업:")
                    for action in summary['major_actions'][:3]:
                        print(f"     - {action['action']}")
        
        # 최근 항목 표시
        recent = history[-limit:] if len(history) > limit else history
        print(f"\n최근 {len(recent)} 개 항목:")
        for entry in recent:
            checkpoint = "💾" if 'checkpoint' in entry else "  "
            print(f"{checkpoint} [{entry['id']:3d}] {entry['timestamp']} | {entry['action']}")
            if entry.get('details'):
                print(f"        └─ {entry['details']}")
    
    def continue_from_last(self):
        """마지막 작업에서 이어서 시작 (개선된 버전)"""
        history = self._load_history()
        if not history:
            print("📭 이전 작업이 없습니다.")
            return None
        
        # 최근 컨텍스트 가져오기
        context = self.get_recent_context()
        
        print(f"\n🔄 이전 작업에서 이어서 시작:")
        print(f"   총 작업 수: {context['total_history']}")
        print(f"   최근 작업 요약:")
        for action, count in context['action_summary'].items():
            print(f"     - {action}: {count}회")
        
        last = history[-1]
        print(f"\n   마지막 작업: {last['action']} ({last['timestamp']})")
        if last.get('details'):
            print(f"   상세: {last['details']}")
        
        # 마지막 체크포인트 로드
        if 'checkpoint' in last:
            checkpoint_data = self.get_last_checkpoint()
            print(f"\n💡 체크포인트 데이터를 로드했습니다.")
            return checkpoint_data
        
        # 체크포인트가 없으면 컨텍스트 반환
        return context
    
    def get_workflow_sync_data(self):
        """워크플로우와 동기화할 데이터 가져오기"""
        history = self._load_history()
        
        # 워크플로우 관련 액션 필터링
        workflow_actions = [
            entry for entry in history 
            if 'workflow' in entry.get('action', '').lower() or 
               'task' in entry.get('action', '').lower() or
               'plan' in entry.get('action', '').lower()
        ]
        
        return {
            "total_actions": len(history),
            "workflow_actions": len(workflow_actions),
            "last_action": history[-1] if history else None,
            "conversations": len(set(e.get('conversation_id', '') for e in history))
        }
    
    def sync_with_workflow(self, workflow_data):
        """워크플로우 데이터와 동기화"""
        # 워크플로우 이벤트를 히스토리에 추가
        if workflow_data.get('active_plan_id'):
            self.add_action(
                "워크플로우 동기화",
                f"플랜 ID: {workflow_data['active_plan_id']}",
                {"workflow_snapshot": workflow_data}
            )
    
    def _load_history(self):
        """히스토리 파일 로드"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_history(self, history):
        """히스토리 파일 저장"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        # 세션 상태도 업데이트
        self._update_session_state(history)
    
    def _update_session_state(self, history):
        """세션 상태 업데이트"""
        session_state = {
            "last_access": datetime.now().isoformat(),
            "total_conversations": len(set(h.get('conversation_id', '') for h in history if h.get('conversation_id'))),
            "total_actions": len(history),
            "current_workflow": "ai-coding-brain-mcp"
        }
        
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(session_state, f, ensure_ascii=False, indent=2)
    
    def _get_conversation_id(self):
        """현재 대화 ID (시간 기반, 분 단위까지)"""
        # 실제 구현에서는 Claude API의 conversation_id를 사용할 수 있음
        return f"conv_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    def get_recent_context(self, limit=5):
        """최근 작업 컨텍스트 요약"""
        history = self._load_history()
        if not history:
            return None
        
        recent = history[-limit:] if len(history) > limit else history
        
        # 주요 액션 타입 분석
        action_types = {}
        for entry in recent:
            action = entry.get('action', 'unknown')
            action_types[action] = action_types.get(action, 0) + 1
        
        # 마지막 체크포인트 확인
        last_checkpoint = None
        for entry in reversed(recent):
            if 'checkpoint' in entry:
                last_checkpoint = entry
                break
        
        context = {
            'total_history': len(history),
            'recent_actions': recent,
            'action_summary': action_types,
            'last_checkpoint': last_checkpoint,
            'last_conversation': recent[-1].get('conversation_id') if recent else None
        }
        
        return context
    
    def search_history(self, keyword, limit=20):
        """히스토리에서 키워드 검색"""
        history = self._load_history()
        results = []
        
        keyword_lower = keyword.lower()
        for entry in history:
            # action, details에서 검색
            if (keyword_lower in entry.get('action', '').lower() or 
                keyword_lower in str(entry.get('details', '')).lower()):
                results.append(entry)
        
        # 최근 순으로 정렬
        results = results[-limit:] if len(results) > limit else results
        
        return results
    
    def get_last_session_summary(self):
        """마지막 세션의 요약 정보"""
        history = self._load_history()
        if not history:
            return None
        
        # 마지막 대화 ID 찾기
        last_conv_id = None
        for entry in reversed(history):
            if entry.get('conversation_id'):
                last_conv_id = entry['conversation_id']
                break
        
        if not last_conv_id:
            return None
        
        # 해당 세션의 모든 액션 수집
        session_actions = [e for e in history if e.get('conversation_id') == last_conv_id]
        
        if not session_actions:
            return None
        
        # 요약 생성
        start_time = session_actions[0]['timestamp']
        end_time = session_actions[-1]['timestamp']
        
        # 주요 작업 식별
        major_actions = []
        for action in session_actions:
            if any(keyword in action['action'].lower() for keyword in ['완료', '생성', '구현', '추가']):
                major_actions.append(action)
        
        summary = {
            'conversation_id': last_conv_id,
            'start_time': start_time,
            'end_time': end_time,
            'total_actions': len(session_actions),
            'major_actions': major_actions[:5],  # 상위 5개만
            'has_checkpoints': any('checkpoint' in a for a in session_actions)
        }
        
        return summary
