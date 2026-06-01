import type { NextConfig } from "next";

const nextConfig: NextConfig = {
	output: "export",
	distDir: "../dist",
	basePath: "/DualGauge",
	images: { unoptimized: true },
	turbopack: {
		rules: {
			"*.css": {
				loaders: ["postcss-loader"],
			},
		},
	},
};

export default nextConfig;
