"use client";

import React from "react";
import AnimatedSection from "./AnimatedSection";

const benchmarks = [
	{ name: "Pearce et al.", secTest: false, funcTest: false, paired: false, pureNL: false, langAgn: false, cov: false },
	{ name: "SecurityEval", secTest: false, funcTest: false, paired: false, pureNL: false, langAgn: false, cov: false },
	{ name: "CodeLMSec", secTest: false, funcTest: false, paired: false, pureNL: false, langAgn: false, cov: false },
	{ name: "SecuCoGen", secTest: false, funcTest: false, paired: false, pureNL: "partial", langAgn: false, cov: false },
	{ name: "SafeGenBench", secTest: false, funcTest: false, paired: false, pureNL: true, langAgn: false, cov: false },
	{ name: "CodeGuard+", secTest: false, funcTest: true, paired: false, pureNL: false, langAgn: false, cov: false },
	{ name: "LiveBench", secTest: false, funcTest: false, paired: false, pureNL: false, langAgn: false, cov: false },
	{ name: "SecCodePLT", secTest: "partial", funcTest: "partial", paired: "partial", pureNL: false, langAgn: false, cov: false },
	{ name: "CWEval", secTest: true, funcTest: true, paired: true, pureNL: false, langAgn: false, cov: false },
	{ name: "SecRepoBench", secTest: true, funcTest: true, paired: true, pureNL: false, langAgn: false, cov: false },
	{ name: "SecureAgentBench", secTest: "partial", funcTest: true, paired: true, pureNL: false, langAgn: false, cov: false },
	{ name: "SUSVIBES", secTest: true, funcTest: true, paired: true, pureNL: false, langAgn: false, cov: false },
	{ name: "BaxBench", secTest: true, funcTest: true, paired: true, pureNL: false, langAgn: false, cov: false },
	{ name: "DualGauge-Bench", secTest: true, funcTest: true, paired: true, pureNL: true, langAgn: true, cov: true },
];

const cols = [
	{ key: "secTest" as const, label: "Sec Test" },
	{ key: "funcTest" as const, label: "Func Test" },
	{ key: "paired" as const, label: "Paired" },
	{ key: "pureNL" as const, label: "Pure NL" },
	{ key: "langAgn" as const, label: "Lang-Agn." },
	{ key: "cov" as const, label: "Coverage" },
];

function renderCell(val: boolean | string) {
	if (val === true)
		return <span style={{ color: "#34d399" }}>&#10003;</span>;
	if (val === "partial")
		return <span style={{ color: "#fbbf24" }}>&#9679;</span>;
	return <span style={{ color: "var(--color-text-secondary)", opacity: 0.3 }}>&#10005;</span>;
}

const ComparisonSection: React.FC = () => {
	return (
		<section id="comparison" className="py-24">
			<AnimatedSection>
				<p
					className="mb-2 text-xs font-semibold uppercase tracking-widest"
					style={{ color: "var(--color-accent)" }}
				>
					Related Work
				</p>
				<h2
					className="mb-6 text-2xl font-bold"
					style={{ color: "var(--color-text-primary)" }}
				>
					Benchmark Comparison
				</h2>
				<p
					className="mb-8 max-w-2xl leading-relaxed"
					style={{ color: "var(--color-text-secondary)" }}
				>
					DualGauge-Bench is the first benchmark to satisfy all six criteria:
					dynamic security tests, functional tests, paired evaluation on the
					same task, pure natural-language specification, language-agnostic
					design, and coverage-oriented construction.
				</p>
			</AnimatedSection>

			<AnimatedSection delay={0.1}>
				<div className="card-dark overflow-hidden rounded-xl">
					<div className="overflow-x-auto">
						<table className="w-full">
							<thead>
								<tr style={{ borderBottom: "1px solid var(--color-border)" }}>
									<th
										className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider"
										style={{
											color: "var(--color-text-secondary)",
											backgroundColor: "var(--color-bg-secondary)",
										}}
									>
										Benchmark
									</th>
									{cols.map((c) => (
										<th
											key={c.key}
											className="px-3 py-3 text-center text-xs font-semibold uppercase tracking-wider"
											style={{
												color: "var(--color-text-secondary)",
												backgroundColor: "var(--color-bg-secondary)",
											}}
										>
											{c.label}
										</th>
									))}
								</tr>
							</thead>
							<tbody>
								{benchmarks.map((b, i) => {
									const isDualGauge = b.name === "DualGauge-Bench";
									return (
										<tr
											key={b.name}
											style={{
												borderBottom:
													i < benchmarks.length - 1
														? "1px solid var(--color-border)"
														: "none",
												backgroundColor: isDualGauge
													? "var(--color-accent-dim)"
													: "transparent",
											}}
										>
											<td className="px-4 py-2.5">
												<span
													className="text-sm"
													style={{
														color: isDualGauge
															? "var(--color-accent)"
															: "var(--color-text-primary)",
														fontWeight: isDualGauge ? 600 : 400,
													}}
												>
													{b.name}
												</span>
											</td>
											{cols.map((c) => (
												<td key={c.key} className="px-3 py-2.5 text-center text-sm">
													{renderCell(b[c.key])}
												</td>
											))}
										</tr>
									);
								})}
							</tbody>
						</table>
					</div>
				</div>
				<p
					className="mt-3 text-xs"
					style={{ color: "var(--color-text-secondary)", opacity: 0.6 }}
				>
					Adapted from Table 1 of the paper. &#10003; = full support, &#9679; = partial, &#10005; = not supported.
				</p>
			</AnimatedSection>
		</section>
	);
};

export default ComparisonSection;
