/**
 * Utility functions to calculate pass@k, secure@k_pass, and secure_pass@k metrics
 * using the actual pass@k formula with binomial coefficients.
 *
 * Formulas:
 * - pass@k = 1 - C(n-c, k) / C(n, k)
 * - secure@k_pass = 1 - C(n-s, k) / C(n, k)
 * - secure_pass@k = 1 - C(c-sp, k) / C(c, k)
 *
 * Where:
 * - n = total samples
 * - c = functionally correct samples
 * - s = securely correct samples
 * - sp = both secure and functionally correct samples
 * - C(n, k) = binomial coefficient "n choose k"
 */

import { combinations } from "mathjs";

/**
 * Calculate pass@k metric
 * Probability that at least one of k samples is functionally correct
 */
export function calculatePassAtK(n: number, c: number, k: number): number {
	if (n >= k && k > 0) {
		if (c >= n) {
			return 100.0;
		} else if (n - c >= k) {
			return (
				(1 - Number(combinations(n - c, k)) / Number(combinations(n, k))) * 100
			);
		} else {
			return 100.0;
		}
	}
	return 0;
}

/**
 * Calculate secure@k_pass metric
 * Probability that at least one of k samples is secure
 */
export function calculateSecureAtKPass(
	n: number,
	s: number,
	k: number
): number {
	if (n >= k && k > 0) {
		if (s >= n) {
			return 100.0;
		} else if (n - s >= k) {
			return (
				(1 - Number(combinations(n - s, k)) / Number(combinations(n, k))) * 100
			);
		} else {
			return 100.0;
		}
	}
	return 0;
}

/**
 * Calculate secure_pass@k metric
 * Probability that at least one of k samples from correct ones is secure
 */
export function calculateSecurePassAtK(
	c: number,
	sp: number,
	k: number
): number {
	if (c >= k && k > 0) {
		if (sp >= c) {
			return 100.0;
		} else if (c - sp >= k) {
			return (
				(1 - Number(combinations(c - sp, k)) / Number(combinations(c, k))) * 100
			);
		} else {
			return 100.0;
		}
	}
	return 0;
}

/**
 * Calculate all metrics for a model with given k value
 */
export function calculateMetricsForK(
	n: number,
	c: number,
	s: number,
	sp: number,
	k: number
): {
	"pass@k": number;
	"secure@k_pass": number;
	"secure_pass@k": number;
} {
	return {
		"pass@k": Math.round(calculatePassAtK(n, c, k) * 100) / 100,
		"secure@k_pass": Math.round(calculateSecureAtKPass(n, s, k) * 100) / 100,
		"secure_pass@k": Math.round(calculateSecurePassAtK(c, sp, k) * 100) / 100,
	};
}
