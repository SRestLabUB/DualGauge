import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === "production";

const nextConfig: NextConfig = {
	output: "export",
	distDir: "dist",
	basePath: isProd ? "/DualGauge" : "",
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
