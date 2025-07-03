# AI Helpers API 모듈

이미지 생성, 웹 자동화 등 다양한 API 기능을 제공하는 모듈입니다.

## 구조

```
ai_helpers/api/
├── __init__.py      # API 모듈 진입점
├── manager.py       # API 활성화/비활성화 관리
├── wrappers.py      # API 래퍼 함수들
├── image.py         # 이미지 생성 API (OpenAI DALL-E)
└── README.md        # 이 문서
```

## 주요 기능

### 1. API 관리

```python
from ai_helpers.api import toggle_api, list_apis

# API 활성화/비활성화
result = toggle_api('image', True)  # 이미지 API 활성화
result = toggle_api('image', False) # 이미지 API 비활성화

# 활성화된 API 목록 조회
apis = list_apis()
# {'image': True, 'web': True, 'structure': True}
```

### 2. 이미지 생성 API

```python
from ai_helpers.api import ImageAPI

# 이미지 생성
result = ImageAPI.generate_image(
    prompt="아름다운 일몰 풍경",
    filename="sunset.png",
    size="1024x1024",
    quality="standard"
)

# 생성된 이미지 목록 조회
images = ImageAPI.list_generated_images()

# 키워드로 이미지 검색
found = ImageAPI.search_generated_images("일몰")

# 이미지를 base64로 인코딩
base64_str = ImageAPI.get_image_base64("sunset.png")
```

## 사용 방법

### JSON REPL 세션에서

```python
# helpers 객체를 통해 사용
helpers.generate_image("귀여운 고양이")
helpers.list_generated_images()
helpers.toggle_api('image', True)
```

### 직접 import해서 사용

```python
from ai_helpers.api import ImageAPI, toggle_api

# API 활성화
toggle_api('image', True)

# 이미지 생성
result = ImageAPI.generate_image("멋진 우주 풍경")
```

## 환경 변수

이미지 생성 API를 사용하려면 OpenAI API 키가 필요합니다:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## 확장 가능성

새로운 API를 추가하려면:

1. `ai_helpers/api/` 디렉토리에 새 모듈 생성
2. `wrappers.py`에 래퍼 클래스 추가
3. `manager.py`의 `_api_modules`에 등록
4. `__init__.py`에서 export

## 리팩토링 내역

- 2025-06-30: json_repl_session.py에서 API 관련 코드 분리
- API 관리 기능을 별도 모듈로 분리
- 이미지 생성 API를 ai_helpers 내부로 이동
