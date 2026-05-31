import React from "react";

const Header: React.FC = () => {
	return (
		<div className="text-center py-8">
			<h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
				CodeSecurityBenchmark+
			</h1>
			<h2 className="text-xl md:text-2xl font-medium text-gray-700">
				Constrained Decoding for Secure Code Generation
			</h2>

			{/* <div className="text-gray-600 mb-6">
				<p className="text-lg mb-0">
					Haipeng Cai<sup>1</sup>, Haipeng Cai<sup>1</sup>, Haipeng Cai
					<sup>2</sup>, Haipeng Cai<sup>1</sup>
				</p>
				<p className="text-sm mt-0">
					<sup>1</sup>University at Buffalo, <sup>2</sup>Google DeepMind
				</p>
			</div> */}

			<div className="flex flex-wrap justify-center gap-6 mb-8">
			<a href="/" className="btn">
					Overview
				</a>
				<a
					href="https://arxiv.org/abs/2405.00218"
					target="_blank"
					rel="noopener noreferrer"
					className="btn"
				>
					Paper
				</a>
				<a href="/code" className="btn">
					Code
				</a>
				<a href="/leaderboard" className="btn">
					Leaderboard
				</a>
			</div>

			{/* <div className="max-w-4xl mx-auto text-left bg-gray-50 p-6 rounded-lg">
				<h3 className="text-lg font-semibold mb-4">TL; DR</h3>
				<p className="text-gray-700 leading-relaxed">
					There is a disconnection between benchmarks for Code LLMs that
					evaluate the security and those that assess correctness. Existing
					benchmarks, like HumanEval and MBPP, only evaluate the correctness,
					while others like the Copilot dataset and SecurityEval, only target
					security. To bridge this gap, we present CodeGuard+, along with two
					new metrics, to measure Code LLMs' ability to generate both secure and
					correct code. Currently, CodeGuard+ supports Python and C/C++, with 91
					prompts covering 34 CWEs.
				</p>
			</div> */}
		</div>
	);
};

export default Header;
