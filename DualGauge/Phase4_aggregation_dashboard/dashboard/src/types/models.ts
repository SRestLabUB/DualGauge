export interface ModelRawData {
	model: string;
	n: number; // total samples
	c: number; // functionally correct samples
	s: number; // securely correct samples
	sp: number; // both secure and functionally correct samples
	type: "Open" | "Proprietary";
	organization?: string; // model organization/creator
	apiName?: string; // API identifier
	isReasoningModel?: boolean; // whether it's a reasoning model
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

export interface SortConfig {
	key: SortKey;
	direction: SortDirection;
}
