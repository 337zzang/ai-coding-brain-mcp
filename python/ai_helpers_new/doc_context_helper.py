"""문서 작업 시 Context 기록을 위한 헬퍼"""
import os
from typing import Optional, List, Dict, Any
from .flow_context_wrapper import record_doc_creation, record_doc_update, get_related_docs

def create_doc_with_context(
    doc_path: str,
    content: str,
    doc_type: str = "general",
    related_to: Optional[Dict[str, str]] = None,
    summary: Optional[str] = None
) -> bool:
    """문서 생성 및 Context 기록

    Args:
        doc_path: 문서 경로 (예: docs/flow-improvement/new_feature.md)
        content: 문서 내용
        doc_type: 문서 타입 (design, report, analysis, guide 등)
        related_to: 관련 문서 정보 {"doc_path": "...", "relation": "..."}
        summary: 문서 요약

    Returns:
        bool: 성공 여부
    """
    try:
        # 디렉토리 생성
        os.makedirs(os.path.dirname(doc_path), exist_ok=True)

        # 문서 저장
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Context 기록
        details = related_to or {}
        if summary:
            details["summary"] = summary

        record_doc_creation(doc_path, doc_type, details)

        print(f"문서 생성 및 Context 기록 완료: {doc_path}")
        return True

    except Exception as e:
        print(f"문서 생성 실패: {e}")
        return False

def update_doc_with_context(
    doc_path: str,
    content: str,
    update_type: str = "content",
    summary: str = ""
) -> bool:
    """문서 수정 및 Context 기록

    Args:
        doc_path: 문서 경로
        content: 새로운 내용
        update_type: 수정 타입 (content, format, merge, append 등)
        summary: 수정 내용 요약

    Returns:
        bool: 성공 여부
    """
    try:
        # 기존 문서 백업 (선택적)
        if os.path.exists(doc_path):
            with open(doc_path, 'r', encoding='utf-8') as f:
                old_content = f.read()

            # 간단한 변경 감지
            if not summary and len(content) != len(old_content):
                lines_diff = len(content.splitlines()) - len(old_content.splitlines())
                if lines_diff > 0:
                    summary = f"{lines_diff}줄 추가"
                elif lines_diff < 0:
                    summary = f"{-lines_diff}줄 삭제"
                else:
                    summary = "내용 수정"

        # 문서 저장
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Context 기록
        record_doc_update(doc_path, update_type, summary)

        print(f"문서 수정 및 Context 기록 완료: {doc_path}")
        return True

    except Exception as e:
        print(f"문서 수정 실패: {e}")
        return False

def suggest_related_docs_for_new(
    category: str,
    keywords: List[str] = None
) -> List[Dict[str, Any]]:
    """새 문서 작성 시 참고할 관련 문서 추천

    Args:
        category: 문서 카테고리 (flow-improvement, design, report 등)
        keywords: 관련 키워드 리스트

    Returns:
        List[Dict]: 추천 문서 리스트
    """
    if os.environ.get('CONTEXT_SYSTEM', 'off') != 'on':
        return []

    try:
        from .context_integration import get_context_integration
        context = get_context_integration()

        # docs_context 읽기
        with open(context.docs_context_file, 'r') as f:
            import json
            docs_context = json.load(f)

        recommendations = []

        # 같은 카테고리의 최근 문서들
        for doc_path, doc_info in docs_context["documents"].items():
            if doc_info.get("category") == category:
                score = 1.0

                # 키워드 매칭으로 점수 조정
                if keywords:
                    doc_name = os.path.basename(doc_path).lower()
                    for keyword in keywords:
                        if keyword.lower() in doc_name:
                            score += 0.2

                recommendations.append({
                    "path": doc_path,
                    "category": category,
                    "last_modified": doc_info["last_modified"],
                    "score": score,
                    "actions_count": len(doc_info.get("actions", []))
                })

        # 점수 순으로 정렬
        recommendations.sort(key=lambda x: (x["score"], x["last_modified"]), reverse=True)

        return recommendations[:10]

    except Exception as e:
        print(f"관련 문서 추천 실패: {e}")
        return []

def generate_doc_template(doc_type: str, title: str, related_docs: List[str] = None) -> str:
    """문서 타입에 맞는 템플릿 생성

    Args:
        doc_type: 문서 타입
        title: 문서 제목
        related_docs: 관련 문서 경로 리스트

    Returns:
        str: 문서 템플릿
    """
    from datetime import datetime

    templates = {
        "design": f"""# {title}

## 개요
[설계 목적과 배경 설명]

## 목표
- [주요 목표 1]
- [주요 목표 2]

## 현재 상태 분석
[현재 시스템/코드의 상태]

## 제안하는 설계
### 아키텍처
[전체 구조 설명]

### 주요 컴포넌트
1. **컴포넌트 1**
   - 역할: 
   - 인터페이스:

### 구현 계획
1. [단계 1]
2. [단계 2]

## 고려사항
- [기술적 고려사항]
- [성능 고려사항]

---
생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",

        "report": f"""# {title}

## 요약
[작업 결과 요약]

## 작업 내용
### 수행한 작업
1. [작업 1]
2. [작업 2]

### 주요 변경사항
- [변경 1]
- [변경 2]

## 결과
### 성공 사항
- [성공 1]

### 문제점 및 해결
- 문제: [문제 설명]
  해결: [해결 방법]

## 테스트 결과
[테스트 수행 결과]

## 다음 단계
- [후속 작업 1]
- [후속 작업 2]

---
작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""",

        "analysis": f"""# {title}

## 분석 개요
[분석 목적과 범위]

## 분석 대상
- [대상 1]
- [대상 2]

## 분석 방법
[사용한 분석 방법론]

## 분석 결과
### 발견사항
1. **발견 1**
   - 상세: 
   - 영향:

### 통계/메트릭
| 항목 | 값 | 설명 |
|------|-----|------|
| 메트릭1 | 0 | 설명 |

## 결론 및 제안
### 결론
[주요 결론]

### 개선 제안
1. [제안 1]
2. [제안 2]

---
분석일: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    }

    template = templates.get(doc_type, f"# {title}\n\n[내용 작성]\n\n---\n생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 관련 문서 추가
    if related_docs:
        related_section = "\n## 관련 문서\n"
        for doc in related_docs:
            doc_name = os.path.basename(doc)
            related_section += f"- [{doc_name}]({doc})\n"

        # 템플릿 끝에 추가
        template = template.replace("---\n", f"{related_section}\n---\n")

    return template
