#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Version Manager - AI Coding Brain MCP
프로젝트의 모든 Git 관련 작업을 총괄하는 중앙 관리자

주요 기능:
- 자동 커밋 및 스마트 커밋 메시지 생성
- 작업 기반 브랜치 관리
- 안전한 롤백 및 복원
- Wisdom 시스템 통합

작성일: 2025-06-26
"""

import os
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import platform

# Windows에서 Git 경로 설정
GIT_CMD = "git"
if platform.system() == "Windows":
    # Windows에서 Git 실행 파일 찾기
    import shutil
    
    # PATH에 Git 경로 추가 (MCP 환경에서도 작동하도록)
    git_paths = [
        r"C:\Program Files\Git\cmd",
        r"C:\Program Files\Git\bin",
        r"C:\Program Files (x86)\Git\cmd",
        r"C:\Program Files (x86)\Git\bin"
    ]
    
    for path in git_paths:
        if os.path.exists(path) and path not in os.environ.get('PATH', ''):
            os.environ['PATH'] = path + ';' + os.environ.get('PATH', '')
    
    git_path = shutil.which("git")
    if git_path:
        GIT_CMD = git_path
    else:
        # 기본 경로 시도
        default_path = r"C:\Program Files\Git\cmd\git.exe"
        if os.path.exists(default_path):
            GIT_CMD = default_path

# Wisdom 시스템 통합
try:
    from project_wisdom import get_wisdom_manager
    WISDOM_AVAILABLE = True
except ImportError:
    WISDOM_AVAILABLE = False


class GitVersionManager:
    """Git 기반 버전 관리 및 백업 시스템"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.project_name = self.project_root.name
        self.git_dir = self.project_root / ".git"
        
        # Git 초기화 확인
        if not self.git_dir.exists():
            self._init_git()
        
        # Wisdom 매니저
        self.wisdom = get_wisdom_manager() if WISDOM_AVAILABLE else None
        
    def _init_git(self) -> bool:
        """Git 저장소 초기화"""
        try:
            result = subprocess.run(
                [GIT_CMD, "init"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding='utf-8',  # Windows 인코딩 명시
                errors='replace'   # 인코딩 에러 시 대체 문자 사용
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Git 초기화 실패: {e}")
            return False
    
    def _run_git_command(self, cmd: List[str]) -> Tuple[bool, str, str]:
        """Git 명령 실행"""
        try:
            result = subprocess.run(
                [GIT_CMD] + cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding='utf-8',  # Windows 인코딩 명시
                errors='replace'   # 인코딩 에러 시 대체 문자 사용
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def git_status(self) -> Dict[str, Any]:
        """현재 Git 상태 확인"""
        status = {
            "branch": None,
            "modified": [],
            "untracked": [],
            "staged": [],
            "clean": True
        }
        
        # 현재 브랜치 확인
        success, stdout, _ = self._run_git_command(["branch", "--show-current"])
        if success:
            status["branch"] = stdout.strip() or "main"
        
        # 변경 사항 확인
        success, stdout, stderr = self._run_git_command(["status", "--porcelain"])
        if success and stdout:
            lines = stdout.strip().split('\n')
            for line in lines:
                if not line or len(line) < 3:  # 최소 길이 체크
                    continue
                    
                status["clean"] = False
                status_code = line[:2]
                file_path = line[3:]
                
                if status_code == "??":
                    status["untracked"].append(file_path)
                elif status_code[0] in "AM":
                    status["staged"].append(file_path)
                elif status_code[1] == "M":
                    status["modified"].append(file_path)
                    status["staged"].append(file_path)
                elif status_code[1] == "M":
                    status["modified"].append(file_path)
        
        return status
    
    def git_commit_smart(self, message: Optional[str] = None, auto_add: bool = True) -> Dict[str, Any]:
        """스마트 커밋 - 자동 메시지 생성 및 Wisdom 통합"""
        result = {
            "success": False,
            "message": "",
            "commit_hash": None,
            "files_committed": []
        }
        
        # 상태 확인
        status = self.git_status()
        if status["clean"] and not status["staged"]:
            result["message"] = "No changes to commit."
            return result
        
        # 자동 스테이징
        if auto_add:
            self._run_git_command(["add", "-A"])
            status = self.git_status()  # 다시 확인
        
        # 커밋 메시지 생성
        if not message:
            message = self._generate_smart_commit_message(status)
        
        # 커밋 실행
        success, stdout, stderr = self._run_git_command(["commit", "-m", message])
        
        if success:
            # 커밋 해시 가져오기
            hash_success, commit_hash, _ = self._run_git_command(["rev-parse", "HEAD"])
            result["success"] = True
            result["commit_hash"] = commit_hash.strip()[:8] if hash_success else None
            result["message"] = f"Commit successful: {message}"
            result["files_committed"] = status["staged"] + status["modified"] + status["untracked"]
            
            # Wisdom에 기록
            if self.wisdom:
                self.wisdom.track_commit(result["commit_hash"], message)
        else:
            result["message"] = f"Commit failed: {stderr}"
        
        return result
    
    def _generate_smart_commit_message(self, status: Dict[str, Any]) -> str:
        """컨텍스트 기반 스마트 커밋 메시지 생성"""
        # 현재 작업 컨텍스트 가져오기
        context = self._get_current_context()
        
        # 변경 파일 분석
        all_files = status["modified"] + status["staged"] + status["untracked"]
        
        # 파일 타입별 분류
        py_files = [f for f in all_files if f.endswith('.py')]
        ts_files = [f for f in all_files if f.endswith('.ts')]
        md_files = [f for f in all_files if f.endswith('.md')]
        
        # 메시지 구성
        parts = []
        
        # 작업 컨텍스트
        if context.get("current_task"):
            parts.append(f"[{context['current_task']}]")
        elif context.get("current_phase"):
            parts.append(f"[{context['current_phase']}]")
        
        # 변경 내용 요약
        changes = []
        if py_files:
            changes.append(f"Python {len(py_files)}개")
        if ts_files:
            changes.append(f"TypeScript {len(ts_files)}개")
        if md_files:
            changes.append(f"문서 {len(md_files)}개")
        
        if changes:
            parts.append(f"수정: {', '.join(changes)}")
        else:
            parts.append(f"{len(all_files)}개 파일 변경")
        
        # 시간 추가
        parts.append(datetime.now().strftime("%H:%M"))
        
        return " ".join(parts)
    
    def _get_current_context(self) -> Dict[str, Any]:
        """현재 작업 컨텍스트 가져오기"""
        context_file = self.project_root / "memory" / ".cache" / "cache_core.json"
        if context_file.exists():
            try:
                with open(context_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        "current_task": data.get("current_task"),
                        "current_phase": data.get("current_phase", "work")
                    }
            except:
                pass
        
        return {"current_task": None, "current_phase": "work"}
    
    def git_branch_smart(self, branch_name: Optional[str] = None, base_branch: str = "main") -> Dict[str, Any]:
        """스마트 브랜치 생성"""
        result = {
            "success": False,
            "branch_name": "",
            "message": ""
        }
        
        # 브랜치 이름 자동 생성
        if not branch_name:
            context = self._get_current_context()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            
            if context.get("current_task"):
                branch_name = f"task/{context['current_task']}_{timestamp}"
            else:
                branch_name = f"work/{timestamp}"
        
        # 현재 변경사항 커밋
        if not self.git_status()["clean"]:
            commit_result = self.git_commit_smart("WIP: 브랜치 전환 전 자동 저장")
            if not commit_result["success"]:
                result["message"] = "변경사항 커밋 실패"
                return result
        
        # 브랜치 생성 및 전환
        success, _, stderr = self._run_git_command(["checkout", "-b", branch_name, base_branch])
        
        if success:
            result["success"] = True
            result["branch_name"] = branch_name
            result["message"] = f"브랜치 '{branch_name}' 생성 및 전환 완료"
        else:
            result["message"] = f"브랜치 생성 실패: {stderr}"
        
        return result
    
    def git_rollback_smart(self, target: Optional[str] = None, safe_mode: bool = True) -> Dict[str, Any]:
        """안전한 롤백"""
        result = {
            "success": False,
            "message": "",
            "backup_branch": None,
            "rolled_back_to": None
        }
        
        # 현재 상태 백업 (safe_mode)
        if safe_mode:
            backup_branch = f"backup/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_success, _, _ = self._run_git_command(["checkout", "-b", backup_branch])
            if backup_success:
                result["backup_branch"] = backup_branch
                # 원래 브랜치로 돌아가기
                self._run_git_command(["checkout", "-"])
        
        # 타겟 결정
        if not target:
            # 마지막 안정적인 커밋 찾기
            if self.wisdom:
                target = self.wisdom.get_last_stable_commit()
            
            if not target:
                # 최근 커밋 3개 중 선택
                success, stdout, _ = self._run_git_command(["log", "--oneline", "-3"])
                if success:
                    commits = stdout.strip().split('\n')
                    if len(commits) >= 2:
                        target = commits[1].split()[0]  # 이전 커밋
        
        if not target:
            result["message"] = "롤백 대상을 찾을 수 없습니다"
            return result
        
        # 롤백 실행
        success, _, stderr = self._run_git_command(["reset", "--hard", target])
        
        if success:
            result["success"] = True
            result["rolled_back_to"] = target
            result["message"] = f"'{target}'로 롤백 완료"
            
            # Wisdom에 기록
            if self.wisdom:
                self.wisdom.track_rollback(target, "Manual rollback")
        else:
            result["message"] = f"롤백 실패: {stderr}"
        
        return result
    
    def git_push(self, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        """원격 저장소로 푸시"""
        result = {
            "success": False,
            "message": "",
            "pushed_branch": None
        }
        
        # 현재 브랜치 확인
        if not branch:
            status = self.git_status()
            branch = status["branch"] or "main"
        
        # 원격 저장소 확인
        check_remote, stdout, _ = self._run_git_command(["remote", "-v"])
        if not check_remote or remote not in stdout:
            result["message"] = f"원격 저장소 '{remote}'가 설정되지 않았습니다. GitHub 저장소를 먼저 연결하세요."
            result["help"] = "git remote add origin https://github.com/USERNAME/REPO.git"
            return result
        
        # 푸시 실행
        success, stdout, stderr = self._run_git_command(["push", remote, branch])
        
        if success:
            result["success"] = True
            result["pushed_branch"] = branch
            result["message"] = f"'{branch}' 브랜치를 '{remote}'로 푸시 완료"
        else:
            # 업스트림 설정이 필요한 경우
            if "no upstream" in stderr:
                success, _, _ = self._run_git_command(["push", "--set-upstream", remote, branch])
                if success:
                    result["success"] = True
                    result["pushed_branch"] = branch
                    result["message"] = f"Pushed '{branch}' to '{remote}' successfully (upstream set)"
                else:
                    result["message"] = f"Push failed: {stderr}"
            elif "Authentication failed" in stderr or "could not read Username" in stderr:
                result["message"] = "Authentication failed: GitHub Personal Access Token required."
                result["help"] = "Please refer to GITHUB_SETUP.md for PAT setup."
            else:
                result["message"] = f"Push failed: {stderr}"
        
        return result
    
    def setup_remote(self, url: str, name: str = "origin") -> Dict[str, Any]:
        """원격 저장소 설정"""
        result = {
            "success": False,
            "message": ""
        }
        
        # 기존 원격 저장소 확인
        check, stdout, _ = self._run_git_command(["remote", "-v"])
        
        if check and name in stdout:
            # 기존 URL 업데이트
            success, _, stderr = self._run_git_command(["remote", "set-url", name, url])
        else:
            # 새로 추가
            success, _, stderr = self._run_git_command(["remote", "add", name, url])
        
        if success:
            result["success"] = True
            result["message"] = f"Remote repository '{name}' configured: {url}"
        else:
            result["message"] = f"Failed to configure remote repository: {stderr}"
        
        return result


# 싱글톤 인스턴스
_git_manager = None

def get_git_manager(project_root: Optional[str] = None) -> GitVersionManager:
    """Git Manager 싱글톤 인스턴스"""
    global _git_manager
    if _git_manager is None:
        # 프로젝트 루트가 지정되지 않으면 현재 작업 디렉토리 사용
        if project_root is None:
            project_root = os.getcwd()
        _git_manager = GitVersionManager(project_root)
    return _git_manager
