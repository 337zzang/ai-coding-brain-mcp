# Sales OCR 시스템 프로세스 문서

## 1. 시스템 개요

Sales OCR은 매출증빙(영수증, 세금계산서 등)과 매출내역을 자동으로 대사하는 파일럿 시스템입니다.

### 주요 기능
- PDF/이미지 형식의 증빙 문서 OCR 처리
- AI (Claude/Gemini)를 활용한 텍스트 추출 및 구조화
- 엑셀 매출내역과 증빙의 자동 매칭
- 매칭 결과 검토 및 수정 GUI

## 2. 시스템 구조

### 2.1 디렉토리 구조
```
sales_ocr/python/
├── run_gui.py              # 진입점
├── api_handlers.py         # AI API 통합 (Claude, Gemini)
├── processing_flow.py      # 데이터 처리 파이프라인
├── ocr_module.py          # OCR 처리 모듈
├── gui/
│   ├── main_window.py     # 메인 윈도우 (68KB)
│   ├── tabs/              # 탭 구성요소
│   │   ├── project_settings.py  # 프로젝트 설정
│   │   ├── data_preview.py      # 데이터 미리보기
│   │   ├── processing.py        # 처리 진행
│   │   └── results.py           # 결과 확인 (71KB)
│   └── managers/          # 비즈니스 로직
└── utils/                 # 유틸리티
```

### 2.2 주요 컴포넌트
- **GUI Layer**: PyQt5 기반 데스크톱 애플리케이션
- **Processing Layer**: 데이터 처리 및 AI 통합
- **Storage Layer**: 메모리 기반 데이터 관리

## 3. 데이터 처리 흐름

### 3.1 기본 프로세스
1. **프로젝트 설정**: API 키 입력, 파일 경로 설정
2. **데이터 로드**: 매출내역 엑셀, 증빙 PDF/이미지 파일 로드
3. **OCR 처리**: AI API를 통한 증빙 텍스트 추출
4. **자동 매칭**: 추출된 텍스트와 매출내역 매칭
5. **결과 검토**: GUI에서 매칭 결과 확인 및 수정

### 3.2 상세 처리 단계
