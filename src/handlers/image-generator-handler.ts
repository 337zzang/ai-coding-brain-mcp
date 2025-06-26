/**
 * AI 이미지 생성 핸들러
 */
import { z } from 'zod';
import { ExecuteCodeHandler } from './execute-code-handler';
import { createLogger } from '../services/logger';

const logger = createLogger('ImageGeneratorHandler');

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
 * AI 이미지 생성
 */
export async function generateAiImage(params: unknown) {
    logger.info('AI 이미지 생성 시작', params);
    
    try {
        // 파라미터 검증
        const validated = generateImageSchema.parse(params);
        
        // Python 코드 생성
        const code = `
# AI 이미지 생성
result = helpers.generate_image(
    prompt="${validated.prompt.replace(/"/g, '\\"')}",
    filename=${validated.filename ? `"${validated.filename}"` : 'None'},
    size="${validated.size}",
    quality="${validated.quality}",
    style="${validated.style}"
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
                const jsonLine = lines.find((line: string) => line.startsWith('{') && line.endsWith('}'));
                
                if (jsonLine) {
                    const imageResult = JSON.parse(jsonLine);
                    
                    logger.info('이미지 생성 성공', imageResult);
                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify({
                                    success: true,
                                    ...imageResult
                                }, null, 2)
                            }
                        ]
                    };
                }
            } catch (parseError) {
                logger.error('결과 파싱 오류', parseError);
            }
        }
        
        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        success: false,
                        error: '이미지 생성 실패',
                        details: executionResult
                    }, null, 2)
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
                        text: JSON.stringify({
                            success: false,
                            error: '입력 검증 실패',
                            details: error.errors
                        }, null, 2)
                    }
                ]
            };
        }
        
        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        success: false,
                        error: error instanceof Error ? error.message : '알 수 없는 오류'
                    }, null, 2)
                }
            ]
        };
    }
}

/**
 * AI 이미지 목록 조회
 */
export async function listAiImages() {
    logger.info('AI 이미지 목록 조회');
    
    try {
        const code = `
# 이미지 목록 조회
images = helpers.list_generated_images()

# JSON으로 변환
import json
print(json.dumps(images, ensure_ascii=False, default=str))
`;
        
        const mcpResponse = await ExecuteCodeHandler.handleExecuteCode({ code, language: 'python' });
        const executionResult = extractExecutionResult(mcpResponse);
        
        if (executionResult && executionResult.success && executionResult.stdout) {
            try {
                const lines = executionResult.stdout.split('\n').filter((line: string) => line.trim());
                const jsonLine = lines.find((line: string) => line.startsWith('[') || line.startsWith('{'));
                
                if (jsonLine) {
                    const images = JSON.parse(jsonLine);
                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify({
                                    success: true,
                                    images: images,
                                    count: images.length
                                }, null, 2)
                            }
                        ]
                    };
                }
            } catch (parseError) {
                logger.error('결과 파싱 오류', parseError);
            }
        }
        
        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        success: false,
                        error: '이미지 목록 조회 실패'
                    }, null, 2)
                }
            ]
        };
        
    } catch (error) {
        logger.error('이미지 목록 조회 오류', error);
        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        success: false,
                        error: error instanceof Error ? error.message : '알 수 없는 오류'
                    }, null, 2)
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

# JSON으로 변환
import json
print(json.dumps(results, ensure_ascii=False, default=str))
`;
        
        const mcpResponse = await ExecuteCodeHandler.handleExecuteCode({ code, language: 'python' });
        const executionResult = extractExecutionResult(mcpResponse);
        
        if (executionResult && executionResult.success && executionResult.stdout) {
            try {
                const lines = executionResult.stdout.split('\n').filter((line: string) => line.trim());
                const jsonLine = lines.find((line: string) => line.startsWith('[') || line.startsWith('{'));
                
                if (jsonLine) {
                    const results = JSON.parse(jsonLine);
                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify({
                                    success: true,
                                    results: results,
                                    count: results.length,
                                    keyword: validated.keyword
                                }, null, 2)
                            }
                        ]
                    };
                }
            } catch (parseError) {
                logger.error('결과 파싱 오류', parseError);
            }
        }
        
        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        success: false,
                        error: '이미지 검색 실패',
                        keyword: validated.keyword
                    }, null, 2)
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
                        text: JSON.stringify({
                            success: false,
                            error: '입력 검증 실패',
                            details: error.errors
                        }, null, 2)
                    }
                ]
            };
        }
        
        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify({
                        success: false,
                        error: error instanceof Error ? error.message : '알 수 없는 오류'
                    }, null, 2)
                }
            ]
        };
    }
}
