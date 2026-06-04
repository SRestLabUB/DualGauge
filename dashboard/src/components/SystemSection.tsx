"use client";

import React from "react";
import AnimatedSection from "./AnimatedSection";

const phases = [
	{
		num: "1",
		title: "Sample Generation",
		desc: "Query the target LLM or coding agent to generate candidate code from specification-only prompts.",
	},
	{
		num: "2",
		title: "Agentic Execution",
		desc: "An LLM-guided executor runs each candidate in isolated containers, stabilizing execution without altering generated logic.",
	},
	{
		num: "3",
		title: "Runtime Evaluation",
		desc: "Functional oracle uses exact output matching. Security oracle uses LLM judgment over code, outputs, and coverage traces.",
	},
	{
		num: "4",
		title: "Result Aggregation",
		desc: "Aggregates per-test verdicts into pass@k, secure@k, and secure-pass@k metrics across the benchmark.",
	},
];

const SystemSection: React.FC = () => {
	return (
		<section id="system" className="py-24">
			<AnimatedSection>
				<p
					className="mb-2 text-xs font-semibold uppercase tracking-widest"
					style={{ color: "var(--color-accent)" }}
				>
					System
				</p>
				<h2
					className="mb-6 text-2xl font-bold"
					style={{ color: "var(--color-text-primary)" }}
				>
					DualGauge Pipeline
				</h2>
				<p
					className="mb-10 max-w-2xl leading-relaxed"
					style={{ color: "var(--color-text-secondary)" }}
				>
					A fully automated benchmarking system for joint
					security-functionality evaluation. DualGauge combines an agentic
					execution engine with an LLM-based runtime evaluator that reasons
					over candidate code, execution outputs, and coverage traces.
				</p>
			</AnimatedSection>

			<AnimatedSection delay={0.1}>
				<div className="grid gap-3 md:grid-cols-2">
					{phases.map((p) => (
						<div key={p.num} className="card-dark rounded-xl p-5">
							<div className="mb-3 flex items-center gap-3">
								<span
									className="font-mono-data flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold"
									style={{
										backgroundColor: "var(--color-accent-dim)",
										color: "var(--color-accent)",
										border: "1px solid var(--color-border-accent)",
									}}
								>
									{p.num}
								</span>
								<h3
									className="text-sm font-semibold"
									style={{ color: "var(--color-text-primary)" }}
								>
									{p.title}
								</h3>
							</div>
							<p
								className="text-sm leading-relaxed"
								style={{ color: "var(--color-text-secondary)" }}
							>
								{p.desc}
							</p>
						</div>
					))}
				</div>
			</AnimatedSection>
		</section>
	);
};

export default SystemSection;
