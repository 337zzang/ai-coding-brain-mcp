"""문서 작업 시 Context 기록을 위한 헬퍼 - Ultra Simple Version"""
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

def create_doc_with_context(
    doc_path: str,
    content: str,
    doc_type: str = "general",
    related_to: Optional[Dict[str, str]] = None,
    summary: Optional[str] = None
) -> bool:
    """문서 생성 - 간단한 버전"""
    try:
        # 디렉토리 생성
        os.makedirs(os.path.dirname(doc_path), exist_ok=True)
        
        # 문서 저장
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Context 기록 (간단히)
        context_dir = ".ai-brain/contexts"
        os.makedirs(context_dir, exist_ok=True)
        
        doc_context = {
            "path": doc_path,
            "type": doc_type,
            "created_at": datetime.now().isoformat(),
            "summary": summary or f"Created {doc_type} document",
            "related_to": related_to or {}
        }
        
        # 컨텍스트 파일에 추가
        context_file = os.path.join(context_dir, "docs_context.json")
        contexts = []
        if os.path.exists(context_file):
            with open(context_file, 'r', encoding='utf-8') as f:
                contexts = json.load(f)
        
        contexts.append(doc_context)
        
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(contexts, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error creating doc: {e}")
        return False

def update_doc_with_context(
    doc_path: str,
    content: str,
    update_type: str = "update",
    summary: Optional[str] = None
) -> bool:
    """문서 업데이트 - 간단한 버전"""
    return create_doc_with_context(doc_path, content, update_type, summary=summary)

def suggest_related_docs_for_new(
    doc_type: str,
    keywords: List[str] = None
) -> List[Dict[str, Any]]:
    """관련 문서 제안 - 간단한 버전"""
    # 간단히 빈 리스트 반환
    return []

def generate_doc_template(doc_type: str) -> str:
    """문서 템플릿 생성"""
    templates = {
        "analysis": """# 분석 문서

## 개요

## 주요 발견사항

## 결론
""",
        "design": """# 설계 문서

## 목표

## 아키텍처

## 구현 계획
""",
        "report": """# 보고서

## 요약

## 상세 내용

## 다음 단계
""",
        "general": """# 문서 제목

## 내용

"""
    }
    
    return templates.get(doc_type, templates["general"])
