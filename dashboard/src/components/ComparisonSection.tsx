"use client";

import React from "react";
import AnimatedSection from "./AnimatedSection";

const benchmarks = [
	{ name: "Pearce et al.", url: "https://arxiv.org/abs/2108.09293", secTest: false, funcTest: false, paired: false, pureNL: false, langAgn: false, cov: false },
	{ name: "SecurityEval", url: "https://github.com/s2e-lab/SecurityEval", secTest: false, funcTest: false, paired: false, pureNL: false, langAgn: false, cov: false },
	{ name: "CodeLMSec", url: "https://arxiv.org/abs/2302.04012", secTest: false, funcTest: false, paired: false, pureNL: false, langAgn: false, cov: false },
	{ name: "SecuCoGen", url: "https://arxiv.org/abs/2310.16263", secTest: false, funcTest: false, paired: false, pureNL: "partial", langAgn: false, cov: false },
	{ name: "SafeGenBench", url: "https://arxiv.org/abs/2506.05692", secTest: false, funcTest: false, paired: false, pureNL: true, langAgn: false, cov: false },
	{ name: "CodeGuard+", url: "https://arxiv.org/abs/2405.00218", secTest: false, funcTest: true, paired: false, pureNL: false, langAgn: false, cov: false },
	{ name: "LiveBench", url: "https://livebench.ai", secTest: false, funcTest: false, paired: false, pureNL: false, langAgn: false, cov: false },
	{ name: "SecCodePLT", url: "https://arxiv.org/abs/2410.11096", secTest: "partial", funcTest: "partial", paired: "partial", pureNL: false, langAgn: false, cov: false },
	{ name: "CWEval", url: "https://arxiv.org/abs/2501.08200", secTest: true, funcTest: true, paired: true, pureNL: false, langAgn: false, cov: false },
	{ name: "SecRepoBench", url: "https://arxiv.org/abs/2504.21205", secTest: true, funcTest: true, paired: true, pureNL: false, langAgn: false, cov: false },
	{ name: "SecureAgentBench", url: "https://arxiv.org/abs/2509.22097", secTest: "partial", funcTest: true, paired: true, pureNL: false, langAgn: false, cov: false },
	{ name: "SUSVIBES", url: "https://arxiv.org/abs/2512.03262", secTest: true, funcTest: true, paired: true, pureNL: false, langAgn: false, cov: false },
	{ name: "BaxBench", url: "https://arxiv.org/abs/2502.11844", secTest: true, funcTest: true, paired: true, pureNL: false, langAgn: false, cov: false },
	{ name: "DualGauge-Bench", url: "https://anonymous.4open.science/r/DualGauge_EMNLP26-07B3", secTest: true, funcTest: true, paired: true, pureNL: true, langAgn: true, cov: true },
];

const cols = [
	{ key: "secTest" as const, label: "Security Tests", short: "SecTest" },
	{ key: "funcTest" as const, label: "Functional Tests", short: "FuncTest" },
	{ key: "paired" as const, label: "Paired Tasks", short: "Paired" },
	{ key: "pureNL" as const, label: "Pure NL Spec.", short: "Pure NL" },
	{ key: "langAgn" as const, label: "Language-Agnostic", short: "Lang.-agn." },
	{ key: "cov" as const, label: "Coverage-Enforced", short: "Cov." },
];

function renderCell(val: boolean | string) {
	if (val === true)
		return <span className="text-base" style={{ color: "#34d399" }}>&#10003;</span>;
	if (val === "partial")
		return <span className="text-base" style={{ color: "#fbbf24" }}>&#9679;</span>;
	return <span className="text-base font-bold" style={{ color: "#f87171" }}>&#10005;</span>;
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
											className="px-3 py-3 text-center text-xs font-semibold tracking-wider"
											style={{
												color: "var(--color-text-secondary)",
												backgroundColor: "var(--color-bg-secondary)",
												minWidth: "80px",
											}}
										>
											<div>{c.label}</div>
											<div className="mt-0.5 font-normal opacity-60">({c.short})</div>
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
												{b.url ? (
													<a
														href={b.url}
														target="_blank"
														rel="noopener noreferrer"
														className="text-sm underline underline-offset-2 hover:opacity-80 transition-opacity"
														style={{
															color: isDualGauge
																? "var(--color-accent)"
																: "#60a5fa",
															fontWeight: isDualGauge ? 600 : 400,
														}}
													>
														{b.name}
													</a>
												) : (
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
												)}
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
					className="mt-3 max-w-3xl text-xs leading-relaxed"
					style={{ color: "var(--color-text-secondary)", opacity: 0.7 }}
				>
					Adapted from Table 1 of the paper.{" "}
					<strong>SecTest</strong> = dynamic security tests;{" "}
					<strong>FuncTest</strong> = functional tests;{" "}
					<strong>Paired</strong> = tests paired for the same coding task;{" "}
					<strong>Pure NL Spec.</strong> = task purely specified by natural language;{" "}
					<strong>Lang.-agn.</strong> = programming-language-agnostic design;{" "}
					<strong>Cov.</strong> = coverage-enforced construction.{" "}
					&#10003; full support &nbsp;&#9679; partial &nbsp;<span style={{ color: "#f87171" }}>&#10005;</span> not supported.
				</p>
			</AnimatedSection>
		</section>
	);
};

export default ComparisonSection;
