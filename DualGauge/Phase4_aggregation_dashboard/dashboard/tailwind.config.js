/** @type {import('tailwindcss').Config} */
module.exports = {
	content: [
		"./src/app/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/components/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/types/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/utils/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/data/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/**/*.{js,ts,jsx,tsx,mdx}",
	],
	theme: {
		extend: {
			fontFamily: {
				sans: [
					"-apple-system",
					"BlinkMacSystemFont",
					"Segoe UI",
					"Roboto",
					"Oxygen",
					"Ubuntu",
					"Cantarell",
					"sans-serif",
				],
				serif: ["Georgia", "Times New Roman", "serif"],
				mono: ["JetBrains Mono", "Fira Code", "monospace"],
			},
		},
	},
	plugins: [],
};
