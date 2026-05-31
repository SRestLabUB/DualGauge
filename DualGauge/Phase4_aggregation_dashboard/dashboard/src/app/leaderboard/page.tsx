"use client";

import React, { useState, useMemo } from "react";
import Navbar from "../../components/Navbar";
import Header from "../../components/Header";
import LeaderboardTable from "../../components/LeaderboardTable";
import SearchSection, { FilterType } from "../../components/SearchSection";
import FilterSection, { FilterOptions } from "../../components/FilterSection";
import Footer from "../../components/Footer";
import { ModelData, SortKey, SortDirection } from "../../types/models";
import { modelRawData } from "../../data/models";
import { sortData, filterData } from "../../utils/helpers";
import { calculateMetricsForK } from "../../utils/metricsCalculator";

const LeaderboardPage: React.FC = () => {
	const [searchTerm, setSearchTerm] = useState<string>("");
	const [filterType, setFilterType] = useState<FilterType>("all");
	const [sortKey, setSortKey] = useState<SortKey | null>(null);
	const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
	const [kValue, setKValue] = useState<number>(1);
	const [filters, setFilters] = useState<FilterOptions>({
		showOrganization: true,
		showAPIName: false,
		showReasoningModels: true,
		showOpenWeightOnly: false,
	});

	// Handle sorting
	const handleSort = (key: SortKey) => {
		if (sortKey === key) {
			setSortDirection(sortDirection === "asc" ? "desc" : "asc");
		} else {
			setSortKey(key);
			setSortDirection("desc");
		}
	};

	// Handle clear filters
	const handleClearFilters = () => {
		setFilters({
			showOrganization: true,
			showAPIName: false,
			showReasoningModels: true,
			showOpenWeightOnly: false,
		});
		setSearchTerm("");
		setFilterType("all");
	};

	// Calculate metrics based on k value and convert raw data to ModelData
	const modelDataWithMetrics = useMemo(() => {
		return modelRawData.map((rawModel) => {
			const metrics = calculateMetricsForK(
				rawModel.n,
				rawModel.c,
				rawModel.s,
				rawModel.sp,
				kValue
			);

			return {
				model: rawModel.model,
				"pass@k": metrics["pass@k"],
				"secure@k_pass": metrics["secure@k_pass"],
				"secure_pass@k": metrics["secure_pass@k"],
				rank: 0, // Will be set after sorting
				type: rawModel.type,
				organization: rawModel.organization,
				apiName: rawModel.apiName,
				isReasoningModel: rawModel.isReasoningModel,
			} as ModelData;
		});
	}, [kValue]);

	// Sort by pass@k to assign ranks
	const rankedData = useMemo(() => {
		const sorted = [...modelDataWithMetrics].sort(
			(a, b) => b["pass@k"] - a["pass@k"]
		);
		return sorted.map((model, index) => ({
			...model,
			rank: index + 1,
		}));
	}, [modelDataWithMetrics]);

	// Memoized filtered and sorted data
	const processedData = useMemo(() => {
		let data = filterData(rankedData, searchTerm, filterType);

		// Apply additional filters
		if (!filters.showReasoningModels) {
			data = data.filter((model) => !model.isReasoningModel);
		}

		if (filters.showOpenWeightOnly) {
			data = data.filter((model) => model.type === "Open");
		}

		if (sortKey) {
			data = sortData(data, sortKey, sortDirection);
		}
		return data;
	}, [rankedData, searchTerm, filterType, sortKey, sortDirection, filters]);

	return (
		<>
			{/* Main Content */}
			{/* <di> */}
			<div className="container mx-auto">
				<Header />

				{/* Leaderboard Section */}
				<section className="py-8">
					<div className="text-center mb-4">
						<h2 className="text-3xl font-bold text-gray-900 mb-4">
							Leaderboard
						</h2>
					</div>

					<div className="mb-8">
						<SearchSection
							searchTerm={searchTerm}
							onSearchChange={setSearchTerm}
							filterType={filterType}
							onFilterChange={setFilterType}
						/>
					</div>

					<div className="mb-6">
						<FilterSection
							filters={filters}
							onFilterChange={setFilters}
							onClearFilters={handleClearFilters}
						/>
					</div>

					<LeaderboardTable
						data={processedData}
						sortKey={sortKey}
						sortDirection={sortDirection}
						onSort={handleSort}
						kValue={kValue}
						onKValueChange={setKValue}
						showOrganization={filters.showOrganization}
						showAPIName={filters.showAPIName}
					/>
				</section>
			</div>
			{/* </div> */}
		</>
	);
};

export default LeaderboardPage;
