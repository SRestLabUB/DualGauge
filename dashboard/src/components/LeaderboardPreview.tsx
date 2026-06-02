"use client";

import React from "react";
import AnimatedSection from "./AnimatedSection";
import { dualGaugeModels } from "../data/models";

function scoreColor(v: number): string {
	if (v >= 40) return "#34d399";
	if (v >= 20) return "#fbbf24";
	if (v > 0) return "#f87171";
	return "var(--color-text-secondary)";
}

const LeaderboardPreview: React.FC = () => {
	const topModels = [...dualGaugeModels]
		.sort((a, b) => b.python["secure-pass@1"] - a.python["secure-pass@1"])
		.slice(0, 5);

	return (
		<section id="leaderboard" className="py-24">
			<AnimatedSection>
				<p
					className="mb-2 text-xs font-semibold uppercase tracking-widest"
					style={{ color: "var(--color-accent)" }}
				>
					Leaderboard
				</p>
				<h2
					className="mb-6 text-2xl font-bold"
					style={{ color: "var(--color-text-primary)" }}
				>
					Top Models (Python, k=1)
				</h2>
				<p
					className="mb-8 max-w-2xl leading-relaxed"
					style={{ color: "var(--color-text-secondary)" }}
				>
					Even the strongest model remains below 15% secure-pass@1 in every
					language. The full leaderboard includes 10 LLMs and 3 agentic
					coding systems across Python, C++, and JavaScript.
				</p>
			</AnimatedSection>

			<AnimatedSection delay={0.1}>
				<div className="card-dark overflow-hidden rounded-xl">
					<table className="w-full">
						<thead>
							<tr style={{ borderBottom: "1px solid var(--color-border)" }}>
								{["#", "Model", "pass@1", "secure@1", "secure-pass@1"].map((h) => (
									<th
										key={h}
										className={`px-4 py-3 text-xs font-semibold uppercase tracking-wider ${
											h !== "#" && h !== "Model" ? "font-mono-data text-right" : "text-left"
										}`}
										style={{ color: "var(--color-text-secondary)" }}
									>
										{h}
									</th>
								))}
							</tr>
						</thead>
						<tbody>
							{topModels.map((m, i) => (
								<tr
									key={m.id}
									style={{
										borderBottom:
											i < topModels.length - 1
												? "1px solid var(--color-border)"
												: "none",
									}}
								>
									<td className="px-4 py-3 font-mono-data text-sm font-bold" style={{ color: "var(--color-text-secondary)" }}>
										{i + 1}
									</td>
									<td className="px-4 py-3">
										<span className="text-sm font-medium" style={{ color: "var(--color-text-primary)" }}>
											{m.model}
										</span>
										<span className="ml-2 text-xs" style={{ color: "var(--color-text-secondary)" }}>
											{m.organization}
										</span>
									</td>
									{(["pass@1", "secure@1", "secure-pass@1"] as const).map((metric) => (
										<td key={metric} className="px-4 py-3 text-right">
											<span
												className="font-mono-data text-sm font-semibold"
												style={{ color: scoreColor(m.python[metric]) }}
											>
												{m.python[metric]}%
											</span>
										</td>
									))}
								</tr>
							))}
						</tbody>
					</table>
				</div>
			</AnimatedSection>

			<AnimatedSection delay={0.15}>
				<p className="mt-4 text-xs leading-relaxed" style={{ color: "var(--color-text-secondary)", opacity: 0.8 }}>
					<strong style={{ color: "var(--color-text-primary)" }}>pass@1</strong> — fraction of problems where the single sample passes all functional tests (functional correctness). &nbsp;
					<strong style={{ color: "var(--color-text-primary)" }}>secure@1</strong> — same for all security tests (security correctness). &nbsp;
					<strong style={{ color: "var(--color-text-primary)" }}>secure-pass@1</strong> — fraction passing both functional and security tests simultaneously; the primary joint metric.
				</p>
			</AnimatedSection>

			<AnimatedSection delay={0.2}>
			<div className="mt-6 text-center">
					<a
						href="/leaderboard"
						className="inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition-all duration-200"
						style={{
							backgroundColor: "var(--color-accent-dim)",
							color: "var(--color-accent)",
							border: "1px solid var(--color-border-accent)",
						}}
					>
						View Full Leaderboard
						<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
							<path d="M5 12h14M12 5l7 7-7 7" />
						</svg>
					</a>
				</div>
			</AnimatedSection>
		</section>
	);
};

export default LeaderboardPreview;
