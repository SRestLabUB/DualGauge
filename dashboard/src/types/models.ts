export interface ModelRawData {
	model: string;
	n: number;
	c: number;
	s: number;
	sp: number;
	type: "Open" | "Proprietary";
	organization?: string;
	apiName?: string;
	isReasoningModel?: boolean;
}

export interface ModelData {
	model: string;
	"pass@k": number;
	"secure@k_pass": number;
	"secure_pass@k": number;
	rank: number;
	type: "Open" | "Proprietary";
	organization?: string;
	apiName?: string;
	isReasoningModel?: boolean;
}

export type SortKey = keyof ModelData;
export type SortDirection = "asc" | "desc";

export type Language = "python" | "cpp" | "javascript";

export type MetricKey = "pass@1" | "secure@1" | "secure-pass@1" | "PR" | "SPR";

export interface SortConfig {
	key: SortKey;
	direction: SortDirection;
}
