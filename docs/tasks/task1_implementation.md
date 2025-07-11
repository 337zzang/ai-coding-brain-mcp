# 🔧 원자적 파일 저장 구현 변경사항

## 변경 파일
- `python/core/context_manager.py`

## 주요 변경사항

### 1. context.json 저장 개선 (라인 148-152)
**기존 코드:**
```python
with open(context_path, 'w', encoding='utf-8') as f:
    json.dump(context_to_save, f, indent=2, ensure_ascii=False)
```

**개선된 코드:**
```python
write_json(context_to_save, Path(context_path))
```

### 2. workflow.json 저장 개선 (라인 158-162)
**기존 코드:**
```python
with open(workflow_path, 'w', encoding='utf-8') as f:
    json.dump(self.workflow_data, f, indent=2, ensure_ascii=False)
```

**개선된 코드:**
```python
write_json(self.workflow_data, Path(workflow_path))
```

## 개선 효과
1. **원자적 쓰기**: 임시 파일 생성 → 완료 후 교체
2. **파일 락**: 동시 접근 시 안전성 보장
3. **데이터 무결성**: 쓰기 중 인터럽트 시에도 원본 보존
4. **일관성**: analyzed_files와 동일한 방식으로 통일

## 전체 개선된 save_all 메서드
    def save_all(self):
        """모든 데이터를 원자적으로 저장합니다."""
        if not self.current_project_name:
            return

        # context.json 저장 (원자적 쓰기 적용)
        context_path = get_context_path(self.current_project_name)

        # 저장할 데이터 준비 (불필요한 필드 제외)
        context_to_save = {}
        excluded_keys = ['__mcp_shared_vars__', 'analyzed_files', 'cache']

        for key, value in self.context.items():
            if key not in excluded_keys:
                context_to_save[key] = value

        # analyzed_files는 별도 캐시 파일로 저장
        if 'analyzed_files' in self.context and self.context['analyzed_files']:
            cache_dir = os.path.join(os.path.dirname(context_path), 'cache')
            os.makedirs(cache_dir, exist_ok=True)
            analyzed_files_path = os.path.join(cache_dir, 'analyzed_files.json')

            try:
                write_json({
                    'analyzed_files': self.context['analyzed_files'],
                    'last_updated': datetime.now().isoformat()
                }, Path(analyzed_files_path))
            except Exception as e:
                print(f"  ⚠️ analyzed_files 캐시 저장 실패: {e}")

        context_to_save['last_modified'] = datetime.now().isoformat()
        context_to_save['project_name'] = self.current_project_name

        # 원자적 쓰기로 context.json 저장
        try:
            write_json(context_to_save, Path(context_path))
            print(f"  ✓ context.json 저장 (원자적 쓰기 적용)")
        except Exception as e:
            print(f"  ❌ context.json 저장 실패: {e}")

        # workflow.json도 원자적 쓰기로 저장
        if self.workflow_data:
            workflow_path = get_workflow_path(self.current_project_name)
            try:
                write_json(self.workflow_data, Path(workflow_path))
                print(f"  ✓ workflow.json 저장 (원자적 쓰기 적용)")
            except Exception as e:
                print(f"  ❌ workflow.json 저장 실패: {e}")
