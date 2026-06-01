"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useActiveSection } from "../hooks/useActiveSection";
import ThemeToggle from "./ThemeToggle";
import Logo from "./Logo";

const ALL_SECTIONS = ["overview", "motivation", "benchmark", "comparison", "system", "metrics", "findings"];

const PAPER_CHILDREN = ["motivation", "benchmark", "comparison"];

type NavItem =
	| { type: "link"; id: string; label: string; href: string }
	| { type: "dropdown"; id: string; label: string; children: { id: string; label: string; href: string }[] };

const HOME_NAV: NavItem[] = [
	{ type: "link", id: "overview", label: "Overview", href: "#overview" },
	{
		type: "dropdown",
		id: "paper",
		label: "Paper",
		children: [
			{ id: "motivation", label: "Motivation", href: "#motivation" },
			{ id: "benchmark", label: "Benchmark", href: "#benchmark" },
			{ id: "comparison", label: "Comparison", href: "#comparison" },
		],
	},
	{ type: "link", id: "system", label: "System", href: "#system" },
	{ type: "link", id: "metrics", label: "Metrics", href: "#metrics" },
	{ type: "link", id: "findings", label: "Findings", href: "#findings" },
];

interface NavbarProps {
	isHomePage?: boolean;
}

const Navbar: React.FC<NavbarProps> = ({ isHomePage = true }) => {
	const activeSection = useActiveSection(isHomePage ? ALL_SECTIONS : []);
	const [mobileOpen, setMobileOpen] = useState(false);
	const [dropdownOpen, setDropdownOpen] = useState(false);
	const dropdownRef = useRef<HTMLDivElement>(null);

	useEffect(() => {
		const handleClick = (e: MouseEvent) => {
			if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
				setDropdownOpen(false);
			}
		};
		document.addEventListener("mousedown", handleClick);
		return () => document.removeEventListener("mousedown", handleClick);
	}, []);

	const isDropdownActive = PAPER_CHILDREN.includes(activeSection);

	const renderLink = (id: string, label: string, href: string) => {
		const isActive = isHomePage && activeSection === id;
		return (
			<a
				key={id}
				href={href}
				className="relative px-3 py-1.5 text-xs font-medium transition-colors duration-200"
				style={{
					color: isActive ? "var(--color-accent)" : "var(--color-text-secondary)",
					textDecoration: "none",
				}}
			>
				{label}
				{isActive && (
					<span
						className="absolute bottom-0 left-3 right-3 h-px"
						style={{ backgroundColor: "var(--color-accent)" }}
					/>
				)}
			</a>
		);
	};

	return (
		<nav
			className="sticky top-0 z-50 w-full nav-blur"
			style={{ borderBottom: "1px solid var(--color-border)" }}
		>
			<div className="mx-auto flex h-14 max-w-[860px] items-center justify-between px-6">
				<Link
					href="/"
					className="flex items-center gap-2 text-sm font-semibold tracking-tight"
					style={{ color: "var(--color-text-primary)", textDecoration: "none" }}
				>
					<Logo size={22} />
					DualGauge
				</Link>

				{/* Desktop nav */}
				<div className="hidden items-center gap-1 md:flex">
					{isHomePage ? (
						<>
							{HOME_NAV.map((item) => {
								if (item.type === "link") {
									return renderLink(item.id, item.label, item.href);
								}
								return (
									<div key={item.id} className="relative" ref={dropdownRef}>
										<button
											onClick={() => setDropdownOpen(!dropdownOpen)}
											className="relative flex items-center gap-1 px-3 py-1.5 text-xs font-medium transition-colors duration-200"
											style={{
												color: isDropdownActive
													? "var(--color-accent)"
													: "var(--color-text-secondary)",
												background: "none",
												border: "none",
												cursor: "pointer",
											}}
										>
											{item.label}
											<svg
												width="10"
												height="10"
												viewBox="0 0 24 24"
												fill="none"
												stroke="currentColor"
												strokeWidth="2.5"
												style={{
													transform: dropdownOpen ? "rotate(180deg)" : "rotate(0deg)",
													transition: "transform 0.2s ease",
												}}
											>
												<polyline points="6 9 12 15 18 9" />
											</svg>
											{isDropdownActive && (
												<span
													className="absolute bottom-0 left-3 right-3 h-px"
													style={{ backgroundColor: "var(--color-accent)" }}
												/>
											)}
										</button>
										{dropdownOpen && (
											<div
												className="absolute left-0 top-full mt-1 min-w-[140px] rounded-lg py-1"
												style={{
													backgroundColor: "var(--color-bg-card)",
													border: "1px solid var(--color-border)",
													boxShadow: "0 8px 24px rgba(0, 0, 0, 0.3)",
												}}
											>
												{item.children.map((child) => {
													const isChildActive = isHomePage && activeSection === child.id;
													return (
														<a
															key={child.id}
															href={child.href}
															onClick={() => setDropdownOpen(false)}
															className="block px-4 py-2 text-xs font-medium transition-colors duration-150"
															style={{
																color: isChildActive
																	? "var(--color-accent)"
																	: "var(--color-text-secondary)",
																textDecoration: "none",
																backgroundColor: isChildActive
																	? "var(--color-accent-dim)"
																	: "transparent",
															}}
														>
															{child.label}
														</a>
													);
												})}
											</div>
										)}
									</div>
								);
							})}
						</>
					) : (
						<Link
							href="/"
							className="relative px-3 py-1.5 text-xs font-medium"
							style={{ color: "var(--color-text-secondary)", textDecoration: "none" }}
						>
							Home
						</Link>
					)}
					<div className="ml-3 pl-3" style={{ borderLeft: "1px solid var(--color-border)" }}>
						<ThemeToggle />
					</div>
				</div>

				{/* Mobile toggle */}
				<div className="flex items-center gap-2 md:hidden">
					<ThemeToggle />
					<button
						onClick={() => setMobileOpen(!mobileOpen)}
						className="flex h-8 w-8 items-center justify-center"
						style={{ color: "var(--color-text-secondary)" }}
					>
						<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
							{mobileOpen ? (
								<path d="M18 6L6 18M6 6l12 12" />
							) : (
								<path d="M4 6h16M4 12h16M4 18h16" />
							)}
						</svg>
					</button>
				</div>
			</div>

			{/* Mobile menu */}
			{mobileOpen && (
				<div
					className="border-t px-6 py-4 md:hidden"
					style={{
						backgroundColor: "var(--color-bg-secondary)",
						borderColor: "var(--color-border)",
					}}
				>
					<div className="flex flex-col gap-1">
						{isHomePage ? (
							<>
								{HOME_NAV.map((item) => {
									if (item.type === "link") {
										const isActive = activeSection === item.id;
										return (
											<a
												key={item.id}
												href={item.href}
												onClick={() => setMobileOpen(false)}
												className="rounded-lg px-3 py-2 text-sm font-medium transition-colors"
												style={{
													color: isActive ? "var(--color-accent)" : "var(--color-text-secondary)",
													textDecoration: "none",
													backgroundColor: isActive ? "var(--color-accent-dim)" : "transparent",
												}}
											>
												{item.label}
											</a>
										);
									}
									return (
										<React.Fragment key={item.id}>
											<span
												className="px-3 py-2 text-xs font-semibold uppercase tracking-wider"
												style={{ color: "var(--color-text-secondary)", opacity: 0.5 }}
											>
												{item.label}
											</span>
											{item.children.map((child) => {
												const isActive = activeSection === child.id;
												return (
													<a
														key={child.id}
														href={child.href}
														onClick={() => setMobileOpen(false)}
														className="rounded-lg px-6 py-2 text-sm font-medium transition-colors"
														style={{
															color: isActive ? "var(--color-accent)" : "var(--color-text-secondary)",
															textDecoration: "none",
															backgroundColor: isActive ? "var(--color-accent-dim)" : "transparent",
														}}
													>
														{child.label}
													</a>
												);
											})}
										</React.Fragment>
									);
								})}
							</>
						) : (
							<Link
								href="/"
								onClick={() => setMobileOpen(false)}
								className="rounded-lg px-3 py-2 text-sm font-medium"
								style={{ color: "var(--color-text-secondary)", textDecoration: "none" }}
							>
								Home
							</Link>
						)}
					</div>
				</div>
			)}
		</nav>
	);
};

export default Navbar;
