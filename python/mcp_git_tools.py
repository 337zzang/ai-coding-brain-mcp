#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP Git Tools - AI Coding Brain MCP
Git 기능을 MCP 도구로 노출하는 모듈

작성일: 2025-06-26
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path

# Git Version Manager import
from git_version_manager import get_git_manager

# Wisdom 시스템
try:
    from project_wisdom import get_wisdom_manager
    WISDOM_AVAILABLE = True
except ImportError:
    WISDOM_AVAILABLE = False


def git_status() -> Dict[str, Any]:
    """
    현재 Git 상태 확인
    
    Returns:
        변경된 파일 목록과 브랜치 정보
    """
    try:
        git_manager = get_git_manager()
        status = git_manager.git_status()
        
        # 사용자 친화적인 메시지 생성
        message_parts = [f"📌 브랜치: {status['branch']}"]
        
        if status['clean']:
            message_parts.append("✅ 작업 디렉토리가 깨끗합니다.")
        else:
            if status['modified']:
                message_parts.append(f"📝 수정됨: {len(status['modified'])}개")
            if status['untracked']:
                message_parts.append(f"🆕 추적 안됨: {len(status['untracked'])}개")
            if status['staged']:
                message_parts.append(f"✅ 스테이징됨: {len(status['staged'])}개")
        
        return {
            "success": True,
            "status": status,
            "message": "\n".join(message_parts)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ Git 상태 확인 실패: {e}"
        }


def git_commit_smart(message: Optional[str] = None, auto_add: bool = True) -> Dict[str, Any]:
    """
    스마트 Git 커밋 (백업)
    
    Args:
        message: 커밋 메시지 (없으면 자동 생성)
        auto_add: 변경 사항 자동 스테이징 여부
        
    Returns:
        커밋 결과
    """
    try:
        git_manager = get_git_manager()
        result = git_manager.git_commit_smart(message, auto_add)
        
        if result['success']:
            # Wisdom 시스템에 성공 기록
            if WISDOM_AVAILABLE:
                wisdom = get_wisdom_manager()
                wisdom.add_best_practice(
                    "Git 커밋으로 작업 백업 완료",
                    category="backup"
                )
            
            return {
                "success": True,
                "commit_hash": result['commit_hash'],
                "files_committed": result['files_committed'],
                "message": f"✅ {result['message']}\n💾 커밋 해시: {result['commit_hash']}"
            }
        else:
            return {
                "success": False,
                "message": result['message']
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ 커밋 실패: {e}"
        }


def git_branch_smart(branch_name: Optional[str] = None, base_branch: str = "main") -> Dict[str, Any]:
    """
    스마트 브랜치 생성
    
    Args:
        branch_name: 브랜치 이름 (없으면 자동 생성)
        base_branch: 기반 브랜치
        
    Returns:
        브랜치 생성 결과
    """
    try:
        git_manager = get_git_manager()
        result = git_manager.git_branch_smart(branch_name, base_branch)
        
        if result['success']:
            return {
                "success": True,
                "branch_name": result['branch_name'],
                "message": f"🌿 {result['message']}"
            }
        else:
            return {
                "success": False,
                "message": result['message']
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ 브랜치 생성 실패: {e}"
        }


def git_rollback_smart(target: Optional[str] = None, safe_mode: bool = True) -> Dict[str, Any]:
    """
    안전한 Git 롤백 (복원)
    
    Args:
        target: 롤백 대상 커밋 (없으면 자동 선택)
        safe_mode: 백업 브랜치 생성 여부
        
    Returns:
        롤백 결과
    """
    try:
        git_manager = get_git_manager()
        result = git_manager.git_rollback_smart(target, safe_mode)
        
        if result['success']:
            message_parts = [f"⏪ {result['message']}"]
            if result['backup_branch']:
                message_parts.append(f"💾 백업 브랜치: {result['backup_branch']}")
            
            # Wisdom에 롤백 기록
            if WISDOM_AVAILABLE:
                wisdom = get_wisdom_manager()
                wisdom.track_mistake("rollback_needed", f"롤백 to {result['rolled_back_to']}")
            
            return {
                "success": True,
                "rolled_back_to": result['rolled_back_to'],
                "backup_branch": result['backup_branch'],
                "message": "\n".join(message_parts)
            }
        else:
            return {
                "success": False,
                "message": result['message']
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ 롤백 실패: {e}"
        }


def git_push(remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
    """
    원격 저장소로 푸시
    
    Args:
        remote: 원격 저장소 이름
        branch: 브랜치 이름 (없으면 현재 브랜치)
        
    Returns:
        푸시 결과
    """
    try:
        git_manager = get_git_manager()
        result = git_manager.git_push(remote, branch)
        
        if result['success']:
            return {
                "success": True,
                "pushed_branch": result['pushed_branch'],
                "message": f"🚀 {result['message']}"
            }
        else:
            return {
                "success": False,
                "message": result['message']
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"❌ 푸시 실패: {e}"
        }


# MCP 도구로 export할 함수들
__all__ = [
    'git_status',
    'git_commit_smart',
    'git_branch_smart',
    'git_rollback_smart',
    'git_push'
]
