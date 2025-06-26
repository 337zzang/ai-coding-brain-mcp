# 🎨 AI 이미지 생성 MCP 도구 가이드

## 개요
AI Coding Brain MCP에 통합된 이미지 생성 도구입니다. OpenAI의 DALL-E 3를 사용하여 고품질 이미지를 생성하고, Claude Desktop에서 직접 확인할 수 있습니다.

## 주요 기능
- **DALL-E 3 지원**: 최신 AI 모델로 고품질 이미지 생성
- **Claude 통합 표시**: 생성된 이미지를 Claude에서 바로 확인
- **다양한 크기**: 정사각형, 세로형, 가로형 지원
- **메타데이터 관리**: 생성 이력 자동 저장

## 설치 및 설정

### 1. 환경 변수 설정
`.env` 파일에 OpenAI API 키 추가:
```
OPENAI_API_KEY=sk-your-api-key-here
```

### 2. 빌드
```bash
npm run build
```

### 3. Claude Desktop 재시작

## 사용 방법

### 1. execute_code에서 사용

#### 이미지 생성
```python
# 기본 사용법
result = helpers.generate_image("귀여운 고양이가 코딩하는 모습")

# 고급 옵션
result = helpers.generate_image(
    prompt="미래적인 AI 어시스턴트",
    filename="ai_assistant.png",
    model="dall-e-3",
    size="1792x1024",  # 와이드스크린
    quality="hd",      # 고품질
    style="vivid"      # 생생한 스타일
)
```

#### 이미지 목록 조회
```python
# 생성된 모든 이미지 목록
images = helpers.list_generated_images()

# 최근 5개 이미지
recent_images = images[-5:]
```

#### 이미지 검색
```python
# 키워드로 검색
cat_images = helpers.search_generated_images("고양이")
robot_images = helpers.search_generated_images("robot")
```

#### Base64 인코딩
```python
# 이미지를 base64로 변환
base64_data = helpers.get_image_base64("image.png")
```

### 2. MCP 도구로 사용 (Claude Desktop 재시작 후)

MCP 도구로 등록되면 Claude에서 직접 사용 가능:
- `generate_ai_image`: 이미지 생성 + Claude에 표시
- `list_ai_images`: 목록 조회 + 썸네일 표시
- `search_ai_images`: 검색 + 결과 이미지 표시

## 옵션 설명

### 모델 (model)
- `dall-e-3`: 최신 모델, 고품질 (기본값)
- `dall-e-2`: 이전 모델, 빠른 생성

### 크기 (size)
#### DALL-E 3
- `1024x1024`: 정사각형 (기본값)
- `1024x1792`: 세로형 (포트레이트)
- `1792x1024`: 가로형 (랜드스케이프)

#### DALL-E 2
- `256x256`: 작은 크기
- `512x512`: 중간 크기
- `1024x1024`: 큰 크기

### 품질 (quality)
- `standard`: 표준 품질 (기본값)
- `hd`: 고품질 (DALL-E 3만 지원)

### 스타일 (style)
- `vivid`: 생생하고 극적인 스타일 (기본값)
- `natural`: 자연스럽고 덜 과장된 스타일

## 파일 구조
```
ai-coding-brain-mcp/
├── image/                        # 생성된 이미지 저장
│   ├── *.png                    # 이미지 파일들
│   └── image_metadata.json      # 메타데이터
├── python/api/
│   └── image_generator.py       # 핵심 로직
└── src/handlers/
    └── image-generator-handler.ts # MCP 핸들러
```

## 프롬프트 작성 팁

1. **구체적으로 작성**: 원하는 스타일, 색상, 구도 명시
2. **아트 스타일 추가**: "in the style of...", "aesthetic" 등
3. **품질 키워드**: "highly detailed", "professional", "4K"
4. **조명 설정**: "dramatic lighting", "soft light", "neon"

### 좋은 프롬프트 예시
```
"A cute robot cat programming on a holographic computer, 
cyberpunk style, neon blue and pink lighting, highly detailed, 
digital art, futuristic workspace background"
```

## 주의사항
- API 호출당 비용이 발생합니다
- 생성된 이미지는 로컬에 저장됩니다
- DALL-E 3는 프롬프트를 자동으로 개선할 수 있습니다

## 문제 해결

### OPENAI_API_KEY 오류
`.env` 파일에 올바른 API 키가 설정되어 있는지 확인

### 이미지가 표시되지 않음
1. npm run build 실행
2. Claude Desktop 재시작
3. MCP 서버 로그 확인

### 크기 오류
선택한 모델이 지원하는 크기인지 확인

---

Happy image generating! 🎨✨
