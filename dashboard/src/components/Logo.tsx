import React from "react";

interface LogoProps {
	size?: number;
	className?: string;
}

const Logo: React.FC<LogoProps> = ({ size = 24, className = "" }) => {
	return (
		<svg
			xmlns="http://www.w3.org/2000/svg"
			viewBox="0 0 100 90"
			width={size}
			height={size * 0.9}
			className={className}
		>
			<defs>
				<linearGradient id="lgLeft" x1="0%" y1="0%" x2="0%" y2="100%">
					<stop offset="0%" stopColor="#fca5a5" />
					<stop offset="100%" stopColor="#dc2626" />
				</linearGradient>
				<linearGradient id="lgRight" x1="0%" y1="0%" x2="0%" y2="100%">
					<stop offset="0%" stopColor="#6ee7b7" />
					<stop offset="100%" stopColor="#059669" />
				</linearGradient>
				<linearGradient id="lgBracketL" x1="0%" y1="0%" x2="0%" y2="100%">
					<stop offset="0%" stopColor="#fecaca" />
					<stop offset="100%" stopColor="#f87171" />
				</linearGradient>
				<linearGradient id="lgBracketR" x1="0%" y1="0%" x2="0%" y2="100%">
					<stop offset="0%" stopColor="#a7f3d0" />
					<stop offset="100%" stopColor="#34d399" />
				</linearGradient>
			</defs>
			<path d="M 50 12 L 22 26 L 22 64 L 50 78" fill="none" stroke="url(#lgLeft)" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
			<path d="M 50 12 L 78 26 L 78 64 L 50 78" fill="none" stroke="url(#lgRight)" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
			<line x1="50" y1="12" x2="50" y2="78" stroke="#1e293b" strokeWidth="0.75" />
			<polyline points="44,39 36,45 44,51" fill="none" stroke="url(#lgBracketL)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
			<polyline points="56,39 64,45 56,51" fill="none" stroke="url(#lgBracketR)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
		</svg>
	);
};

export default Logo;
