"use client";

import React from "react";
import AnimatedSection from "./AnimatedSection";

const FindingsSection: React.FC = () => {
	return (
		<section id="findings" className="py-24">
			<AnimatedSection>
				<p
					className="mb-2 text-xs font-semibold uppercase tracking-widest"
					style={{ color: "var(--color-accent)" }}
				>
					Findings
				</p>
				<h2
					className="mb-6 text-2xl font-bold"
					style={{ color: "var(--color-text-primary)" }}
				>
					Key Results
				</h2>
			</AnimatedSection>

			<AnimatedSection delay={0.1}>
				<div className="space-y-3">
					{[
						{
							title: "Joint performance is critically low",
							body: "Even the strongest model (GPT-5 Medium) remains below 15% secure-pass@1 in every language, despite reaching nearly 39% functional pass rate on Python.",
						},
						{
							title: "Functional correctness is a poor proxy",
							body: "secure@1 consistently exceeds secure-pass@1 across all models — models can produce secure code, they just don't do so consistently alongside correctness.",
						},
						{
							title: "Model-side factors don't reliably help",
							body: "Scale, extended thinking, quantization, instruction tuning, and code specialization each shift metrics differently. No factor reliably improves the joint metric — secure generation is not emergent from stronger coding capability.",
						},
						{
							title: "Agentic systems don't improve over direct generation",
							body: "OpenHands underperforms Codex on every metric despite using the same underlying model. Agents spend effort on repository-oriented overhead and substitute self-generated tests for ground-truth feedback.",
						},
						{
							title: "Failures are about coverage, not knowledge",
							body: "Security failures reveal partial defenses — guards that look reasonable but fail to cover the actual attack vector. Models are not unaware of security requirements; they address them incompletely.",
						},
					].map((item) => (
						<div key={item.title} className="card-dark rounded-xl p-5">
							<h3
								className="mb-2 text-sm font-semibold"
								style={{ color: "var(--color-text-primary)" }}
							>
								{item.title}
							</h3>
							<p
								className="text-sm leading-relaxed"
								style={{ color: "var(--color-text-secondary)" }}
							>
								{item.body}
							</p>
						</div>
					))}
				</div>
			</AnimatedSection>
		</section>
	);
};

export default FindingsSection;
