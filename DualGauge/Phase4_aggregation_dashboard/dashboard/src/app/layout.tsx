import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
	title: "CodeGuard+",
	description:
		"Constrained Decoding for Secure Code Generation - A comprehensive benchmark for evaluating Code LLMs on both security and correctness.",
	keywords: [
		"Code Security",
		"Code LLM",
		"Benchmark",
		"Secure Code Generation",
		"CWE",
		"Vulnerabilities",
	],
};

export default function RootLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<html lang="en">
			<body>{children}</body>
		</html>
	);
}
