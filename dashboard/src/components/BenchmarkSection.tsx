"use client";

import React from "react";
import AnimatedSection from "./AnimatedSection";

const stats = [
	{ label: "Coding Tasks", value: "307" },
	{ label: "CWE Categories", value: "90" },
	{ label: "Languages", value: "3" },
	{ label: "LLMs Evaluated", value: "10" },
	{ label: "Agent Systems", value: "3" },
	{ label: "Configurations", value: "45" },
];

const BenchmarkSection: React.FC = () => {
	return (
		<section id="benchmark" className="py-24">
			<AnimatedSection>
				<p
					className="mb-2 text-xs font-semibold uppercase tracking-widest"
					style={{ color: "var(--color-accent)" }}
				>
					Benchmark
				</p>
				<h2
					className="mb-6 text-2xl font-bold"
					style={{ color: "var(--color-text-primary)" }}
				>
					DualGauge-Bench
				</h2>
				<p
					className="mb-4 max-w-2xl leading-relaxed"
					style={{ color: "var(--color-text-secondary)" }}
				>
					The first language-agnostic benchmark that pairs each
					specification-only prompt with dual, coverage-enforced functional
					and security test suites. Each task is a pure natural-language
					specification — no partial code, function signatures, or
					framework scaffolding.
				</p>
				<p
					className="mb-10 max-w-2xl leading-relaxed"
					style={{ color: "var(--color-text-secondary)" }}
				>
					Tests are constructed through a human-LLM co-creation process,
					with functional tests guided by boundary value analysis and
					equivalence-class partitioning, and security tests derived from
					OWASP and CERT principles. Currently instantiated across Python,
					C++, and JavaScript.
				</p>
			</AnimatedSection>

			<AnimatedSection delay={0.1}>
				<div className="grid grid-cols-3 gap-3 md:grid-cols-6">
					{stats.map((stat) => (
						<div
							key={stat.label}
							className="card-dark rounded-xl px-4 py-4 text-center"
						>
							<div
								className="font-mono-data text-xl font-bold"
								style={{ color: "var(--color-accent)" }}
							>
								{stat.value}
							</div>
							<div
								className="mt-1 text-xs font-medium"
								style={{ color: "var(--color-text-secondary)" }}
							>
								{stat.label}
							</div>
						</div>
					))}
				</div>
			</AnimatedSection>
		</section>
	);
};

export default BenchmarkSection;
