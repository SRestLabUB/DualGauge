import type { NextConfig } from "next";

const nextConfig: NextConfig = {
	output: "export",
	distDir: "dist",
	basePath: process.env.GITHUB_PAGES === "true" ? "/DualGauge" : "",
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
