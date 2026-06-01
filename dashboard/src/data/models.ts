import { ModelRawData } from "../types/models";

export interface LanguageResult {
	PR: number;
	SPR: number;
	"pass@1": number;
	"secure@1": number;
	"secure-pass@1": number;
}

export interface DualGaugeModel {
	id: string;
	model: string;
	organization: string;
	type: "Open" | "Proprietary" | "Agent";
	isReasoningModel: boolean;
	isAgent: boolean;
	python: LanguageResult;
	cpp: LanguageResult;
	javascript: LanguageResult;
}

// Data from Table 2 of the DualGauge paper (10 LLMs)
export const dualGaugeModels: DualGaugeModel[] = [
	{
		id: "gpt-5-medium",
		model: "GPT-5 Medium",
		organization: "OpenAI",
		type: "Proprietary",
		isReasoningModel: false,
		isAgent: false,
		python: { PR: 73.2, SPR: 72.7, "pass@1": 38.6, "secure@1": 34.5, "secure-pass@1": 14.8 },
		cpp: { PR: 54.1, SPR: 73.3, "pass@1": 19.8, "secure@1": 30.4, "secure-pass@1": 8.4 },
		javascript: { PR: 47.9, SPR: 72.9, "pass@1": 20.0, "secure@1": 32.4, "secure-pass@1": 8.0 },
	},
	{
		id: "gpt-4.1",
		model: "GPT-4.1",
		organization: "OpenAI",
		type: "Proprietary",
		isReasoningModel: false,
		isAgent: false,
		python: { PR: 65.2, SPR: 68.4, "pass@1": 31.3, "secure@1": 23.4, "secure-pass@1": 8.7 },
		cpp: { PR: 49.0, SPR: 63.5, "pass@1": 19.5, "secure@1": 23.2, "secure-pass@1": 5.9 },
		javascript: { PR: 42.9, SPR: 63.5, "pass@1": 16.1, "secure@1": 23.3, "secure-pass@1": 4.5 },
	},
	{
		id: "claude-opus-4-7-think",
		model: "Claude Opus 4.7 (think-on)",
		organization: "Anthropic",
		type: "Proprietary",
		isReasoningModel: true,
		isAgent: false,
		python: { PR: 70.3, SPR: 59.6, "pass@1": 33.9, "secure@1": 24.0, "secure-pass@1": 10.2 },
		cpp: { PR: 52.6, SPR: 63.8, "pass@1": 19.2, "secure@1": 24.9, "secure-pass@1": 5.0 },
		javascript: { PR: 49.2, SPR: 50.4, "pass@1": 24.3, "secure@1": 24.3, "secure-pass@1": 7.0 },
	},
	{
		id: "claude-sonnet-4-5",
		model: "Claude Sonnet 4.5 (think-off)",
		organization: "Anthropic",
		type: "Proprietary",
		isReasoningModel: false,
		isAgent: false,
		python: { PR: 68.5, SPR: 57.1, "pass@1": 31.3, "secure@1": 20.2, "secure-pass@1": 8.4 },
		cpp: { PR: 49.0, SPR: 59.4, "pass@1": 19.0, "secure@1": 23.6, "secure-pass@1": 5.4 },
		javascript: { PR: 46.8, SPR: 56.6, "pass@1": 21.4, "secure@1": 23.6, "secure-pass@1": 6.6 },
	},
	{
		id: "claude-haiku-4-5",
		model: "Claude Haiku 4.5",
		organization: "Anthropic",
		type: "Proprietary",
		isReasoningModel: false,
		isAgent: false,
		python: { PR: 40.8, SPR: 55.2, "pass@1": 17.8, "secure@1": 18.8, "secure-pass@1": 6.5 },
		cpp: { PR: 42.6, SPR: 57.8, "pass@1": 18.2, "secure@1": 22.7, "secure-pass@1": 5.3 },
		javascript: { PR: 32.3, SPR: 50.8, "pass@1": 15.5, "secure@1": 15.9, "secure-pass@1": 2.9 },
	},
	{
		id: "llama-3.1-8b",
		model: "Llama 3.1 8B Instruct (bf16)",
		organization: "Meta",
		type: "Open",
		isReasoningModel: false,
		isAgent: false,
		python: { PR: 48.5, SPR: 49.2, "pass@1": 22.5, "secure@1": 14.4, "secure-pass@1": 5.1 },
		cpp: { PR: 15.1, SPR: 35.4, "pass@1": 4.5, "secure@1": 5.9, "secure-pass@1": 0.9 },
		javascript: { PR: 30.3, SPR: 44.8, "pass@1": 9.0, "secure@1": 12.8, "secure-pass@1": 2.3 },
	},
	{
		id: "qwen3-14b",
		model: "Qwen3 14B",
		organization: "Alibaba",
		type: "Open",
		isReasoningModel: false,
		isAgent: false,
		python: { PR: 60.2, SPR: 56.5, "pass@1": 27.4, "secure@1": 17.5, "secure-pass@1": 5.6 },
		cpp: { PR: 24.8, SPR: 46.1, "pass@1": 12.3, "secure@1": 11.5, "secure-pass@1": 1.5 },
		javascript: { PR: 37.5, SPR: 55.9, "pass@1": 13.9, "secure@1": 18.7, "secure-pass@1": 3.0 },
	},
	{
		id: "qwen2.5-coder-32b",
		model: "Qwen2.5 Coder 32B Instruct",
		organization: "Alibaba",
		type: "Open",
		isReasoningModel: false,
		isAgent: false,
		python: { PR: 64.2, SPR: 56.5, "pass@1": 29.5, "secure@1": 20.3, "secure-pass@1": 7.2 },
		cpp: { PR: 23.3, SPR: 43.5, "pass@1": 7.0, "secure@1": 10.1, "secure-pass@1": 1.6 },
		javascript: { PR: 39.7, SPR: 50.1, "pass@1": 13.0, "secure@1": 14.8, "secure-pass@1": 2.2 },
	},
	{
		id: "codestral-22b",
		model: "Codestral 22B v0.1",
		organization: "Mistral",
		type: "Open",
		isReasoningModel: false,
		isAgent: false,
		python: { PR: 63.7, SPR: 49.8, "pass@1": 27.5, "secure@1": 14.8, "secure-pass@1": 4.5 },
		cpp: { PR: 23.3, SPR: 41.5, "pass@1": 7.0, "secure@1": 10.1, "secure-pass@1": 1.6 },
		javascript: { PR: 37.6, SPR: 48.8, "pass@1": 10.7, "secure@1": 12.5, "secure-pass@1": 0.0 },
	},
	{
		id: "gemma-3-27b",
		model: "Gemma 3 27B IT",
		organization: "Google",
		type: "Open",
		isReasoningModel: false,
		isAgent: false,
		python: { PR: 61.5, SPR: 56.6, "pass@1": 27.3, "secure@1": 19.6, "secure-pass@1": 6.9 },
		cpp: { PR: 28.3, SPR: 45.5, "pass@1": 8.1, "secure@1": 13.5, "secure-pass@1": 1.2 },
		javascript: { PR: 36.6, SPR: 52.2, "pass@1": 13.8, "secure@1": 18.8, "secure-pass@1": 2.7 },
	},
];

// Data from Table 4 of the DualGauge paper (3 agentic systems)
export const agentModels: DualGaugeModel[] = [
	{
		id: "codex-gpt-5.4",
		model: "Codex (GPT-5.4)",
		organization: "OpenAI",
		type: "Agent",
		isReasoningModel: false,
		isAgent: true,
		python: { PR: 71.7, SPR: 78.5, "pass@1": 46.7, "secure@1": 50.7, "secure-pass@1": 24.3 },
		cpp: { PR: 34.1, SPR: 77.6, "pass@1": 15.1, "secure@1": 46.2, "secure-pass@1": 8.9 },
		javascript: { PR: 44.2, SPR: 78.7, "pass@1": 23.4, "secure@1": 48.5, "secure-pass@1": 13.5 },
	},
	{
		id: "openhands-gpt-5.4",
		model: "OpenHands (GPT-5.4)",
		organization: "OpenHands",
		type: "Agent",
		isReasoningModel: false,
		isAgent: true,
		python: { PR: 49.4, SPR: 63.2, "pass@1": 27.3, "secure@1": 29.6, "secure-pass@1": 9.5 },
		cpp: { PR: 29.3, SPR: 65.4, "pass@1": 12.9, "secure@1": 29.8, "secure-pass@1": 5.0 },
		javascript: { PR: 36.2, SPR: 63.3, "pass@1": 14.2, "secure@1": 30.1, "secure-pass@1": 4.6 },
	},
	{
		id: "claude-code-opus-4.7",
		model: "Claude Code (Opus 4.7)",
		organization: "Anthropic",
		type: "Agent",
		isReasoningModel: false,
		isAgent: true,
		python: { PR: 40.5, SPR: 53.2, "pass@1": 21.7, "secure@1": 19.4, "secure-pass@1": 4.9 },
		cpp: { PR: 16.0, SPR: 59.0, "pass@1": 4.3, "secure@1": 22.0, "secure-pass@1": 1.6 },
		javascript: { PR: 23.1, SPR: 61.7, "pass@1": 10.6, "secure@1": 26.6, "secure-pass@1": 2.0 },
	},
];

export const allModels: DualGaugeModel[] = [...dualGaugeModels, ...agentModels];

// Legacy exports for backward compat (used by old metricsCalculator)
export const modelRawData: ModelRawData[] = [];
