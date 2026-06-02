"use client";

import React, { useState, useMemo } from "react";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";
import ModelDetailModal from "../../components/ModelDetailModal";
import { allModels, DualGaugeModel, LanguageResult } from "../../data/models";
import { Language } from "../../types/models";

type SortField = keyof LanguageResult | "model" | "organization" | "type";
type SortDir = "asc" | "desc";

const LANGUAGES: { key: Language; label: string }[] = [
	{ key: "python", label: "Python" },
	{ key: "cpp", label: "C++" },
	{ key: "javascript", label: "JavaScript" },
];

const METRIC_COLS: { key: keyof LanguageResult; label: string }[] = [
	{ key: "pass@1", label: "pass@1" },
	{ key: "secure@1", label: "secure@1" },
	{ key: "secure-pass@1", label: "secure-pass@1" },
	{ key: "PR", label: "PR" },
	{ key: "SPR", label: "SPR" },
];

function scoreColor(v: number): string {
	if (v >= 40) return "#34d399";
	if (v >= 20) return "#fbbf24";
	if (v > 0) return "#f87171";
	return "var(--color-text-secondary)";
}

function scoreBg(v: number): string {
	if (v >= 40) return "rgba(52,211,153,0.1)";
	if (v >= 20) return "rgba(251,191,36,0.1)";
	if (v > 0) return "rgba(248,113,113,0.1)";
	return "rgba(139,143,154,0.08)";
}

const LeaderboardPage: React.FC = () => {
	const [language, setLanguage] = useState<Language>("python");
	const [search, setSearch] = useState("");
	const [showAgents, setShowAgents] = useState(true);
	const [showOpenOnly, setShowOpenOnly] = useState(false);
	const [sortField, setSortField] = useState<SortField>("secure-pass@1");
	const [sortDir, setSortDir] = useState<SortDir>("desc");
	const [selectedModel, setSelectedModel] = useState<DualGaugeModel | null>(null);

	const handleSort = (field: SortField) => {
		if (sortField === field) {
			setSortDir(sortDir === "asc" ? "desc" : "asc");
		} else {
			setSortField(field);
			setSortDir("desc");
		}
	};

	const data = useMemo(() => {
		const filtered = allModels.filter((m) => {
			if (!showAgents && m.isAgent) return false;
			if (showOpenOnly && m.type !== "Open") return false;
			if (search && !m.model.toLowerCase().includes(search.toLowerCase())) return false;
			return true;
		});

		filtered.sort((a, b) => {
			let aVal: string | number;
			let bVal: string | number;

			if (sortField === "model" || sortField === "organization" || sortField === "type") {
				aVal = a[sortField];
				bVal = b[sortField];
			} else {
				aVal = a[language][sortField];
				bVal = b[language][sortField];
			}

			if (typeof aVal === "number" && typeof bVal === "number") {
				return sortDir === "asc" ? aVal - bVal : bVal - aVal;
			}
			const cmp = String(aVal).localeCompare(String(bVal));
			return sortDir === "asc" ? cmp : -cmp;
		});

		return filtered;
	}, [language, search, showAgents, showOpenOnly, sortField, sortDir]);

	const renderSortArrow = (field: SortField) => {
		if (sortField !== field) return null;
		return (
			<span className="ml-1" style={{ color: "var(--color-accent)" }}>
				{sortDir === "asc" ? "↑" : "↓"}
			</span>
		);
	};

	return (
		<>
			<Navbar isHomePage={false} />
			<main className="mx-auto max-w-6xl px-6 py-12">
				{/* Header */}
				<div className="mb-8">
					<p
						className="mb-2 text-xs font-semibold uppercase tracking-widest"
						style={{ color: "var(--color-accent)" }}
					>
						DualGauge-Bench
					</p>
					<h1
						className="text-3xl font-bold tracking-tight"
						style={{ color: "var(--color-text-primary)" }}
					>
						Leaderboard
					</h1>
					<p
						className="mt-2 text-sm leading-relaxed"
						style={{ color: "var(--color-text-secondary)" }}
					>
						Joint security-functionality evaluation of 10 LLMs and 3 agentic coding
						systems across 307 specification-only tasks. Click any model to view
						cross-language details.
					</p>
				</div>

				{/* Language tabs */}
				<div className="mb-6 flex items-center gap-1 rounded-lg p-1" style={{ backgroundColor: "var(--color-bg-secondary)", border: "1px solid var(--color-border)" }}>
					{LANGUAGES.map((l) => (
						<button
							key={l.key}
							onClick={() => setLanguage(l.key)}
							className="rounded-md px-4 py-2 text-sm font-medium transition-all duration-150"
							style={{
								backgroundColor: language === l.key ? "var(--color-accent-dim)" : "transparent",
								color: language === l.key ? "var(--color-accent)" : "var(--color-text-secondary)",
								border: language === l.key ? "1px solid var(--color-border-accent)" : "1px solid transparent",
							}}
						>
							{l.label}
						</button>
					))}
				</div>

				{/* Search + filters */}
				<div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
					<div className="relative flex-1">
						<div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
							<svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ color: "var(--color-text-secondary)" }}>
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
							</svg>
						</div>
						<input
							type="text"
							className="w-full rounded-lg py-2.5 pl-9 pr-4 text-sm focus:outline-none"
							placeholder="Search models..."
							value={search}
							onChange={(e) => setSearch(e.target.value)}
							style={{
								backgroundColor: "var(--color-bg-secondary)",
								color: "var(--color-text-primary)",
								border: "1px solid var(--color-border)",
							}}
						/>
					</div>

					<div className="flex items-center gap-4">
						<label className="flex cursor-pointer items-center gap-2">
							<input
								type="checkbox"
								checked={showAgents}
								onChange={() => setShowAgents(!showAgents)}
								className="h-3.5 w-3.5 rounded"
								style={{ accentColor: "var(--color-accent)" }}
							/>
							<span className="text-xs font-medium" style={{ color: "var(--color-text-secondary)" }}>
								Agents
							</span>
						</label>
						<label className="flex cursor-pointer items-center gap-2">
							<input
								type="checkbox"
								checked={showOpenOnly}
								onChange={() => setShowOpenOnly(!showOpenOnly)}
								className="h-3.5 w-3.5 rounded"
								style={{ accentColor: "var(--color-accent)" }}
							/>
							<span className="text-xs font-medium" style={{ color: "var(--color-text-secondary)" }}>
								Open Weight Only
							</span>
						</label>
					</div>
				</div>

				{/* Table */}
				<div className="card-dark overflow-hidden rounded-xl">
					<div className="overflow-x-auto">
						<table className="min-w-full">
							<thead>
								<tr style={{ borderBottom: "1px solid var(--color-border)" }}>
									<th
										className="w-12 py-3 pl-4 pr-2 text-left text-xs font-semibold uppercase tracking-wider"
										style={{ color: "var(--color-text-secondary)", backgroundColor: "var(--color-bg-secondary)" }}
									>
										#
									</th>
									{[
										{ field: "model" as SortField, label: "Model" },
										{ field: "organization" as SortField, label: "Org" },
									].map((col) => (
										<th
											key={col.field}
											className="cursor-pointer select-none px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider transition-colors"
											style={{ color: sortField === col.field ? "var(--color-accent)" : "var(--color-text-secondary)", backgroundColor: "var(--color-bg-secondary)" }}
											onClick={() => handleSort(col.field)}
										>
											{col.label}{renderSortArrow(col.field)}
										</th>
									))}
									{METRIC_COLS.map((col) => (
										<th
											key={col.key}
											className="font-mono-data cursor-pointer select-none px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider transition-colors"
											style={{ color: sortField === col.key ? "var(--color-accent)" : "var(--color-text-secondary)", backgroundColor: "var(--color-bg-secondary)" }}
											onClick={() => handleSort(col.key)}
										>
											{col.label}{renderSortArrow(col.key)}
										</th>
									))}
									<th
										className="cursor-pointer select-none px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider transition-colors"
										style={{ color: sortField === "type" ? "var(--color-accent)" : "var(--color-text-secondary)", backgroundColor: "var(--color-bg-secondary)" }}
										onClick={() => handleSort("type")}
									>
										Type{renderSortArrow("type")}
									</th>
									<th
										className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider"
										style={{ color: "var(--color-text-secondary)", backgroundColor: "var(--color-bg-secondary)" }}
									>
										Details
									</th>
								</tr>
							</thead>
							<tbody>
								{data.map((model, idx) => {
									const langData = model[language];
									return (
										<tr
											key={model.id}
											className="cursor-pointer transition-colors duration-150"
											style={{
												borderBottom: idx < data.length - 1 ? "1px solid var(--color-border)" : "none",
											}}
											onClick={() => setSelectedModel(model)}
										>
											{/* Rank */}
											<td className="py-3 pl-4 pr-2">
												<span
													className="font-mono-data inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold"
													style={{
														backgroundColor: idx < 3 ? "var(--color-accent-dim)" : "var(--color-bg-secondary)",
														color: idx < 3 ? "var(--color-accent)" : "var(--color-text-secondary)",
														border: idx < 3 ? "1px solid var(--color-border-accent)" : "1px solid var(--color-border)",
													}}
												>
													{idx + 1}
												</span>
											</td>

											{/* Model */}
											<td className="px-4 py-3">
												<span className="text-sm font-medium" style={{ color: "var(--color-text-primary)" }}>
													{model.model}
												</span>
											</td>

											{/* Org */}
											<td className="px-4 py-3">
												<span className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
													{model.organization}
												</span>
											</td>

											{/* Metric values */}
											{METRIC_COLS.map((col) => {
												const val = langData[col.key];
												return (
													<td key={col.key} className="px-4 py-3 text-right">
														<span
															className="font-mono-data inline-block rounded px-2 py-0.5 text-xs font-semibold"
															style={{
																color: scoreColor(val),
																backgroundColor: scoreBg(val),
															}}
														>
															{val}%
														</span>
													</td>
												);
											})}

											{/* Type */}
											<td className="px-4 py-3 text-center">
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
													<span
														className="h-1.5 w-1.5 rounded-full"
														style={{
															backgroundColor:
																model.type === "Open"
																	? "#34d399"
																	: model.type === "Agent"
																	? "#a855f7"
																	: "var(--color-accent)",
														}}
													/>
													{model.type}
												</span>
											</td>

											{/* Details button */}
											<td className="px-4 py-3 text-center">
												<button
													onClick={(e) => {
														e.stopPropagation();
														setSelectedModel(model);
													}}
													className="rounded-lg px-3 py-1 text-xs font-medium transition-all"
													style={{
														backgroundColor: "var(--color-accent-dim)",
														color: "var(--color-accent)",
														border: "1px solid var(--color-border-accent)",
													}}
												>
													View
												</button>
											</td>
										</tr>
									);
								})}
							</tbody>
						</table>
					</div>
				</div>

				{/* Stats bar */}
				<div className="mt-4 flex items-center justify-between">
					<span className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
						{data.length} model{data.length !== 1 ? "s" : ""} · 307 tasks · k=1
					</span>
					<span className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
						Sorted by {sortField} ({sortDir})
					</span>
				</div>

				{/* Metric legend */}
				<div
					className="mt-6 rounded-xl p-4"
					style={{ backgroundColor: "var(--color-bg-secondary)", border: "1px solid var(--color-border)" }}
				>
					<p className="mb-3 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--color-text-secondary)" }}>
						Metric Definitions
					</p>
					<div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
						{[
							{ name: "pass@1", full: "Functional Correctness", desc: "Fraction of problems where the single generated sample passes all functional tests, averaged over all benchmark problems." },
							{ name: "secure@1", full: "Security Correctness", desc: "Fraction of problems where the single generated sample passes all security tests, averaged over all benchmark problems." },
							{ name: "secure-pass@1", full: "Joint Security-Functionality", desc: "Fraction of problems where the single sample passes both all functional and all security tests simultaneously. The primary metric." },
							{ name: "PR", full: "Pass Rate (Pfunc / Tfunc)", desc: "Proportion of individual functional test cases passed across all problems — a test-case-level metric, unlike pass@1 which is problem-level." },
							{ name: "SPR", full: "Secure Pass Rate (Psec / Tsec)", desc: "Proportion of individual security test cases passed across all problems — test-case-level analogue of secure@1." },
						].map((m) => (
							<div key={m.name} className="flex gap-2">
								<code
									className="mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-xs font-bold"
									style={{ backgroundColor: "var(--color-accent-dim)", color: "var(--color-accent)" }}
								>
									{m.name}
								</code>
								<p className="text-xs leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
									<span className="font-semibold" style={{ color: "var(--color-text-primary)" }}>{m.full} — </span>
									{m.desc}
								</p>
							</div>
						))}
					</div>
				</div>
			</main>
			<Footer />

			{/* Model detail modal */}
			{selectedModel && (
				<ModelDetailModal
					model={selectedModel}
					onClose={() => setSelectedModel(null)}
				/>
			)}
		</>
	);
};

export default LeaderboardPage;
