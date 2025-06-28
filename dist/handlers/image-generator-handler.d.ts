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
/**
 * AI 이미지 생성
 */
export declare function generateAiImage(params: unknown): Promise<{
    content: ContentItem[];
} | {
    content: {
        type: string;
        text: string;
    }[];
}>;
/**
 * AI 이미지 목록 조회 (썸네일 포함)
 */
export declare function listAiImages(): Promise<{
    content: ContentItem[];
} | {
    content: {
        type: string;
        text: string;
    }[];
}>;
/**
 * AI 이미지 검색
 */
export declare function searchAiImages(params: unknown): Promise<{
    content: ContentItem[];
} | {
    content: {
        type: string;
        text: string;
    }[];
}>;
export {};
//# sourceMappingURL=image-generator-handler.d.ts.map