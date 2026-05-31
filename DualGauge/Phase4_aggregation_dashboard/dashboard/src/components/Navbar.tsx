import React from "react";

const Navbar: React.FC = () => {
	return (
		<nav className="w-full bg-white border-b border-gray-200 sticky top-0 z-50">
			<div className="container mx-auto">
				<div className="flex items-center justify-between h-16">
					{/* Logo */}
					<div className="flex items-center">
						<h1 className="text-xl font-semibold text-gray-900">CodeGuard+</h1>
					</div>

					{/* Navigation Links */}
					<div className="hidden md:flex items-center space-x-8">
						<a
							href="https://arxiv.org/abs/2405.00218"
							target="_blank"
							rel="noopener noreferrer"
							className="text-gray-700 hover:text-gray-900 transition-colors"
						>
							Paper
						</a>
						<a
							href="/leaderboard"
							className="text-gray-700 hover:text-gray-900 transition-colors"
						>
							Leaderboard
						</a>
						<a
							href="#"
							className="text-gray-700 hover:text-gray-900 transition-colors"
						>
							Code
						</a>
						<a
							href="https://arxiv.org/abs/2405.00218"
							target="_blank"
							rel="noopener noreferrer"
							className="text-gray-700 hover:text-gray-900 transition-colors"
						>
							arXiv
						</a>
					</div>

					{/* Mobile menu button */}
					<div className="md:hidden">
						<button className="text-gray-700 hover:text-gray-900">
							<svg
								className="h-6 w-6"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									strokeWidth={2}
									d="M4 6h16M4 12h16M4 18h16"
								/>
							</svg>
						</button>
					</div>
				</div>
			</div>
		</nav>
	);
};

export default Navbar;
