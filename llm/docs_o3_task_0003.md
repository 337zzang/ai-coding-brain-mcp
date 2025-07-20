# docs 분석 결과

## 질문
Python 프로젝트에서 효과적인 폴더 구조를 설계하는 방법을 간단히 설명해주세요.

## 답변
효과적인 Python 프로젝트 폴더 구조(기본형)  

my_project/  
├─ README.md          : 프로젝트 개요·사용법  
├─ pyproject.toml     : 의존성·빌드·패키징 메타데이터  
├─ requirements.txt   : 추가 의존성 목록(선택)  
├─ .gitignore         : VCS 무시 목록  
├─ src/               : 실제 애플리케이션·라이브러리 코드  
│  └─ my_package/     : 패키지 루트(모듈들 __init__.py 포함)  
│     ├─ __init__.py  
│     ├─ module_a.py  
│     └─ subpkg/  
│        └─ __init__.py  
├─ tests/             : pytest 등 테스트 코드(프로덕션 코드와 분리)  
│  └─ test_module_a.py  
├─ docs/              : Sphinx·MkDocs 등 문서 소스  
├─ scripts/           : CLI 스크립트·유틸리티(실험용 코드)  
├─ notebooks/         : Jupyter 노트북(데이터 분석, 예제)  
└─ .github/           : CI 설정(예: GitHub Actions 워크플로)

핵심 원칙  
1. src 레이아웃: 패키지(root)/테스트 분리로 import 충돌 방지.  
2. 모든 import 는 src/my_package 로부터만 가능하도록 PYTHONPATH 자동 설정(pyproject, setup.cfg 등).  
3. 외부 API 기준으로 모듈 설계·__init__.py 에서 필요한 심볼만 노출.  
4. 테스트·문서·빌드·CI·실험 코드 각 디렉터리 분리해 관심사 분리(SoC).  
5. 설정(예: .env, config.yaml)은 config/ 나 패키지 내부에 두고 dotenv 혹은 pydantic-settings 활용.  
6. 반복 작업(포매터, 린터, 타입체커) 설정은 pyproject.toml 또는 별도 config 파일에 통합.  
7. 컨테이너 사용 시 Dockerfile, docker-compose.yml 루트에 배치.  

이 구조를 기반으로 프로젝트 규모·도메인에 따라 추가 디렉터리를 확장하면 관리·테스트·배포가 수월해집니다.

---
*생성 시간: 2025-07-19 23:12:56*