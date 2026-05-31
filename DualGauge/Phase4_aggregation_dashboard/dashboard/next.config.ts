import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === "production";

const nextConfig: NextConfig = {
	// Enable static export so we can deploy to GitHub Pages
	output: "export",
	// Use a relative base path for assets so pages work under /<repo>
	images: { unoptimized: true },
	experimental: {
		turbo: {
			rules: {
				"*.css": {
					loaders: ["postcss-loader"],
				},
			},
		},
	},
	// If you plan to host under a subpath like https://<user>.github.io/<repo>/,
	// set basePath in runtime via env or hardcode here. Leaving unset keeps root.
};

export default nextConfig;
