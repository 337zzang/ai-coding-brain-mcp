/**
 * AI 이미지 생성 핸들러 (이미지 표시 기능 포함)
 */
import { z } from 'zod';
import { ExecuteCodeHandler } from './execute-code-handler';
import { createLogger } from '../services/logger';
import * as fs from 'fs';

const logger = createLogger('ImageGeneratorHandler');

// MCP 응답 content 타입 정의
interface TextContent {
    type: 'text';
    text: string;
}

interface ImageContent {
    type: 'image';
    data: string;
    mimeType: string;
}

type ContentItem = TextContent | ImageContent;


// 입력 스키마 정의
const generateImageSchema = z.object({
    prompt: z.string().min(1, "프롬프트는 필수입니다"),
    filename: z.string().optional(),
    size: z.enum(['1024x1024', '1024x1792', '1792x1024']).optional().default('1024x1024'),
    quality: z.enum(['standard', 'hd']).optional().default('standard'),
    style: z.enum(['vivid', 'natural']).optional().default('vivid')
});

const searchImageSchema = z.object({
    keyword: z.string().min(1, "검색 키워드는 필수입니다")
});

/**
 * MCP 응답에서 실행 결과 추출
 */
function extractExecutionResult(mcpResponse: any): any {
    try {
        // MCP 응답의 content[0].text에서 JSON 파싱
        if (mcpResponse.content && mcpResponse.content[0] && mcpResponse.content[0].text) {
            const resultText = mcpResponse.content[0].text;
            const parsedResult = JSON.parse(resultText);
            return parsedResult;
        }
        return null;
    } catch (e) {
        logger.error('MCP 응답 파싱 오류', e);
        return null;
    }
}

/**
 * 이미지 파일을 base64로 인코딩
 */
function imageToBase64(filepath: string): string | null {
    try {
        const imageBuffer = fs.readFileSync(filepath);
        return imageBuffer.toString('base64');
    } catch (error) {
        logger.error('이미지 base64 인코딩 오류', error);
        return null;
    }
}

/**
 * AI 이미지 생성
 */
export async function generateAiImage(params: unknown) {
    logger.info('AI 이미지 생성 시작', params);
    
    try {
        // 파라미터 검증
        const validated = generateImageSchema.parse(params);
        
        // Python 코드 생성 (base64 반환 포함)
        const code = `
# AI 이미지 생성 (DALL-E 3)
result = helpers.generate_image(
    prompt="${validated.prompt.replace(/"/g, '\\"')}",
    filename=${validated.filename ? `"${validated.filename}"` : 'None'},
    size="${validated.size}",
    quality="${validated.quality}",
    style="${validated.style}",
    model="dall-e-3",
    return_base64=True  # base64 데이터도 반환
)

# 결과를 JSON으로 직렬화
import json
print(json.dumps(result, ensure_ascii=False))
`;
        
        // 코드 실행
        const mcpResponse = await ExecuteCodeHandler.handleExecuteCode({ code, language: 'python' });
        const executionResult = extractExecutionResult(mcpResponse);
        
        if (executionResult && executionResult.success && executionResult.stdout) {
            try {
                // stdout에서 JSON 결과 추출
                const lines = executionResult.stdout.split('\n').filter((line: string) => line.trim());
                const jsonLine = lines.find((line: string) => line.startsWith('{') && line.includes('"success"'));
                
                if (jsonLine) {
                    const imageResult = JSON.parse(jsonLine);
                    
                    if (imageResult.success) {
                        logger.info('이미지 생성 성공', { filename: imageResult.filename });
                        
                        // MCP 응답 구성 (텍스트 정보 + 이미지)
                        const content: ContentItem[] = [
                            {
                                type: 'text',
                                text: `✅ DALL-E 3 이미지 생성 성공!\n\n` +
                                      `📄 파일명: ${imageResult.filename}\n` +
                                      `📝 원본 프롬프트: ${imageResult.prompt}\n` +
                                      `✨ 개선된 프롬프트: ${imageResult.revised_prompt || imageResult.prompt}\n` +
                                      `📐 크기: ${imageResult.size}\n` +
                                      `🎨 스타일: ${imageResult.style}\n` +
                                      `💎 품질: ${imageResult.quality}`
                            }
                        ];
                        
                        // base64 이미지가 있으면 추가
                        if (imageResult.base64) {
                            content.push({
                                type: 'image',
                                data: imageResult.base64,
                                mimeType: 'image/png'
                            });
                        } else if (imageResult.filepath) {
                            // base64가 없으면 파일에서 읽기
                            const base64Data = imageToBase64(imageResult.filepath);
                            if (base64Data) {
                                content.push({
                                    type: 'image',
                                    data: base64Data,
                                    mimeType: 'image/png'
                                });
                            }
                        }
                        
                        return { content };
                    }
                }
            } catch (parseError) {
                logger.error('결과 파싱 오류', parseError);
            }
        }
        
        return {
            content: [
                {
                    type: 'text',
                    text: '❌ 이미지 생성 실패\n\n' + JSON.stringify(executionResult, null, 2)
                }
            ]
        };
        
    } catch (error) {
        logger.error('이미지 생성 오류', error);
        
        if (error instanceof z.ZodError) {
            return {
                content: [
                    {
                        type: 'text',
                        text: '❌ 입력 검증 실패\n\n' + JSON.stringify(error.errors, null, 2)
                    }
                ]
            };
        }
        
        return {
            content: [
                {
                    type: 'text',
                    text: `❌ 오류 발생: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
                }
            ]
        };
    }
}

/**
 * AI 이미지 목록 조회 (썸네일 포함)
 */
export async function listAiImages() {
    logger.info('AI 이미지 목록 조회');
    
    try {
        const code = `
# 이미지 목록 조회
images = helpers.list_generated_images()

# 최근 이미지 3개의 base64 추가
for i, img in enumerate(images[-3:]):
    try:
        img['thumbnail'] = helpers.get_image_base64(img['filename'])
    except:
        img['thumbnail'] = None

# JSON으로 변환
import json
print(json.dumps({
    'images': images,
    'total': len(images)
}, ensure_ascii=False, default=str))
`;
        
        const mcpResponse = await ExecuteCodeHandler.handleExecuteCode({ code, language: 'python' });
        const executionResult = extractExecutionResult(mcpResponse);
        
        if (executionResult && executionResult.success && executionResult.stdout) {
            try {
                const lines = executionResult.stdout.split('\n').filter((line: string) => line.trim());
                const jsonLine = lines.find((line: string) => line.startsWith('{') && line.includes('"images"'));
                
                if (jsonLine) {
                    const result = JSON.parse(jsonLine);
                    const images = result.images || [];
                    
                    // 텍스트 정보
                    let textContent = `📸 총 ${result.total}개의 이미지가 생성되었습니다.\n\n`;
                    
                    // 최근 5개 이미지 정보
                    const recentImages = images.slice(-5).reverse();
                    recentImages.forEach((img: any, idx: number) => {
                        textContent += `${idx + 1}. ${img.filename}\n`;
                        textContent += `   📝 ${img.prompt.substring(0, 50)}...\n`;
                        textContent += `   📅 ${img.created_at}\n`;
                        textContent += `   🎨 ${img.model || 'dall-e-2'}\n\n`;
                    });
                    
                    const content: ContentItem[] = [{ type: 'text', text: textContent }];
                    
                    // 썸네일 추가 (최근 3개)
                    const imagesWithThumbnails = images.slice(-3).reverse();
                    imagesWithThumbnails.forEach((img: any) => {
                        if (img.thumbnail) {
                            content.push({
                                type: 'text',
                                text: `\n🖼️ ${img.filename}:`
                            });
                            content.push({
                                type: 'image',
                                data: img.thumbnail,
                                mimeType: 'image/png'
                            });
                        }
                    });
                    
                    return { content };
                }
            } catch (parseError) {
                logger.error('결과 파싱 오류', parseError);
            }
        }
        
        return {
            content: [
                {
                    type: 'text',
                    text: '❌ 이미지 목록 조회 실패'
                }
            ]
        };
        
    } catch (error) {
        logger.error('이미지 목록 조회 오류', error);
        return {
            content: [
                {
                    type: 'text',
                    text: `❌ 오류 발생: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
                }
            ]
        };
    }
}

/**
 * AI 이미지 검색
 */
export async function searchAiImages(params: unknown) {
    logger.info('AI 이미지 검색', params);
    
    try {
        // 파라미터 검증
        const validated = searchImageSchema.parse(params);
        
        const code = `
# 이미지 검색
results = helpers.search_generated_images("${validated.keyword.replace(/"/g, '\\"')}")

# 검색 결과 이미지의 base64 추가 (최대 3개)
for i, img in enumerate(results[:3]):
    try:
        img['thumbnail'] = helpers.get_image_base64(img['filename'])
    except:
        img['thumbnail'] = None

# JSON으로 변환
import json
print(json.dumps({
    'results': results,
    'count': len(results),
    'keyword': "${validated.keyword.replace(/"/g, '\\"')}"
}, ensure_ascii=False, default=str))
`;
        
        const mcpResponse = await ExecuteCodeHandler.handleExecuteCode({ code, language: 'python' });
        const executionResult = extractExecutionResult(mcpResponse);
        
        if (executionResult && executionResult.success && executionResult.stdout) {
            try {
                const lines = executionResult.stdout.split('\n').filter((line: string) => line.trim());
                const jsonLine = lines.find((line: string) => line.startsWith('{') && line.includes('"results"'));
                
                if (jsonLine) {
                    const result = JSON.parse(jsonLine);
                    const results = result.results || [];
                    
                    // 텍스트 정보
                    let textContent = `🔍 '${result.keyword}' 검색 결과: ${result.count}개의 이미지\n\n`;
                    
                    if (results.length === 0) {
                        textContent += '검색 결과가 없습니다.';
                    } else {
                        results.forEach((img: any, idx: number) => {
                            textContent += `${idx + 1}. ${img.filename}\n`;
                            textContent += `   📝 ${img.prompt}\n`;
                            if (img.revised_prompt && img.revised_prompt !== img.prompt) {
                                textContent += `   ✨ ${img.revised_prompt}\n`;
                            }
                            textContent += `   📅 ${img.created_at}\n\n`;
                        });
                    }
                    
                    const content: ContentItem[] = [{ type: 'text', text: textContent }];
                    
                    // 검색 결과 이미지 추가 (최대 3개)
                    results.slice(0, 3).forEach((img: any) => {
                        if (img.thumbnail) {
                            content.push({
                                type: 'text',
                                text: `\n🖼️ ${img.filename}:`
                            });
                            content.push({
                                type: 'image',
                                data: img.thumbnail,
                                mimeType: 'image/png'
                            });
                        }
                    });
                    
                    return { content };
                }
            } catch (parseError) {
                logger.error('결과 파싱 오류', parseError);
            }
        }
        
        return {
            content: [
                {
                    type: 'text',
                    text: `❌ 이미지 검색 실패 (키워드: ${validated.keyword})`
                }
            ]
        };
        
    } catch (error) {
        logger.error('이미지 검색 오류', error);
        
        if (error instanceof z.ZodError) {
            return {
                content: [
                    {
                        type: 'text',
                        text: '❌ 입력 검증 실패\n\n' + JSON.stringify(error.errors, null, 2)
                    }
                ]
            };
        }
        
        return {
            content: [
                {
                    type: 'text',
                    text: `❌ 오류 발생: ${error instanceof Error ? error.message : '알 수 없는 오류'}`
                }
            ]
        };
    }
}
