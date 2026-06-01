import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
	subsets: ["latin"],
	variable: "--font-inter",
	display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
	subsets: ["latin"],
	variable: "--font-jetbrains",
	display: "swap",
});

export const metadata: Metadata = {
	title: "DualGauge — Joint Security-Functionality Benchmarking",
	description:
		"Automated joint security-functionality benchmarking of specification-only code generation by LLMs and coding agents.",
	keywords: [
		"Code Security",
		"Code LLM",
		"Benchmark",
		"DualGauge",
		"Secure Code Generation",
		"CWE",
		"Coding Agents",
	],
};

export default function RootLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<html
			lang="en"
			className={`${inter.variable} ${jetbrainsMono.variable}`}
			suppressHydrationWarning
		>
			<head>
				<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
				<script
					dangerouslySetInnerHTML={{
						__html: `
							(function() {
								var theme = localStorage.getItem('theme');
								if (theme === 'light') {
									document.documentElement.classList.add('light');
								}
							})();
						`,
					}}
				/>
			</head>
			<body>{children}</body>
		</html>
	);
}
