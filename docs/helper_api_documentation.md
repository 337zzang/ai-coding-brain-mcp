# 📚 AI Helpers 파일/디렉토리 관련 함수 API 문서

## 🔍 조사 요약
- 조사일: 2025-07-27
- 총 헬퍼 함수 수: 87개
- 파일/디렉토리 관련 함수: 13개
- ⚠️ 주의: create_directory 함수는 존재하지 않음 (os.makedirs 사용)

## 📁 파일 작업 함수

### h.read(path: str, encoding: str = 'utf-8') -> Dict[str, Any]
- **설명**: 파일을 읽어서 내용 반환
- **반환**: {'ok': bool, 'data': str, 'error': str (실패 시)}
- **주의**: offset, length 파라미터 없음

### h.write(path: str, content: str, encoding: str = 'utf-8', backup: bool = False) -> Dict[str, Any]
- **설명**: 파일에 내용 쓰기
- **backup**: True 시 백업 생성
- **반환**: {'ok': bool, 'data': '', 'error': str (실패 시)}

### h.append(path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]
- **설명**: 파일에 내용 추가
- **반환**: {'ok': bool, 'data': '', 'error': str (실패 시)}

### h.exists(path: str) -> Dict[str, Any]
- **설명**: 파일 존재 여부 확인
- **반환**: {'ok': bool, 'data': bool (존재 여부)}

### h.info(path: str) -> Dict[str, Any]
- **설명**: 파일 정보 조회
- **반환**: {'ok': bool, 'data': {'size': int, 'created': float, 'modified': float, 'lineCount': int}}

## 📂 디렉토리 작업 함수

### h.scan_directory_dict(path: str = '.', max_depth: int = 3) -> Dict[str, Any]
- **설명**: 디렉토리 구조를 딕셔너리로 반환
- **반환 구조**:
```python
{
    'ok': True,
    'data': {
        'root': str,  # 스캔한 루트 경로
        'structure': {
            '파일/폴더명': {
                'type': 'file' | 'directory',
                'size': int (파일인 경우),
                'children': dict (디렉토리인 경우)
            }
        },
        'stats': {
            'total_files': int  # 전체 파일 수
            # 주의: 'directories' 키는 없을 수 있음
        }
    }
}
```

### h.list_directory(path: str = '.') -> Dict[str, Any]
- **설명**: 디렉토리 내용 조회
- **반환**: 파일/디렉토리 목록

### ❌ h.create_directory
- **존재하지 않음**
- **대안**: `os.makedirs(path, exist_ok=True)` 사용

## 🔧 프로젝트 관련 함수

### h.get_current_project() -> Dict[str, Any]
- **반환**: {'ok': bool, 'data': {'name': str, 'path': str}}

### h.flow_project_with_workflow(project_name: str)
- **설명**: 프로젝트 전환 (바탕화면에서만 검색)
- **특징**: 워크플로우도 자동 전환

## 💡 발견된 문제 및 해결책

### 1. 파일 읽기 offset/length 미지원
- **문제**: h.read()는 offset, length 파라미터 없음
- **해결**: 
  ```python
  # 전체 읽은 후 슬라이싱
  content = h.read(path)['data']
  lines = content.split('\n')[offset:offset+length]
  ```

### 2. create_directory 함수 없음
- **문제**: h.create_directory() 존재하지 않음
- **해결**: `os.makedirs(path, exist_ok=True)` 사용

### 3. scan_directory_dict의 stats 구조
- **정확한 키**: 'total_files' (✅ 정상 작동)
- **주의**: 'directories' 키는 제공되지 않음
- **해결**: 필요시 structure를 순회하여 직접 계산

## 📊 파일 수 계산 헬퍼 함수
```python
def count_files_and_dirs(structure):
    '''scan_directory_dict 결과에서 파일/디렉토리 수 계산'''
    files = 0
    dirs = 0

    def traverse(struct):
        nonlocal files, dirs
        for name, item in struct.items():
            if item.get('type') == 'file':
                files += 1
            elif item.get('type') == 'directory':
                dirs += 1
                if 'children' in item:
                    traverse(item['children'])

    traverse(structure)
    return files, dirs
```
