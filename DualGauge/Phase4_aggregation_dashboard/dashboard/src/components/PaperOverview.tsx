import React from "react";

const PaperOverview: React.FC = () => {
	return (
		<section className="py-16">
			<div className="container mx-auto">
				<h2 className="text-3xl font-bold text-gray-900 mb-8">New Metrics</h2>

				<div className="prose prose-lg max-w-none">
					<p className="text-gray-700 leading-relaxed mb-6">
						Previous works calculate the security rate as the percentage of
						secure programs within unique generated programs that can be parsed
						and compiled. This does not measure correctness and forgives
						generated code that is functionally wrong. This is disconnected from
						the standard pass@k metric widely used in the literature for
						comparing performance of Code LLMs, which defines the expected
						likelihood of generating any correct code output within k code
						outputs.
					</p>

					<p className="text-gray-700 leading-relaxed mb-6">
						Thus, we propose two new evaluation metrics:{" "}
						<strong>secure@k_pass</strong> and <strong>secure-pass@k</strong>.
						When k = 1, secure@1_pass measures the likelihood of any generated
						correct code being secure; secure-pass@1 measures the expected
						likelihood of generating both secure and semantically correct code
						given a single generation.
					</p>
				</div>

				<div className="mt-12 bg-gray-50 rounded-lg p-8">
					<h3 className="text-xl font-semibold text-gray-900 mb-4">
						Key Insights
					</h3>
					<ul className="space-y-3 text-gray-700">
						<li className="flex items-start">
							<span className="text-blue-600 mr-2">•</span>
							Our metric secure-pass@1 is more realistic than traditional
							Security Rate metrics
						</li>
						<li className="flex items-start">
							<span className="text-blue-600 mr-2">•</span>
							We evaluate both security and correctness of generated code
						</li>
						<li className="flex items-start">
							<span className="text-blue-600 mr-2">•</span>
							Traditional Security Rate severely overestimates how secure a
							model really is
						</li>
					</ul>
				</div>
			</div>
		</section>
	);
};

export default PaperOverview;

