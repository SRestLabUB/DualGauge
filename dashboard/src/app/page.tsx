"use client";

import React from "react";
import Navbar from "../components/Navbar";
import HeroSection from "../components/HeroSection";
import MotivationSection from "../components/MotivationSection";
import BenchmarkSection from "../components/BenchmarkSection";
import ComparisonSection from "../components/ComparisonSection";
import SystemSection from "../components/SystemSection";
import MetricsSection from "../components/MetricsSection";
import LeaderboardPreview from "../components/LeaderboardPreview";
import FindingsSection from "../components/FindingsSection";
import Footer from "../components/Footer";

const HomePage: React.FC = () => {
	return (
		<>
			<Navbar isHomePage={true} />
			<main className="mx-auto max-w-[860px] px-6">
				<HeroSection />
				<div style={{ borderTop: "1px solid var(--color-border)" }} />
				<MotivationSection />
				<div style={{ borderTop: "1px solid var(--color-border)" }} />
				<BenchmarkSection />
				<div style={{ borderTop: "1px solid var(--color-border)" }} />
				<ComparisonSection />
				<div style={{ borderTop: "1px solid var(--color-border)" }} />
				<SystemSection />
				<div style={{ borderTop: "1px solid var(--color-border)" }} />
				<MetricsSection />
				<div style={{ borderTop: "1px solid var(--color-border)" }} />
				<LeaderboardPreview />
				<div style={{ borderTop: "1px solid var(--color-border)" }} />
				<FindingsSection />
			</main>
			<Footer />
		</>
	);
};

export default HomePage;
