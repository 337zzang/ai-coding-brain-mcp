/**
 * AI 이미지 생성 핸들러
 */
import { z } from 'zod';
import path from 'path';
import { executeCode } from '../services/execute-code-service';
import { Logger } from '../utils/logger';

const logger = new Logger('ImageGeneratorHandler');

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
    prompt="${validated.prompt.replace(/"/g, '\"')}",
    filename=${validated.filename ? `"${validated.filename}"` : 'None'},
    size="${validated.size}",
    quality="${validated.quality}",
    style="${validated.style}"
)

# 결과 반환
result
`;
        
        // 코드 실행
        const result = await executeCode(code);
        
        if (result.success) {
            try {
                // stdout의 마지막 줄에서 결과 추출
                const lines = result.stdout.split('\n').filter(line => line.trim());
                const lastLine = lines[lines.length - 1];
                
                // 딕셔너리 형태의 결과 파싱
                if (lastLine.startsWith('{') && lastLine.endsWith('}')) {
                    const imageResult = JSON.parse(lastLine.replace(/'/g, '"'));
                    
                    if (imageResult.success) {
                        logger.info('이미지 생성 성공', imageResult);
                        return {
                            success: true,
                            ...imageResult
                        };
                    } else {
                        throw new Error(imageResult.error || '이미지 생성 실패');
                    }
                }
                
                // 결과 파싱 실패
                return {
                    success: true,
                    message: result.stdout,
                    raw_result: result
                };
            } catch (parseError) {
                logger.error('결과 파싱 오류', parseError);
                return {
                    success: true,
                    message: result.stdout,
                    raw_result: result
                };
            }
        } else {
            throw new Error(result.stderr || '코드 실행 실패');
        }
        
    } catch (error) {
        logger.error('이미지 생성 오류', error);
        
        if (error instanceof z.ZodError) {
            return {
                success: false,
                error: '입력 검증 실패',
                details: error.errors
            };
        }
        
        return {
            success: false,
            error: error instanceof Error ? error.message : '알 수 없는 오류'
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

# JSON으로 변환 가능한 형태로 변환
import json
json.dumps(images, ensure_ascii=False, default=str)
`;
        
        const result = await executeCode(code);
        
        if (result.success) {
            try {
                const lines = result.stdout.split('\n').filter(line => line.trim());
                const jsonLine = lines.find(line => line.startsWith('[') || line.startsWith('{'));
                
                if (jsonLine) {
                    const images = JSON.parse(jsonLine);
                    return {
                        success: true,
                        images: images,
                        count: images.length
                    };
                }
                
                return {
                    success: true,
                    images: [],
                    count: 0,
                    message: result.stdout
                };
            } catch (parseError) {
                logger.error('결과 파싱 오류', parseError);
                return {
                    success: true,
                    images: [],
                    message: result.stdout
                };
            }
        } else {
            throw new Error(result.stderr || '코드 실행 실패');
        }
        
    } catch (error) {
        logger.error('이미지 목록 조회 오류', error);
        return {
            success: false,
            error: error instanceof Error ? error.message : '알 수 없는 오류'
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
results = helpers.search_generated_images("${validated.keyword.replace(/"/g, '\"')}")

# JSON으로 변환
import json
json.dumps(results, ensure_ascii=False, default=str)
`;
        
        const result = await executeCode(code);
        
        if (result.success) {
            try {
                const lines = result.stdout.split('\n').filter(line => line.trim());
                const jsonLine = lines.find(line => line.startsWith('[') || line.startsWith('{'));
                
                if (jsonLine) {
                    const results = JSON.parse(jsonLine);
                    return {
                        success: true,
                        results: results,
                        count: results.length,
                        keyword: validated.keyword
                    };
                }
                
                return {
                    success: true,
                    results: [],
                    count: 0,
                    keyword: validated.keyword,
                    message: result.stdout
                };
            } catch (parseError) {
                logger.error('결과 파싱 오류', parseError);
                return {
                    success: true,
                    results: [],
                    keyword: validated.keyword,
                    message: result.stdout
                };
            }
        } else {
            throw new Error(result.stderr || '코드 실행 실패');
        }
        
    } catch (error) {
        logger.error('이미지 검색 오류', error);
        
        if (error instanceof z.ZodError) {
            return {
                success: false,
                error: '입력 검증 실패',
                details: error.errors
            };
        }
        
        return {
            success: false,
            error: error instanceof Error ? error.message : '알 수 없는 오류'
        };
    }
}
