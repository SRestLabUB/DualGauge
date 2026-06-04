"use client";

import React from "react";
import { DualGaugeModel } from "../data/models";
import { Language } from "../types/models";

interface ModelDetailModalProps {
	model: DualGaugeModel;
	onClose: () => void;
}

const LANGS: { key: Language; label: string }[] = [
	{ key: "python", label: "Python" },
	{ key: "cpp", label: "C++" },
	{ key: "javascript", label: "JavaScript" },
];

const METRICS = [
	{ key: "PR" as const, label: "Pass Rate (PR)", desc: "% of functional test cases passed" },
	{ key: "SPR" as const, label: "Secure Pass Rate (SPR)", desc: "% of security test cases passed" },
	{ key: "pass@1" as const, label: "pass@1", desc: "Prob. of generating correct code in one attempt" },
	{ key: "secure@1" as const, label: "secure@1", desc: "Prob. of generating secure code in one attempt" },
	{ key: "secure-pass@1" as const, label: "secure-pass@1", desc: "Prob. of generating both correct and secure code" },
];

function scoreColor(v: number): string {
	if (v >= 40) return "#34d399";
	if (v >= 20) return "#fbbf24";
	if (v > 0) return "#f87171";
	return "var(--color-text-secondary)";
}

const ModelDetailModal: React.FC<ModelDetailModalProps> = ({ model, onClose }) => {
	return (
		<div
			className="fixed inset-0 z-50 flex items-center justify-center p-4"
			style={{ backgroundColor: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }}
			onClick={onClose}
		>
			<div
				className="card-dark relative w-full max-w-3xl max-h-[85vh] overflow-y-auto rounded-xl p-6"
				onClick={(e) => e.stopPropagation()}
			>
				{/* Header */}
				<div className="mb-6 flex items-start justify-between">
					<div>
						<h2
							className="text-xl font-bold"
							style={{ color: "var(--color-text-primary)" }}
						>
							{model.model}
						</h2>
						<div className="mt-1 flex items-center gap-3">
							<span className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
								{model.organization}
							</span>
							<span
								className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
								style={{
									backgroundColor:
										model.type === "Open"
											? "rgba(52,211,153,0.1)"
											: model.type === "Agent"
											? "rgba(168,85,247,0.1)"
											: "var(--color-accent-dim)",
									color:
										model.type === "Open"
											? "#34d399"
											: model.type === "Agent"
											? "#a855f7"
											: "var(--color-accent)",
									border: `1px solid ${
										model.type === "Open"
											? "rgba(52,211,153,0.2)"
											: model.type === "Agent"
											? "rgba(168,85,247,0.2)"
											: "var(--color-border-accent)"
									}`,
								}}
							>
								{model.type}
							</span>
							{model.isReasoningModel && (
								<span
									className="rounded-full px-2 py-0.5 text-xs font-medium"
									style={{
										backgroundColor: "rgba(251,191,36,0.1)",
										color: "#fbbf24",
										border: "1px solid rgba(251,191,36,0.2)",
									}}
								>
									Thinking
								</span>
							)}
						</div>
					</div>
					<button
						onClick={onClose}
						className="flex h-8 w-8 items-center justify-center rounded-lg transition-colors"
						style={{ color: "var(--color-text-secondary)" }}
					>
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
							<path d="M18 6L6 18M6 6l12 12" />
						</svg>
					</button>
				</div>

				{/* Cross-language comparison table */}
				<div className="overflow-x-auto">
					<table className="w-full">
						<thead>
							<tr style={{ borderBottom: "1px solid var(--color-border)" }}>
								<th
									className="py-2.5 pr-4 text-left text-xs font-semibold uppercase tracking-wider"
									style={{ color: "var(--color-text-secondary)" }}
								>
									Metric
								</th>
								{LANGS.map((l) => (
									<th
										key={l.key}
										className="px-4 py-2.5 text-center text-xs font-semibold uppercase tracking-wider"
										style={{ color: "var(--color-text-secondary)" }}
									>
										{l.label}
									</th>
								))}
							</tr>
						</thead>
						<tbody>
							{METRICS.map((m, i) => (
								<tr
									key={m.key}
									style={{
										borderBottom:
											i < METRICS.length - 1 ? "1px solid var(--color-border)" : "none",
									}}
								>
									<td className="py-3 pr-4">
										<div
											className="font-mono-data text-sm font-semibold"
											style={{ color: "var(--color-text-primary)" }}
										>
											{m.label}
										</div>
										<div className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
											{m.desc}
										</div>
									</td>
									{LANGS.map((l) => {
										const val = model[l.key][m.key];
										return (
											<td key={l.key} className="px-4 py-3 text-center">
												<span
													className="font-mono-data text-sm font-bold"
													style={{ color: scoreColor(val) }}
												>
													{val}%
												</span>
											</td>
										);
									})}
								</tr>
							))}
						</tbody>
					</table>
				</div>

				{/* Best performing language highlight */}
				<div
					className="mt-6 rounded-lg p-4"
					style={{
						backgroundColor: "var(--color-accent-dim)",
						border: "1px solid var(--color-border-accent)",
					}}
				>
					<h4
						className="mb-2 text-xs font-semibold uppercase tracking-wider"
						style={{ color: "var(--color-text-primary)" }}
					>
						Summary
					</h4>
					<div className="grid grid-cols-3 gap-4">
						{LANGS.map((l) => {
							const sp = model[l.key]["secure-pass@1"];
							return (
								<div key={l.key} className="text-center">
									<div className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
										{l.label}
									</div>
									<div
										className="font-mono-data text-lg font-bold"
										style={{ color: scoreColor(sp) }}
									>
										{sp}%
									</div>
									<div className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
										secure-pass@1
									</div>
								</div>
							);
						})}
					</div>
				</div>
			</div>
		</div>
	);
};

export default ModelDetailModal;
