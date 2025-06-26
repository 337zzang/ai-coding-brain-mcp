#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gitignore Manager - AI Coding Brain MCP
.gitignore 파일 관리를 위한 유틸리티
"""

import os
import re
from typing import List, Dict, Set
from pathlib import Path

class GitignoreManager:
    """
    .gitignore 파일 관리 클래스
    """
    
    # 일반적인 ignore 패턴들
    COMMON_PATTERNS = {
        "Python": [
            "__pycache__/",
            "*.py[cod]",
            "*$py.class",
            "*.so",
            ".Python",
            "venv/",
            "env/",
            ".venv/",
            "ENV/",
            "env.bak/",
            "venv.bak/",
            ".pytest_cache/",
            ".coverage",
            "htmlcov/",
            "*.egg-info/",
            "dist/",
            "build/",
            ".mypy_cache/",
            ".dmypy.json",
            "dmypy.json",
            ".pyre/",
            ".pytype/",
        ],
        "Node.js": [
            "node_modules/",
            "npm-debug.log*",
            "yarn-debug.log*",
            "yarn-error.log*",
            ".npm",
            ".eslintcache",
            ".node_repl_history",
            "*.tsbuildinfo",
            ".next/",
            ".nuxt/",
            ".cache/",
            "dist/",
            ".parcel-cache/",
        ],
        "IDE": [
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "*~",
            ".project",
            ".classpath",
            ".settings/",
            "*.sublime-*",
            ".history/",
        ],
        "OS": [
            ".DS_Store",
            ".DS_Store?",
            "._*",
            ".Spotlight-V100",
            ".Trashes",
            "ehthumbs.db",
            "Thumbs.db",
            "desktop.ini",
            "$RECYCLE.BIN/",
        ],
        "환경 설정": [
            ".env",
            ".env.local",
            ".env.development",
            ".env.test",
            ".env.production",
            "*.env",
            "config.local.js",
            "secrets.json",
        ],
        "로그 및 임시 파일": [
            "*.log",
            "*.log.*",
            "logs/",
            "*.tmp",
            "*.temp",
            "*.cache",
            "tmp/",
            "temp/",
        ],
        "백업 파일": [
            "*.bak",
            "*.backup",
            "*.old",
            "*.orig",
            "backup/",
            "backups/",
        ]
    }
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.gitignore_path = self.project_root / ".gitignore"
        
    def analyze_project(self) -> Dict[str, List[str]]:
        """프로젝트를 분석하여 ignore해야 할 파일/폴더 찾기"""
        suggestions = {}
        
        # 프로젝트의 모든 파일/폴더 스캔
        all_files = set()
        all_dirs = set()
        
        for root, dirs, files in os.walk(self.project_root):
            # .git 폴더는 제외
            if '.git' in root:
                continue
                
            for d in dirs:
                all_dirs.add(d)
            for f in files:
                all_files.add(f)
                # 확장자도 추출
                if '.' in f:
                    ext = '*' + f[f.rfind('.'):]
                    all_files.add(ext)
        
        # 패턴 매칭
        for category, patterns in self.COMMON_PATTERNS.items():
            found = []
            for pattern in patterns:
                # 간단한 패턴 매칭
                if pattern.endswith('/'):
                    # 디렉토리 패턴
                    dir_name = pattern.rstrip('/')
                    if dir_name in all_dirs:
                        found.append(pattern)
                elif '*' in pattern:
                    # 와일드카드 패턴
                    regex = pattern.replace('.', r'\.').replace('*', '.*')
                    regex = '^' + regex + '$'
                    for f in all_files:
                        if re.match(regex, f):
                            found.append(pattern)
                            break
                else:
                    # 정확한 파일명
                    if pattern in all_files:
                        found.append(pattern)
            
            if found:
                suggestions[category] = found
                
        return suggestions
    
    def read_gitignore(self) -> List[str]:
        """현재 .gitignore 파일 읽기"""
        if not self.gitignore_path.exists():
            return []
        
        with open(self.gitignore_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    def update_gitignore(self, patterns: List[str], category: str = None) -> Dict[str, any]:
        """
        .gitignore 파일 업데이트
        
        Args:
            patterns: 추가할 패턴 리스트
            category: 카테고리 이름 (주석으로 추가됨)
            
        Returns:
            결과 딕셔너리
        """
        existing = set(self.read_gitignore())
        new_patterns = [p for p in patterns if p not in existing]
        
        if not new_patterns:
            return {
                "success": True,
                "message": "이미 모든 패턴이 .gitignore에 있습니다.",
                "added": [],
                "existing": patterns
            }
        
        # 파일에 추가
        with open(self.gitignore_path, 'a', encoding='utf-8') as f:
            if category:
                f.write(f"\n# {category}\n")
            for pattern in new_patterns:
                f.write(f"{pattern}\n")
        
        return {
            "success": True,
            "message": f"{len(new_patterns)}개의 패턴을 추가했습니다.",
            "added": new_patterns,
            "existing": [p for p in patterns if p in existing]
        }
    
    def create_gitignore(self, categories: List[str] = None) -> Dict[str, any]:
        """
        새로운 .gitignore 파일 생성
        
        Args:
            categories: 포함할 카테고리 리스트 (None이면 모든 카테고리)
            
        Returns:
            결과 딕셔너리
        """
        if self.gitignore_path.exists():
            return {
                "success": False,
                "message": ".gitignore 파일이 이미 존재합니다. update_gitignore를 사용하세요."
            }
        
        if categories is None:
            categories = list(self.COMMON_PATTERNS.keys())
        
        with open(self.gitignore_path, 'w', encoding='utf-8') as f:
            f.write("# AI Coding Brain MCP - .gitignore\n")
            f.write("# 자동 생성된 파일\n\n")
            
            for category in categories:
                if category in self.COMMON_PATTERNS:
                    f.write(f"# {category}\n")
                    for pattern in self.COMMON_PATTERNS[category]:
                        f.write(f"{pattern}\n")
                    f.write("\n")
        
        total_patterns = sum(len(self.COMMON_PATTERNS[cat]) for cat in categories if cat in self.COMMON_PATTERNS)
        
        return {
            "success": True,
            "message": f".gitignore 파일을 생성했습니다. ({total_patterns}개 패턴)",
            "categories": categories,
            "patterns_count": total_patterns
        }

# 싱글톤 인스턴스
_gitignore_manager = None

def get_gitignore_manager(project_root: str = ".") -> GitignoreManager:
    """GitignoreManager 인스턴스 반환"""
    global _gitignore_manager
    if _gitignore_manager is None:
        _gitignore_manager = GitignoreManager(project_root)
    return _gitignore_manager
