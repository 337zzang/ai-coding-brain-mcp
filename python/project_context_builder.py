#!/usr/bin/env python3
"""
프로젝트 컨텍스트 문서 자동 생성 도구
README.md, PROJECT_CONTEXT.md 등을 자동으로 생성/업데이트
"""

import os
import json
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import re

class ProjectContextBuilder:
    """프로젝트 컨텍스트 문서 빌더"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.project_name = self.project_root.name
        self.config = self._load_config()
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def _load_config(self) -> Dict:
        """프로젝트 설정 로드"""
        config_files = [
            ".ai-brain.config.json",
            "package.json",
            "pyproject.toml"
        ]
        
        config = {
            "name": self.project_name,
            "description": "",
            "version": "0.0.1",
            "language": "Unknown",
            "dependencies": {}
        }
        
        for config_file in config_files:
            path = self.project_root / config_file
            if path.exists():
                try:
                    if config_file.endswith('.json'):
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if config_file == "package.json":
                                config["name"] = data.get("name", config["name"])
                                config["description"] = data.get("description", config["description"])
                                config["version"] = data.get("version", config["version"])
                                config["dependencies"] = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                                config["language"] = "TypeScript/JavaScript"
                            elif config_file == ".ai-brain.config.json":
                                config.update(data)
                except Exception as e:
                    print(f"⚠️ {config_file} 로드 실패: {e}")
                    
        return config
        
    def analyze_project_structure(self) -> Dict:
        """프로젝트 구조 분석"""
        stats = {
            "total_files": 0,
            "py_files": 0,
            "ts_files": 0,
            "js_files": 0,
            "json_files": 0,
            "md_files": 0,
            "directories": 0,
            "main_directories": [],
            "file_types": {}
        }
        
        ignore_patterns = ['.git', 'node_modules', '__pycache__', 'dist', 'build', '.venv', 'venv']
        
        for root, dirs, files in os.walk(self.project_root):
            # 무시할 디렉토리 제외
            dirs[:] = [d for d in dirs if d not in ignore_patterns]
            
            rel_path = Path(root).relative_to(self.project_root)
            if rel_path == Path('.'):
                stats["main_directories"] = dirs
            
            stats["directories"] += len(dirs)
            
            for file in files:
                stats["total_files"] += 1
                ext = Path(file).suffix.lower()
                
                # 파일 타입별 카운트
                if ext == '.py':
                    stats["py_files"] += 1
                elif ext == '.ts':
                    stats["ts_files"] += 1
                elif ext == '.js':
                    stats["js_files"] += 1
                elif ext == '.json':
                    stats["json_files"] += 1
                elif ext == '.md':
                    stats["md_files"] += 1
                    
                stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
                
        return stats
        
    def build_readme(self) -> str:
        """README.md 생성"""
        stats = self.analyze_project_structure()
        
        readme = f"""# {self.config.get('name', self.project_name)}

{self.config.get('description', '프로젝트 설명이 필요합니다.')}

## 📋 프로젝트 정보

- **버전**: {self.config.get('version', '0.0.1')}
- **언어**: {self.config.get('language', 'Unknown')}
- **최종 업데이트**: {self.timestamp}

## 📊 프로젝트 통계

- **전체 파일**: {stats['total_files']}개
- **디렉토리**: {stats['directories']}개
- **주요 언어**:
"""
        
        if stats['py_files'] > 0:
            readme += f"  - Python: {stats['py_files']}개 파일\n"
        if stats['ts_files'] > 0:
            readme += f"  - TypeScript: {stats['ts_files']}개 파일\n"
        if stats['js_files'] > 0:
            readme += f"  - JavaScript: {stats['js_files']}개 파일\n"
            
        readme += f"""
## 🗂️ 프로젝트 구조

```
{self.project_name}/
"""
        
        for dir in stats['main_directories'][:8]:  # 주요 디렉토리 최대 8개
            readme += f"├── {dir}/\n"
        if len(stats['main_directories']) > 8:
            readme += f"└── ... (외 {len(stats['main_directories']) - 8}개)\n"
        else:
            readme += "└── ...\n"
            
        readme += """```

## 🚀 시작하기

### 설치

```bash
# 의존성 설치
"""
        
        if (self.project_root / "package.json").exists():
            readme += "npm install\n"
        if (self.project_root / "requirements.txt").exists():
            readme += "pip install -r requirements.txt\n"
            
        readme += """```

### 실행

```bash
# 프로젝트 실행 명령어를 여기에 추가하세요
```

## 📖 문서

- [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) - 프로젝트 상세 컨텍스트
- [file_directory.md](./file_directory.md) - 파일 구조 문서
- [project_wisdom.md](./project_wisdom.md) - 프로젝트 지혜와 교훈

## 🤝 기여하기

기여를 환영합니다! PR을 보내주세요.

---
*이 문서는 /build 명령으로 자동 생성되었습니다.*
"""
        
        return readme
        
    def build_project_context(self) -> str:
        """PROJECT_CONTEXT.md 생성"""
        stats = self.analyze_project_structure()
        
        context = f"""# 프로젝트 컨텍스트: {self.config.get('name', self.project_name)}

> 이 문서는 프로젝트의 상세 컨텍스트와 구조를 설명합니다.
> 최종 업데이트: {self.timestamp}

## 🎯 프로젝트 개요

**프로젝트명**: {self.config.get('name', self.project_name)}  
**설명**: {self.config.get('description', '프로젝트 설명이 필요합니다.')}  
**버전**: {self.config.get('version', '0.0.1')}  
**주요 언어**: {self.config.get('language', 'Unknown')}

## 🏗️ 아키텍처

### 기술 스택
"""
        
        # 언어별 기술 스택 추론
        if stats['py_files'] > 0:
            context += "- **백엔드/스크립트**: Python\n"
        if stats['ts_files'] > 0:
            context += "- **프론트엔드/서버**: TypeScript\n"
        if stats['js_files'] > 0:
            context += "- **스크립트**: JavaScript\n"
            
        context += """
### 주요 디렉토리 구조

| 디렉토리 | 설명 |
|---------|------|
"""
        
        # 디렉토리 설명 추론
        dir_descriptions = {
            "src": "소스 코드",
            "python": "Python 스크립트 및 유틸리티",
            "dist": "빌드 결과물",
            "test": "테스트 코드",
            "docs": "문서",
            "scripts": "유틸리티 스크립트",
            "handlers": "요청 핸들러",
            "tools": "도구 정의",
            "memory": "캐시 및 상태 저장",
            "utils": "유틸리티 함수"
        }
        
        for dir in stats['main_directories'][:10]:
            desc = dir_descriptions.get(dir, "프로젝트 관련 파일")
            context += f"| `{dir}/` | {desc} |\n"
            
        
        # 디렉토리 트리 추가
        context += f"""
### 디렉토리 트리 뷰

\`\`\`
{self._generate_tree_structure(max_depth=2)}
\`\`\`
"""
        
        context += f"""
## 📦 의존성

### 주요 의존성
"""
        
        # 의존성 표시
        deps = self.config.get('dependencies', {})
        if deps:
            for i, (dep, version) in enumerate(list(deps.items())[:15]):
                context += f"- `{dep}`: {version}\n"
            if len(deps) > 15:
                context += f"- ... 외 {len(deps) - 15}개\n"
        else:
            context += "- 의존성 정보 없음\n"
            
        context += f"""
## 🔧 설정 파일

### 주요 설정 파일 목록
"""
        
        config_files = [
            (".ai-brain.config.json", "AI Coding Brain 설정"),
            ("package.json", "Node.js 프로젝트 설정"),
            ("tsconfig.json", "TypeScript 설정"),
            (".env", "환경 변수"),
            (".gitignore", "Git 무시 파일"),
            ("requirements.txt", "Python 의존성")
        ]
        
        for file, desc in config_files:
            if (self.project_root / file).exists():
                context += f"- `{file}`: {desc}\n"
                
        context += f"""
## 📊 프로젝트 통계

- **전체 파일 수**: {stats['total_files']}개
- **디렉토리 수**: {stats['directories']}개
- **파일 타입 분포**:
"""
        
        # 상위 5개 파일 타입
        sorted_types = sorted(stats['file_types'].items(), key=lambda x: x[1], reverse=True)[:5]
        for ext, count in sorted_types:
            percentage = (count / stats['total_files'] * 100) if stats['total_files'] > 0 else 0
            context += f"  - `{ext or 'no extension'}`: {count}개 ({percentage:.1f}%)\n"
            
        context += """
## 🚀 빠른 시작

1. **프로젝트 클론**
   ```bash
   git clone [repository-url]
   cd """ + self.project_name + """
   ```

2. **의존성 설치**
   ```bash
"""
        
        if (self.project_root / "package.json").exists():
            context += "   npm install\n"
        if (self.project_root / "requirements.txt").exists():
            context += "   pip install -r requirements.txt\n"
            
        context += """   ```

3. **환경 설정**
   - `.env.example`을 `.env`로 복사하고 필요한 값 설정
   - 필요한 API 키와 설정 구성

4. **실행**
   - 프로젝트별 실행 명령어 참조

## 🔍 추가 정보

- 상세한 파일 구조는 [file_directory.md](./file_directory.md) 참조
- 프로젝트 작업 중 발견한 교훈은 [project_wisdom.md](./project_wisdom.md) 참조
- API 문서는 [API_REFERENCE.md](./API_REFERENCE.md) 참조 (생성 예정)

---
*이 문서는 /build 명령으로 자동 생성되었습니다.*
"""
        
        return context
        
    def save_document(self, filename: str, content: str) -> bool:
        """문서 저장"""
        try:
            file_path = self.project_root / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {filename} 생성/업데이트 완료")
            return True
        except Exception as e:
            print(f"❌ {filename} 저장 실패: {e}")
            return False

    def generate_file_directory(self) -> str:
        """file_directory.md 생성"""
        content = f"""# 📁 Project Structure - {self.project_name}

*Generated: {self.timestamp}*

## 📊 Overview

"""
        stats = self.analyze_project_structure()
        content += f"- Total Files: {stats['total_files']}\n"
        content += f"- Total Directories: {stats['directories']}\n\n"
        
        content += "### File Types Distribution:\n"
        sorted_types = sorted(stats['file_types'].items(), key=lambda x: x[1], reverse=True)
        for ext, count in sorted_types[:20]:
            content += f"- `{ext or '[no extension]'}`: {count} files\n"
            
        content += "\n## 📂 Directory Structure\n\n```\n"
        content += self._generate_tree_structure()
        content += "\n```\n"
        
        return content
        
    def _generate_tree_structure(self, max_depth: int = 3) -> str:
        """디렉토리 트리 구조 생성"""
        tree = []
        ignore_dirs = {'.git', 'node_modules', '__pycache__', 'dist', 'build', '.venv', 'venv'}
        
        def walk_dir(path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return
                
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            except (PermissionError, OSError):
                return
                
            dirs = [item for item in items if item.is_dir() and item.name not in ignore_dirs]
            files = [item for item in items if item.is_file()]
            
            # 디렉토리 표시
            for i, dir_item in enumerate(dirs[:10]):  # 최대 10개 디렉토리
                is_last_dir = (i == len(dirs) - 1) and len(files) == 0
                tree.append(f"{prefix}{'└── ' if is_last_dir else '├── '}{dir_item.name}/")
                
                if depth < max_depth:
                    extension = "    " if is_last_dir else "│   "
                    walk_dir(dir_item, prefix + extension, depth + 1)
                    
            # 파일 표시 (주요 파일만)
            important_files = [f for f in files if f.suffix in ['.py', '.ts', '.js', '.json', '.md']][:5]
            for i, file_item in enumerate(important_files):
                is_last = i == len(important_files) - 1
                tree.append(f"{prefix}{'└── ' if is_last else '├── '}{file_item.name}")
                
            if len(files) > len(important_files):
                tree.append(f"{prefix}└── ... ({len(files) - len(important_files)} more files)")
                
        tree.append(f"{self.project_name}/")
        walk_dir(self.project_root, "", 0)
        
        return "\n".join(tree)
            
    def build_all(self, update_readme: bool = True, update_context: bool = True, include_file_directory: bool = False) -> Dict[str, bool]:
        """모든 문서 빌드"""
        results = {}
        
        if update_readme:
            readme_content = self.build_readme()
            results['README.md'] = self.save_document('README.md', readme_content)
            
        if update_context:
            context_content = self.build_project_context()
            results['PROJECT_CONTEXT.md'] = self.save_document('PROJECT_CONTEXT.md', context_content)
            
                
        if include_file_directory:
            file_dir_content = self.generate_file_directory()
            results['file_directory.md'] = self.save_document('file_directory.md', file_dir_content)
        
        
        return results

# 메인 함수
def build_project_context(update_readme: bool = True, update_context: bool = True, include_stats: bool = True, include_file_directory: bool = False):
    """프로젝트 컨텍스트 문서 빌드"""
    builder = ProjectContextBuilder()
    results = builder.build_all(update_readme, update_context, include_file_directory)
    
    if include_stats:
        stats = builder.analyze_project_structure()
        print(f"\n📊 프로젝트 통계:")
        print(f"  - 전체 파일: {stats['total_files']}개")
        print(f"  - Python: {stats['py_files']}개")
        print(f"  - TypeScript: {stats['ts_files']}개")
        
    return results

if __name__ == "__main__":
    build_project_context()
