import React from "react";
import Link from "next/link";
import Logo from "./Logo";

const Footer: React.FC = () => {
	return (
		<footer
			className="py-12"
			style={{ borderTop: "1px solid var(--color-border)" }}
		>
			<div className="mx-auto max-w-[860px] px-6 text-center">
				<div className="mb-3 flex items-center justify-center gap-2">
					<Logo size={18} />
					<h3
						className="text-sm font-semibold"
						style={{ color: "var(--color-text-primary)" }}
					>
						DualGauge
					</h3>
				</div>
				<p
					className="mx-auto mb-6 max-w-md text-xs leading-relaxed"
					style={{ color: "var(--color-text-secondary)" }}
				>
					The first fully automated framework for joint
					security-functionality evaluation of specification-only code
					generation. 307 tasks across Python, C++, and JavaScript
					covering 90 CWEs.
				</p>
				<div className="flex items-center justify-center gap-4 text-xs">
					<a
						href="https://github.com/SRestLabUB/DualGauge"
						target="_blank"
						rel="noopener noreferrer"
						style={{ color: "var(--color-text-secondary)" }}
					>
						Code
					</a>
					<span style={{ color: "var(--color-border)" }}>|</span>
					<Link href="/leaderboard" style={{ color: "var(--color-text-secondary)" }}>
						Leaderboard
					</Link>
				</div>
			</div>
		</footer>
	);
};

export default Footer;
