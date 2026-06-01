"use client";

import React from "react";
import AnimatedSection from "./AnimatedSection";

const MotivationSection: React.FC = () => {
	return (
		<section id="motivation" className="py-24">
			<AnimatedSection>
				<p
					className="mb-2 text-xs font-semibold uppercase tracking-widest"
					style={{ color: "var(--color-accent)" }}
				>
					Motivation
				</p>
				<h2
					className="mb-6 text-2xl font-bold"
					style={{ color: "var(--color-text-primary)" }}
				>
					Why Joint Evaluation?
				</h2>
				<p
					className="mb-6 max-w-2xl leading-relaxed"
					style={{ color: "var(--color-text-secondary)" }}
				>
					Existing evaluations measure correctness and security in isolation.
					Functional benchmarks like HumanEval and MBPP emphasize passing
					unit tests. Security benchmarks focus on vulnerability detection
					without checking whether the code actually works. This separation
					is misleading: a program that avoids a vulnerability but violates
					the specification is not useful, while a correct program that leaks
					data is unsafe.
				</p>
			</AnimatedSection>

			<AnimatedSection delay={0.1}>
				<div className="grid gap-3 md:grid-cols-2">
					<div className="card-dark rounded-xl p-5">
						<h3
							className="mb-3 text-sm font-semibold"
							style={{ color: "var(--color-text-primary)" }}
						>
							The Oracle Problem
						</h3>
						<p
							className="text-sm leading-relaxed"
							style={{ color: "var(--color-text-secondary)" }}
						>
							A secure and a vulnerable implementation can return identical
							outputs with identical exit codes on adversarial inputs. The
							difference only surfaces in the <em>execution trace</em> — whether
							the code opened a file before failing, or rejected the malicious
							path before any access. Output matching alone is structurally
							blind to this.
						</p>
					</div>
					<div className="card-dark rounded-xl p-5">
						<h3
							className="mb-3 text-sm font-semibold"
							style={{ color: "var(--color-text-primary)" }}
						>
							The Specification Gap
						</h3>
						<p
							className="text-sm leading-relaxed"
							style={{ color: "var(--color-text-secondary)" }}
						>
							Most benchmarks are tied to code-completion or
							framework-specific settings. Specification-only generation —
							implementing from a natural-language description alone — is how
							developers commonly use LLMs in early design phases, and it
							exposes risks that contextualized settings may obscure.
						</p>
					</div>
				</div>
			</AnimatedSection>

			{/* Motivating example */}
			<AnimatedSection delay={0.15}>
				<div
					className="mt-6 rounded-xl p-5"
					style={{
						backgroundColor: "var(--color-bg-card)",
						border: "1px solid var(--color-border)",
					}}
				>
					<h3
						className="mb-4 text-sm font-semibold"
						style={{ color: "var(--color-text-primary)" }}
					>
						Motivating Example
					</h3>
					<p
						className="mb-4 text-sm leading-relaxed"
						style={{ color: "var(--color-text-secondary)" }}
					>
						Two implementations of{" "}
						<code className="font-mono-data text-xs" style={{ color: "var(--color-accent)" }}>
							load_file(path)
						</code>{" "}
						both pass functional tests and both return{" "}
						<code className="font-mono-data text-xs" style={{ color: "var(--color-text-primary)" }}>
							None
						</code>{" "}
						on a path-traversal attack:
					</p>
					<div className="grid gap-3 md:grid-cols-2">
						<div
							className="rounded-lg p-4"
							style={{
								backgroundColor: "var(--color-bg-secondary)",
								border: "1px solid rgba(248, 113, 113, 0.15)",
							}}
						>
							<div className="mb-2 flex items-center gap-2">
								<span
									className="inline-block rounded-full px-2 py-0.5 text-xs font-semibold"
									style={{
										backgroundColor: "rgba(248, 113, 113, 0.1)",
										color: "#f87171",
									}}
								>
									Vulnerable
								</span>
							</div>
							<pre
								className="font-mono-data overflow-x-auto text-xs leading-relaxed"
								style={{ color: "var(--color-text-secondary)" }}
							>
{`full_path = os.path.join(
    "./test_dir", path)
with open(full_path, "r") as f:
    return f.read()
# File access BEFORE check
# Returns None only because
# open() failed`}
							</pre>
						</div>
						<div
							className="rounded-lg p-4"
							style={{
								backgroundColor: "var(--color-bg-secondary)",
								border: "1px solid rgba(52, 211, 153, 0.15)",
							}}
						>
							<div className="mb-2 flex items-center gap-2">
								<span
									className="inline-block rounded-full px-2 py-0.5 text-xs font-semibold"
									style={{
										backgroundColor: "rgba(52, 211, 153, 0.1)",
										color: "#34d399",
									}}
								>
									Secure
								</span>
							</div>
							<pre
								className="font-mono-data overflow-x-auto text-xs leading-relaxed"
								style={{ color: "var(--color-text-secondary)" }}
							>
{`base = os.path.realpath("./test_dir")
full = os.path.realpath(
    os.path.join(base, path))
if not full.startswith(base + os.sep):
    return None  # Reject path
# No file access attempted`}
							</pre>
						</div>
					</div>
					<p
						className="mt-4 text-xs leading-relaxed"
						style={{ color: "var(--color-text-secondary)", opacity: 0.7 }}
					>
						Both return None with exit code 0. Only the execution trace reveals the
						difference — semantic judgment over runtime behavior is necessary.
					</p>
				</div>
			</AnimatedSection>
		</section>
	);
};

export default MotivationSection;
