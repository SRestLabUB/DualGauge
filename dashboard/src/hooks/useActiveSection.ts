"use client";

import { useState, useEffect } from "react";

export function useActiveSection(sectionIds: string[]): string {
	const [active, setActive] = useState(sectionIds[0] || "");

	useEffect(() => {
		const observer = new IntersectionObserver(
			(entries) => {
				for (const entry of entries) {
					if (entry.isIntersecting) {
						setActive(entry.target.id);
					}
				}
			},
			{ rootMargin: "-20% 0px -75% 0px" }
		);

		for (const id of sectionIds) {
			const el = document.getElementById(id);
			if (el) observer.observe(el);
		}

		return () => observer.disconnect();
	}, [sectionIds]);

	return active;
}
