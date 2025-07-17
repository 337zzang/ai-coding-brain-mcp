/**
 * Restart REPL Tool Schema
 * JSON Schema definition for the restart_json_repl tool
 */

export const restartReplSchema = {
  type: "object" as const,  // "object" 리터럴 타입으로 지정
  properties: {
    keep_helpers: {
      type: "boolean" as const,
      default: true,
      description: "helpers 객체 유지 여부"
    },
    reason: {
      type: "string" as const,
      default: "세션 새로고침",
      description: "재시작 이유"
    }
  },
  required: [] as string[],
  additionalProperties: false
};

/**
 * TypeScript type derived from schema
 */
export interface RestartReplInput {
  keep_helpers?: boolean;
  reason?: string;
}
