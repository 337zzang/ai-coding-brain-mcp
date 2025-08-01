"""Context System 통합 모듈 - Flow 작업 및 문서 추적"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

class ContextIntegration:
    """Flow 작업 및 문서 작업을 Context에 통합 기록"""

    def __init__(self, base_path: str = ".ai-brain"):
        self.base_path = base_path
        self.contexts_dir = os.path.join(base_path, "contexts")
        self.docs_context_file = os.path.join(self.contexts_dir, "docs_context.json")
        self._ensure_directories()

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        os.makedirs(self.contexts_dir, exist_ok=True)

        # docs_context 초기화
        if not os.path.exists(self.docs_context_file):
            self._init_docs_context()

    def _init_docs_context(self):
        """문서 Context 초기화"""
        initial_context = {
            "created_at": datetime.now().isoformat(),
            "documents": {},
            "references": [],
            "categories": {},
            "recent_activities": []
        }
        with open(self.docs_context_file, 'w') as f:
            json.dump(initial_context, f, indent=2)

    def record_flow_action(self, flow_id: str, action_type: str, details: Dict[str, Any]):
        """Flow 관련 작업 기록"""
        flow_context_dir = os.path.join(self.contexts_dir, f"flow_{flow_id}")
        os.makedirs(flow_context_dir, exist_ok=True)

        context_file = os.path.join(flow_context_dir, "context.json")

        # 기존 Context 읽기 또는 새로 생성
        if os.path.exists(context_file):
            with open(context_file, 'r') as f:
                context = json.load(f)
        else:
            context = {
                "flow_id": flow_id,
                "created_at": datetime.now().isoformat(),
                "actions": [],
                "statistics": {}
            }

        # 새 액션 추가
        action = {
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "details": details
        }
        context["actions"].append(action)

        # 통계 업데이트
        if action_type not in context["statistics"]:
            context["statistics"][action_type] = 0
        context["statistics"][action_type] += 1

        # 저장
        with open(context_file, 'w') as f:
            json.dump(context, f, indent=2, default=str)

    def record_doc_action(self, doc_path: str, action_type: str, details: Dict[str, Any]):
        """문서 관련 작업 기록"""
        # docs_context 읽기
        with open(self.docs_context_file, 'r') as f:
            docs_context = json.load(f)

        # 문서 정보 업데이트
        if doc_path not in docs_context["documents"]:
            docs_context["documents"][doc_path] = {
                "first_seen": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "actions": [],
                "references": [],
                "category": self._determine_category(doc_path)
            }

        doc_info = docs_context["documents"][doc_path]
        doc_info["last_modified"] = datetime.now().isoformat()

        # 액션 기록
        action = {
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "details": details
        }
        doc_info["actions"].append(action)

        # 최근 활동에 추가
        recent_activity = {
            "timestamp": datetime.now().isoformat(),
            "doc_path": doc_path,
            "action": action_type,
            "summary": details.get("summary", "")
        }
        docs_context["recent_activities"].insert(0, recent_activity)
        docs_context["recent_activities"] = docs_context["recent_activities"][:100]  # 최근 100개만 유지

        # 카테고리 통계 업데이트
        category = doc_info["category"]
        if category not in docs_context["categories"]:
            docs_context["categories"][category] = {"count": 0, "last_updated": ""}
        docs_context["categories"][category]["count"] += 1
        docs_context["categories"][category]["last_updated"] = datetime.now().isoformat()

        # 저장
        with open(self.docs_context_file, 'w') as f:
            json.dump(docs_context, f, indent=2, default=str)

    def record_doc_reference(self, from_doc: str, to_doc: str, reference_type: str = "link"):
        """문서 간 참조 관계 기록"""
        with open(self.docs_context_file, 'r') as f:
            docs_context = json.load(f)

        reference = {
            "from": from_doc,
            "to": to_doc,
            "type": reference_type,
            "timestamp": datetime.now().isoformat()
        }

        docs_context["references"].append(reference)

        # 각 문서의 참조 정보도 업데이트
        for doc in [from_doc, to_doc]:
            if doc in docs_context["documents"]:
                if "references" not in docs_context["documents"][doc]:
                    docs_context["documents"][doc]["references"] = []
                docs_context["documents"][doc]["references"].append(reference)

        with open(self.docs_context_file, 'w') as f:
            json.dump(docs_context, f, indent=2, default=str)

    def get_related_docs(self, doc_path: str, limit: int = 5) -> List[Dict[str, Any]]:
        """관련 문서 추천"""
        with open(self.docs_context_file, 'r') as f:
            docs_context = json.load(f)

        if doc_path not in docs_context["documents"]:
            return []

        doc_info = docs_context["documents"][doc_path]
        category = doc_info["category"]

        # 같은 카테고리의 다른 문서들
        related = []
        for path, info in docs_context["documents"].items():
            if path != doc_path and info["category"] == category:
                related.append({
                    "path": path,
                    "category": category,
                    "last_modified": info["last_modified"],
                    "relevance_score": 1.0  # 같은 카테고리
                })

        # 참조 관계가 있는 문서들
        for ref in docs_context["references"]:
            if ref["from"] == doc_path:
                related.append({
                    "path": ref["to"],
                    "reference_type": ref["type"],
                    "relevance_score": 0.8
                })
            elif ref["to"] == doc_path:
                related.append({
                    "path": ref["from"],
                    "reference_type": ref["type"],
                    "relevance_score": 0.8
                })

        # 중복 제거 및 정렬
        seen = set()
        unique_related = []
        for doc in sorted(related, key=lambda x: x.get("relevance_score", 0), reverse=True):
            if doc["path"] not in seen:
                seen.add(doc["path"])
                unique_related.append(doc)

        return unique_related[:limit]

    def _determine_category(self, doc_path: str) -> str:
        """문서 경로에서 카테고리 결정"""
        path_parts = Path(doc_path).parts

        if "docs" in path_parts:
            docs_index = path_parts.index("docs")
            if docs_index + 1 < len(path_parts):
                # docs 다음 디렉토리를 카테고리로 사용
                return path_parts[docs_index + 1]

        # 기본 카테고리
        if "test" in doc_path.lower():
            return "test"
        elif "design" in doc_path.lower():
            return "design"
        elif "report" in doc_path.lower():
            return "report"
        else:
            return "general"

    def get_context_summary(self) -> Dict[str, Any]:
        """전체 Context 요약 정보"""
        summary = {
            "flows": {},
            "documents": {},
            "statistics": {}
        }

        # Flow Context 요약
        flow_dirs = [d for d in os.listdir(self.contexts_dir) if d.startswith("flow_")]
        for flow_dir in flow_dirs:
            context_file = os.path.join(self.contexts_dir, flow_dir, "context.json")
            if os.path.exists(context_file):
                with open(context_file, 'r') as f:
                    flow_context = json.load(f)
                flow_id = flow_context.get("flow_id", flow_dir[5:])
                summary["flows"][flow_id] = {
                    "actions_count": len(flow_context.get("actions", [])),
                    "statistics": flow_context.get("statistics", {})
                }

        # 문서 Context 요약
        if os.path.exists(self.docs_context_file):
            with open(self.docs_context_file, 'r') as f:
                docs_context = json.load(f)
            summary["documents"] = {
                "total_count": len(docs_context.get("documents", {})),
                "categories": docs_context.get("categories", {}),
                "recent_activities": len(docs_context.get("recent_activities", []))
            }

        return summary

# 싱글톤 인스턴스
_context_integration = None

def get_context_integration() -> ContextIntegration:
    """Context Integration 싱글톤 인스턴스 반환"""
    global _context_integration
    if _context_integration is None:
        _context_integration = ContextIntegration()
    return _context_integration
