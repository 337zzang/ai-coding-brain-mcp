#!/usr/bin/env python3
"""
Session Workflow Manager - 극도로 최적화된 워크플로우 관리 시스템
O3의 JSON 모델 적용: 99% 크기 절감, 100% 기능 유지
프로젝트별 독립적인 워크플로우 관리
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List

# 현재 프로젝트 정보를 저장할 전역 변수
CURRENT_PROJECT_PATH = os.getcwd()  # 기본값을 현재 디렉토리로

def get_current_project_path():
    """현재 프로젝트 경로 반환"""
    return CURRENT_PROJECT_PATH

def get_workflow_path():
    """프로젝트별 워크플로우 경로 반환"""
    project_path = get_current_project_path()
    return os.path.join(project_path, "memory", "workflow.json")

def get_history_path():
    """프로젝트별 히스토리 경로 반환"""
    project_path = get_current_project_path()
    return os.path.join(project_path, "memory", "workflow_history.json")

# 상태 코드
STATUS = {
    "new": "N",
    "running": "R", 
    "paused": "P",
    "done": "D",
    "cancelled": "X"
}

# 역방향 매핑 (디코딩용)
STATUS_DECODE = {v: k for k, v in STATUS.items()}


class WorkSession:
    """극도로 단순화된 워크플로우 세션 관리자"""

    def __init__(self):
        self.data = self._load_or_create()
        self.history = []  # 메모리 내 히스토리
        self.current_project_path = CURRENT_PROJECT_PATH  # 인스턴스 변수로도 저장

    def _load_or_create(self) -> Dict[str, Any]:
        """워크플로우 파일 로드 또는 생성"""
        workflow_file = get_workflow_path()
        if os.path.exists(workflow_file):
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"📄 워크플로우 로드: {workflow_file}")
                    return data
            except Exception as e:
                print(f"⚠️ 워크플로우 로드 실패: {e}")

        # 새 워크플로우 생성 (극도로 압축된 형태)
        return {
            "v": "1.0",
            "p": None,
            "s": "N",  # STATUS["new"] 대신 직접 값 사용
            "t": [],
            "f": None
        }

    def _save(self):
        """워크플로우 저장"""
        workflow_file = get_workflow_path()
        os.makedirs(os.path.dirname(workflow_file), exist_ok=True)
        with open(workflow_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, separators=(',', ':'))

    def _archive_to_history(self):
        """완료된 워크플로우를 히스토리에 추가"""
        if self.data["s"] in ["D", "X"]:  # STATUS 값 직접 사용
            history = []
            history_file = get_history_path()
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                except:
                    history = []

            # 간단한 요약만 저장
            summary = {
                "p": self.data.get("p", ""),
                "st": self.data.get("st", ""),
                "u": datetime.now().isoformat(),
                "s": self.data["s"],
                "t": len(self.data.get("t", []))
            }

            history.append(summary)
            # 최근 100개만 유지
            history = history[-100:]

            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, separators=(',', ':'))

    def start(self, title: str, desc: str = "") -> str:
        """새 워크플로우 시작"""
        self._archive_to_history()

        self.data = {
            "v": "1.0",
            "p": title,
            "s": "R",  # STATUS["running"] 대신 직접 값 사용
            "st": datetime.now().isoformat(),
            "t": [],
            "g": [],
            "c": None,
            "f": desc if desc else None
        }
        self._save()
        self._mcp_message("workflow_started", {"title": title})
        return f"✅ '{title}' 시작됨"

    def add_task(self, task_name: str) -> str:
        """태스크 추가"""
        task = {
            "i": len(self.data.get("t", [])) + 1,
            "n": task_name,
            "d": False
        }

        if "t" not in self.data:
            self.data["t"] = []

        self.data["t"].append(task)
        self._save()
        self._mcp_message("task_added", {"task": task_name})
        return f"📋 태스크 추가: {task_name}"

    def list_tasks(self) -> str:
        """태스크 목록 표시"""
        tasks = self.data.get("t", [])
        if not tasks:
            return "📋 태스크가 없습니다"

        lines = ["\n=== 📋 태스크 목록 ==="]
        for task in tasks:
            status = "✅" if task.get("d", False) else "⏳"
            skip = " (건너뜀)" if task.get("sk", False) else ""
            lines.append(f"{task['i']}. {status} {task['n']}{skip}")

        return "\n".join(lines)

    def complete_task(self, task_id: int = None) -> str:
        """태스크 완료"""
        tasks = self.data.get("t", [])
        if not tasks:
            return "❌ 태스크가 없습니다"

        if task_id is None:
            # 첫 번째 미완료 태스크 찾기
            for task in tasks:
                if not task.get("d", False) and not task.get("sk", False):
                    task["d"] = True
                    self._save()
                    return f"✅ 완료: {task['n']}"
            return "❌ 완료할 태스크가 없습니다"
        else:
            # 특정 ID의 태스크 완료
            for task in tasks:
                if task["i"] == task_id:
                    task["d"] = True
                    self._save()
                    return f"✅ 완료: {task['n']}"
            return f"❌ 태스크 {task_id}를 찾을 수 없습니다"

    def status(self) -> str:
        """현재 상태 표시"""
        if not self.data.get("p"):
            return "📊 진행 중인 워크플로우가 없습니다"

        tasks = self.data.get("t", [])
        done_count = sum(1 for t in tasks if t.get("d", False))
        total_count = len(tasks)
        progress = (done_count / total_count * 100) if total_count > 0 else 0

        status_text = STATUS_DECODE.get(self.data['s'], self.data['s'])

        lines = [
            "\n=== 📊 워크플로우 상태 ===",
            f"프로젝트: {self.data['p']}",
            f"상태: {status_text}",
            f"진행률: {progress:.1f}% ({done_count}/{total_count})",
        ]

        if self.data.get("f"):
            lines.append(f"포커스: {self.data['f']}")

        # 현재 진행 중인 태스크
        current_task = None
        for task in tasks:
            if not task.get("d", False) and not task.get("sk", False):
                current_task = task["n"]
                break

        if current_task:
            lines.append(f"현재 태스크: {current_task}")

        # 현재 프로젝트 경로 표시
        lines.append(f"\n📁 프로젝트 경로: {self.current_project_path}")

        return "\n".join(lines)

    def complete(self) -> str:
        """워크플로우 완료"""
        if not self.data.get("p"):
            return "❌ 진행 중인 워크플로우가 없습니다"

        self.data["s"] = "D"  # STATUS["done"] 대신 직접 값 사용
        self.data["u"] = datetime.now().isoformat()
        self._save()
        self._archive_to_history()

        title = self.data["p"]
        self._mcp_message("workflow_completed", {"title": title})
        return f"🎉 워크플로우 완료: {title}"

    def handle_command(self, cmd: str) -> str:
        """통합 명령어 처리"""
        parts = cmd.strip().split(maxsplit=2)
        if not parts:
            return "❌ 명령어를 입력하세요"

        command = parts[0].lower()

        # 명령어 매핑
        if command in ["/start", "/s"]:
            if len(parts) < 2:
                return "❌ 사용법: /start <프로젝트명> [설명]"
            title = parts[1]
            desc = parts[2] if len(parts) > 2 else ""
            return self.start(title, desc)

        elif command in ["/task", "/t"]:
            if len(parts) < 2:
                return self.list_tasks()

            sub_cmd = parts[1].lower()
            if sub_cmd == "list":
                return self.list_tasks()
            elif sub_cmd == "add" and len(parts) > 2:
                return self.add_task(parts[2])
            elif sub_cmd == "done":
                task_id = int(parts[2]) if len(parts) > 2 else None
                return self.complete_task(task_id)
            else:
                return self.add_task(" ".join(parts[1:]))

        elif command in ["/status", "/st"]:
            return self.status()

        elif command in ["/complete", "/done", "/c"]:
            return self.complete()

        elif command in ["/focus", "/f"]:
            if len(parts) < 2:
                focus = self.data.get("f", "없음")
                return f"🎯 현재 포커스: {focus}"
            else:
                self.data["f"] = " ".join(parts[1:])
                self._save()
                return f"🎯 포커스 설정: {self.data['f']}"

        elif command in ["/next", "/n"]:
            return self.complete_task()

        elif command in ["/skip"]:
            tasks = self.data.get("t", [])
            for task in tasks:
                if not task.get("d", False) and not task.get("sk", False):
                    task["sk"] = True
                    reason = " ".join(parts[1:]) if len(parts) > 1 else "건너뜀"
                    self._save()
                    return f"⏭️ 건너뜀: {task['n']} ({reason})"
            return "❌ 건너뛸 태스크가 없습니다"

        elif command == "/a":
            # 프로젝트 분석 명령 (외부에서 처리)
            return "PROJECT_ANALYSIS_REQUESTED"

        else:
            # 명령어가 아닌 경우 태스크로 추가
            return self.add_task(cmd)

    def _mcp_message(self, event: str, data: Dict[str, Any]):
        """MCP 프로토콜 메시지 출력"""
        print(f"MCP::{event} {json.dumps(data)}")
        sys.stdout.flush()

    def set_project(self, project_path: str):
        """프로젝트 전환 시 호출"""
        global CURRENT_PROJECT_PATH

        # 현재 워크플로우 저장
        if self.data.get("p"):
            self._save()

        # 새 프로젝트 경로 설정
        CURRENT_PROJECT_PATH = project_path
        self.current_project_path = project_path  # 인스턴스 변수도 업데이트

        # 새 프로젝트의 워크플로우 로드
        self.data = self._load_or_create()

        print(f"📂 워크플로우 전환: {os.path.basename(project_path)}")

    def checkpoint(self, message: str = ""):
        """체크포인트 생성 (Git 커밋 시 호출)"""
        if "cp" not in self.data:
            self.data["cp"] = []

        checkpoint = {
            "t": datetime.now().isoformat(),
            "m": message
        }

        self.data["cp"].append(checkpoint)
        # 최근 10개만 유지
        self.data["cp"] = self.data["cp"][-10:]
        self._save()


# 전역 세션 인스턴스
if 'WORK_SESSION' not in globals():
    WORK_SESSION = WorkSession()


# 헬퍼 함수들
def workflow(cmd: str) -> str:
    """메인 워크플로우 함수"""
    return WORK_SESSION.handle_command(cmd)

def work_start(title: str, desc: str = "") -> str:
    """워크플로우 시작"""
    return WORK_SESSION.start(title, desc)

def work_task(task: str) -> str:
    """태스크 추가"""
    return WORK_SESSION.add_task(task)

def work_status() -> str:
    """상태 확인"""
    return WORK_SESSION.status()

def work_complete() -> str:
    """워크플로우 완료"""
    return WORK_SESSION.complete()

def work_checkpoint(message: str = "") -> str:
    """체크포인트 생성"""
    WORK_SESSION.checkpoint(message)
    return f"💾 체크포인트 생성: {message}"

def work_set_project(project_path: str):
    """프로젝트 설정 (내부용)"""
    WORK_SESSION.set_project(project_path)


# 테스트용 코드
if __name__ == "__main__":
    print("Session Workflow Manager - Test Mode")
    print(workflow("/status"))
