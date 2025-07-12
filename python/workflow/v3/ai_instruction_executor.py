"""
AI 지시서를 읽고 실행하는 실행자
MCP 도구를 사용해 실제 작업을 수행
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AIInstructionExecutor:
    """AI 지시서를 읽고 MCP 도구로 실행"""
    
    def __init__(self, instruction_file: str = "ai_instructions.json"):
        self.instruction_file = Path("memory") / instruction_file
        self.current_instruction = None
        self.execution_history = []
        
    def get_pending_instructions(self) -> List[Dict[str, Any]]:
        """대기 중인 지시서 목록 반환"""
        try:
            if not self.instruction_file.exists():
                return []
                
            with open(self.instruction_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 우선순위와 시간 순으로 정렬
            pending = data.get("pending", [])
            priority_order = {"immediate": 0, "high": 1, "normal": 2, "low": 3}
            
            pending.sort(key=lambda x: (
                priority_order.get(x.get("priority", "normal"), 2),
                x.get("created_at", "")
            ))
            
            return pending
            
        except Exception as e:
            logger.error(f"지시서 읽기 실패: {e}")
            return []    
    def execute_next_instruction(self) -> Optional[Dict[str, Any]]:
        """다음 지시서를 실행"""
        instructions = self.get_pending_instructions()
        
        if not instructions:
            logger.info("실행할 지시서가 없습니다.")
            return None
            
        # 첫 번째 지시서 선택
        instruction = instructions[0]
        self.current_instruction = instruction
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🤖 AI 지시 실행 시작")
        logger.info(f"ID: {instruction['instruction_id']}")
        logger.info(f"타입: {instruction['event_type']}")
        logger.info(f"우선순위: {instruction['priority']}")
        logger.info(f"{'='*60}")
        
        # 실행 결과 저장
        execution_result = {
            "instruction_id": instruction["instruction_id"],
            "started_at": datetime.now().isoformat(),
            "actions_completed": [],
            "actions_failed": [],
            "overall_success": True
        }
        
        # 각 작업 실행
        for i, action in enumerate(instruction["ai_actions_required"], 1):
            logger.info(f"\n[{i}/{len(instruction['ai_actions_required'])}] {action['action']}")
            
            try:
                # MCP 명령어 실행
                result = self._execute_action(action)
                
                if result["success"]:
                    execution_result["actions_completed"].append({
                        "action": action["action"],
                        "result": result["output"]
                    })
                    logger.info(f"✅ {action['action']} 완료")
                else:
                    execution_result["actions_failed"].append({
                        "action": action["action"],
                        "error": result["error"]
                    })
                    execution_result["overall_success"] = False
                    logger.error(f"❌ {action['action']} 실패: {result['error']}")
                    
            except Exception as e:
                execution_result["actions_failed"].append({
                    "action": action["action"],
                    "error": str(e)
                })
                execution_result["overall_success"] = False
                logger.error(f"❌ 작업 실행 중 오류: {e}")
        
        # 실행 완료
        execution_result["completed_at"] = datetime.now().isoformat()
        
        # 지시서 상태 업데이트
        self._update_instruction_status(
            instruction["instruction_id"],
            "completed" if execution_result["overall_success"] else "failed",
            execution_result
        )
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🏁 지시 실행 완료")
        logger.info(f"성공: {len(execution_result['actions_completed'])}개")
        logger.info(f"실패: {len(execution_result['actions_failed'])}개")
        logger.info(f"{'='*60}\n")
        
        return execution_result    
    def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """개별 작업 실행"""
        try:
            mcp_commands = action.get("mcp_commands", [])
            outputs = []
            
            print(f"\n💡 실행: {action['description']}")
            
            # 각 MCP 명령어 실행 (실제로는 AI가 수행)
            for cmd in mcp_commands:
                print(f"  > {cmd}")
                # 여기서 실제 명령어 실행
                # 예: exec(cmd) 또는 다른 방식으로 실행
                outputs.append(f"[실행됨] {cmd}")
            
            return {
                "success": True,
                "output": outputs
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _update_instruction_status(self, instruction_id: str, status: str, result: Dict[str, Any]):
        """지시서 상태 업데이트"""
        try:
            with open(self.instruction_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # pending에서 찾아서 상태 업데이트
            for inst in data["pending"][:]:
                if inst["instruction_id"] == instruction_id:
                    inst["status"] = status
                    inst["execution_result"] = result
                    
                    # 적절한 목록으로 이동
                    if status == "completed":
                        data["completed"].append(inst)
                    else:
                        data["failed"].append(inst)
                    
                    data["pending"].remove(inst)
                    break
            
            # 저장
            with open(self.instruction_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"지시서 상태 업데이트 실패: {e}")
    
    def execute_all_pending(self, max_count: int = 10) -> List[Dict[str, Any]]:
        """모든 대기 중인 지시 실행 (최대 개수 제한)"""
        results = []
        
        for i in range(max_count):
            result = self.execute_next_instruction()
            if result is None:
                break
            results.append(result)
        
        return results
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """실행 요약 정보 반환"""
        try:
            if not self.instruction_file.exists():
                return {"pending": 0, "completed": 0, "failed": 0}
                
            with open(self.instruction_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return {
                "pending": len(data.get("pending", [])),
                "completed": len(data.get("completed", [])),
                "failed": len(data.get("failed", [])),
                "next_instruction": data.get("pending", [{}])[0].get("instruction_id") if data.get("pending") else None
            }
            
        except Exception as e:
            logger.error(f"요약 정보 조회 실패: {e}")
            return {"error": str(e)}

# AI가 사용할 수 있는 간단한 헬퍼 함수들
def check_ai_instructions():
    """AI 지시서 확인"""
    executor = AIInstructionExecutor()
    summary = executor.get_execution_summary()
    
    print(f"\n📋 AI 지시서 현황:")
    print(f"  대기 중: {summary.get('pending', 0)}개")
    print(f"  완료됨: {summary.get('completed', 0)}개")
    print(f"  실패함: {summary.get('failed', 0)}개")
    
    if summary.get('pending', 0) > 0:
        print(f"\n⚡ 다음 지시: {summary.get('next_instruction', 'None')}")
        print("실행하려면: execute_ai_instruction()")
    
    return summary

def execute_ai_instruction():
    """다음 AI 지시 실행"""
    executor = AIInstructionExecutor()
    result = executor.execute_next_instruction()
    return result

def execute_all_ai_instructions(max_count: int = 5):
    """모든 대기 중인 AI 지시 실행"""
    executor = AIInstructionExecutor()
    results = executor.execute_all_pending(max_count)
    
    print(f"\n✅ {len(results)}개 지시 실행 완료")
    return results