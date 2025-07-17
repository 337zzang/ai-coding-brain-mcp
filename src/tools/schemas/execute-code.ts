/**
 * Execute Code Tool Schema
 * JSON Schema definition for the execute_code tool
 */

export const executeCodeSchema = {
  type: "object" as const,  // "object" 리터럴 타입으로 지정
  properties: {
    code: {
      type: "string" as const,
      description: "실행할 Python 코드"
    },
    language: {
      type: "string" as const,
      enum: ["python"] as const,
      default: "python",
      description: "프로그래밍 언어 (현재 Python만 지원)"
    }
  },
  required: ["code"] as string[],
  additionalProperties: false
};

/**
 * TypeScript type derived from schema
 */
export interface ExecuteCodeInput {
  code: string;
  language?: "python";
}
