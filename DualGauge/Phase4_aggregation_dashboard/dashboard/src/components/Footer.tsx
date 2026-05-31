import React from "react";

const Footer: React.FC = () => {
	return (
		<footer className="bg-gray-50 border-t border-gray-200 py-12">
			<div className="container mx-auto">
				<div className="grid md:grid-cols-3 gap-8">
					<div>
						<h3 className="text-lg font-semibold text-gray-900 mb-4">
							CodeGuard+
						</h3>
						<p className="text-gray-600 text-sm leading-relaxed">
							A comprehensive benchmark for evaluating Code LLMs on both
							security and correctness. Supporting Python and C/C++ with 91
							prompts covering 34 CWEs.
						</p>
					</div>

					<div>
						<h3 className="text-lg font-semibold text-gray-900 mb-4">
							Resources
						</h3>
						<ul className="space-y-2 text-sm">
							<li>
								<a
									href="https://arxiv.org/abs/2405.00218"
									className="text-gray-600 hover:text-gray-900 transition-colors"
								>
									Paper (arXiv)
								</a>
							</li>
							<li>
								<a
									href="#code"
									className="text-gray-600 hover:text-gray-900 transition-colors"
								>
									Code Repository
								</a>
							</li>
							<li>
								<a
									href="#leaderboard"
									className="text-gray-600 hover:text-gray-900 transition-colors"
								>
									Leaderboard
								</a>
							</li>
						</ul>
					</div>

					<div>
						<h3 className="text-lg font-semibold text-gray-900 mb-4">
							Contact
						</h3>
						<p className="text-gray-600 text-sm">
							Please reach out to{" "}
							<a
								href="mailto:yanjunfu@umd.edu"
								className="text-blue-600 hover:text-blue-800"
							>
								Yanjun Fu
							</a>{" "}
							for questions or feedback.
						</p>
					</div>
				</div>

				<div className="mt-8 pt-8 border-t border-gray-200 text-center">
					<p className="text-gray-500 text-sm">
						Code for this website was based on Nerfies and LiveCodeBench. This
						website is licensed under a Creative Commons Attribution-ShareAlike
						4.0 International License.
					</p>
				</div>
			</div>
		</footer>
	);
};

export default Footer;
