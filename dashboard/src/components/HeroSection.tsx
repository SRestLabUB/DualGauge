"use client";

import React from "react";
import Link from "next/link";
import AnimatedSection from "./AnimatedSection";
import Logo from "./Logo";

const HeroSection: React.FC = () => {
	return (
		<section id="overview" className="pb-20 pt-20">
			<AnimatedSection>
				<div className="text-center">
					<div className="relative inline-block">
						<div
							className="absolute inset-0 -z-10 blur-3xl"
							style={{
								background:
									"radial-gradient(ellipse at center, rgba(56, 189, 248, 0.08), transparent 70%)",
								transform: "scale(2.5)",
							}}
						/>
						<div className="mb-4 flex justify-center">
								<Logo size={64} />
							</div>
							<h1
								className="text-5xl font-bold tracking-tight md:text-6xl"
								style={{ color: "var(--color-text-primary)" }}
							>
								DualGauge
							</h1>
					</div>

					<p
						className="mx-auto mt-6 max-w-xl text-lg leading-relaxed"
						style={{ color: "var(--color-text-secondary)" }}
					>
						Automated Joint Security-Functionality Benchmarking of
						Specification-Only Code Generation by LLMs and Coding Agents
					</p>

					<div className="mt-10 flex flex-wrap items-center justify-center gap-3">
						<a
							href="https://arxiv.org/pdf/2511.20709"
							target="_blank"
							rel="noopener noreferrer"
							className="inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition-all duration-200"
							style={{
								backgroundColor: "var(--color-accent-dim)",
								color: "var(--color-accent)",
								border: "1px solid var(--color-border-accent)",
							}}
						>
							<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
								<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
								<polyline points="14 2 14 8 20 8" />
								<line x1="16" y1="13" x2="8" y2="13" />
								<line x1="16" y1="17" x2="8" y2="17" />
								<polyline points="10 9 9 9 8 9" />
							</svg>
							Paper
						</a>
						<a
							href="https://github.com/SRestLabUB/DualGauge"
							target="_blank"
							rel="noopener noreferrer"
							className="inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition-all duration-200"
							style={{
								backgroundColor: "var(--color-accent-dim)",
								color: "var(--color-accent)",
								border: "1px solid var(--color-border-accent)",
							}}
						>
							<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
								<path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 00-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0020 4.77 5.07 5.07 0 0019.91 1S18.73.65 16 2.48a13.38 13.38 0 00-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 005 4.77a5.44 5.44 0 00-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 009 18.13V22" />
							</svg>
							Code
						</a>
						<a
							href="https://doi.org/10.5281/zenodo.20480617"
							target="_blank"
							rel="noopener noreferrer"
							className="inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition-all duration-200"
							style={{
								backgroundColor: "var(--color-accent-dim)",
								color: "var(--color-accent)",
								border: "1px solid var(--color-border-accent)",
							}}
						>
							<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
								<ellipse cx="12" cy="5" rx="9" ry="3" />
								<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
								<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
							</svg>
							Data
						</a>
						<a
							href="https://github.com/SRestLabUB/DualGauge/issues"
							target="_blank"
							rel="noopener noreferrer"
							className="inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition-all duration-200"
							style={{
								backgroundColor: "transparent",
								color: "var(--color-text-secondary)",
								border: "1px solid var(--color-border)",
							}}
						>
							<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
								<circle cx="12" cy="12" r="10" />
								<path d="M8 15h8M9 9h.01M15 9h.01" />
							</svg>
							Issues / Suggestions
						</a>
						<Link
							href="/leaderboard"
							className="inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition-all duration-200"
							style={{
								backgroundColor: "transparent",
								color: "var(--color-text-secondary)",
								border: "1px solid var(--color-border)",
							}}
						>
							<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
								<line x1="18" y1="20" x2="18" y2="10" />
								<line x1="12" y1="20" x2="12" y2="4" />
								<line x1="6" y1="20" x2="6" y2="14" />
							</svg>
							Leaderboard
						</Link>
					</div>
				</div>
			</AnimatedSection>

			{/* Abstract / TL;DR */}
			<AnimatedSection delay={0.15}>
				<div
					className="mx-auto mt-16 max-w-2xl rounded-xl p-6"
					style={{
						backgroundColor: "var(--color-bg-card)",
						border: "1px solid var(--color-border)",
					}}
				>
					<h3
						className="mb-3 text-xs font-semibold uppercase tracking-widest"
						style={{ color: "var(--color-accent)" }}
					>
						TL;DR
					</h3>
					<p
						className="text-sm leading-relaxed"
						style={{ color: "var(--color-text-secondary)" }}
					>
						LLMs and coding agents generate code from natural-language specs,
						but ensuring it is both correct <em>and</em> secure remains unsolved.
						We present <strong style={{ color: "var(--color-text-primary)" }}>DualGauge</strong>,
						the first fully automated framework for joint evaluation, and{" "}
						<strong style={{ color: "var(--color-text-primary)" }}>DualGauge-Bench</strong>,
						a language-agnostic benchmark of 307 tasks with paired functional and
						security tests. Even the strongest model stays below{" "}
						<span className="font-mono-data font-semibold" style={{ color: "#f87171" }}>
							15% secure-pass@1
						</span>{" "}
						in every language. Common scaling levers — model size, extended thinking,
						code specialization — do not reliably close the gap. Agentic systems
						(Codex, OpenHands, Claude Code) provide no advantage over direct
						generation on specification-only tasks.
					</p>
				</div>
			</AnimatedSection>
		</section>
	);
};

export default HeroSection;
