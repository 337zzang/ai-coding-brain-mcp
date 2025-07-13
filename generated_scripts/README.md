# 네이버 올스타전 검색 자동화 실행 가이드

## 생성된 스크립트

1. **naver_allstar_search_manual.py** - 전체 기능 버전
   - 상세한 로그 출력
   - 에러 처리 포함
   - 다양한 정보 추출

2. **naver_simple.py** - 간단한 버전
   - 핵심 기능만 포함
   - 빠른 실행

## 실행 방법

```bash
# 전체 버전 실행
python generated_scripts/naver_allstar_search_manual.py

# 간단 버전 실행  
python generated_scripts/naver_simple.py
```

## 주요 기능

1. 네이버 홈페이지 접속
2. "올스타전" 검색어 입력
3. 검색 실행
4. 검색 결과에서 정보 추출:
   - 관련 뉴스 제목
   - 스포츠 섹션 정보
   - 날짜 정보

## 필요 사항

- Python 3.7 이상
- Playwright 설치
- 인터넷 연결

## 문제 해결

1. **Playwright 설치 안됨**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **모듈 찾을 수 없음**
   - 프로젝트 루트에서 실행하세요
   - 또는 PYTHONPATH 설정

3. **검색창을 찾을 수 없음**
   - 네이버 UI가 변경되었을 수 있습니다
   - 선택자 업데이트 필요
