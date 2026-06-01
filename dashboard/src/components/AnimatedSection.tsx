"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface AnimatedSectionProps {
	children: React.ReactNode;
	className?: string;
	delay?: number;
}

const AnimatedSection: React.FC<AnimatedSectionProps> = ({
	children,
	className = "",
	delay = 0,
}) => {
	const [mounted, setMounted] = useState(false);
	useEffect(() => setMounted(true), []);

	if (!mounted) {
		return <div className={className}>{children}</div>;
	}

	return (
		<motion.div
			initial={{ opacity: 0, y: 24 }}
			whileInView={{ opacity: 1, y: 0 }}
			viewport={{ once: true, margin: "-60px" }}
			transition={{ duration: 0.5, delay, ease: [0.25, 0.1, 0.25, 1] }}
			className={className}
		>
			{children}
		</motion.div>
	);
};

export default AnimatedSection;
