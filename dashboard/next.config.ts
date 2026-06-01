import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
