"use client";

import React from "react";
import Navbar from "../components/Navbar";
import Header from "../components/Header";
import PaperOverview from "../components/PaperOverview";
import ConstrainedDecodingSection from "../components/ConstrainedDecodingSection";
import Footer from "../components/Footer";

const HomePage: React.FC = () => {
	return (
		<>
			{/* <Navbar /> */}

			{/* Main Content */}
			<div className="min-h-screen bg-white">
				<div className="container mx-auto">
					<Header />

					{/* Metrics Section */}
					<PaperOverview />

					{/* Constrained Decoding Section */}
					<ConstrainedDecodingSection />
				</div>

				{/* <Footer /> */}
			</div>
		</>
	);
};

export default HomePage;
