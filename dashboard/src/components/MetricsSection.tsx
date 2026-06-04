"use client";

import React from "react";
import AnimatedSection from "./AnimatedSection";

const MetricsSection: React.FC = () => {
	return (
		<section id="metrics" className="py-24">
			<AnimatedSection>
				<p
					className="mb-2 text-xs font-semibold uppercase tracking-widest"
					style={{ color: "var(--color-accent)" }}
				>
					Metrics
				</p>
				<h2
					className="mb-6 text-2xl font-bold"
					style={{ color: "var(--color-text-primary)" }}
				>
					Joint Evaluation Metrics
				</h2>
				<p
					className="mb-10 max-w-2xl leading-relaxed"
					style={{ color: "var(--color-text-secondary)" }}
				>
					Given n sampled solutions for a benchmark problem, with c
					functionally correct, s securely correct, and sp satisfying both,
					DualGauge computes three complementary metrics plus two aggregate rates.
				</p>
			</AnimatedSection>

			<AnimatedSection delay={0.1}>
				<div className="space-y-3">
					{[
						{
							name: "pass@k",
							formula: "1 − C(n−c, k) / C(n, k)",
							desc: "Functional correctness — probability that at least one of k samples satisfies the specification.",
						},
						{
							name: "secure@k",
							formula: "1 − C(n−s, k) / C(n, k)",
							desc: "Security correctness — probability that at least one of k samples is secure.",
						},
						{
							name: "secure-pass@k",
							formula: "1 − C(n−sp, k) / C(n, k)",
							desc: "Joint security-functionality — probability of generating code that is both correct and secure. The primary metric.",
						},
					].map((m) => (
						<div key={m.name} className="card-dark rounded-xl p-5">
							<div className="mb-2 flex flex-wrap items-baseline gap-3">
								<code
									className="font-mono-data text-sm font-bold"
									style={{ color: "var(--color-accent)" }}
								>
									{m.name}
								</code>
								<span
									className="font-mono-data text-xs"
									style={{ color: "var(--color-text-secondary)" }}
								>
									= {m.formula}
								</span>
							</div>
							<p className="text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
								{m.desc}
							</p>
						</div>
					))}
				</div>
			</AnimatedSection>

			<AnimatedSection delay={0.15}>
				<div className="mt-3 grid gap-3 md:grid-cols-2">
					{[
						{
							name: "PR (Pass Rate)",
							formula: "P_func / T_func",
							desc: "Proportion of functional test cases passed across the entire benchmark.",
						},
						{
							name: "SPR (Secure Pass Rate)",
							formula: "P_sec / T_sec",
							desc: "Proportion of security test cases passed across the entire benchmark.",
						},
					].map((m) => (
						<div key={m.name} className="card-dark rounded-xl p-5">
							<div className="mb-2 flex flex-wrap items-baseline gap-3">
								<code
									className="font-mono-data text-sm font-bold"
									style={{ color: "var(--color-accent)" }}
								>
									{m.name}
								</code>
								<span
									className="font-mono-data text-xs"
									style={{ color: "var(--color-text-secondary)" }}
								>
									= {m.formula}
								</span>
							</div>
							<p className="text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
								{m.desc}
							</p>
						</div>
					))}
				</div>
			</AnimatedSection>
		</section>
	);
};

export default MetricsSection;
