import React from "react";

export interface FilterOptions {
	showOrganization: boolean;
	showAPIName: boolean;
	showReasoningModels: boolean;
	showOpenWeightOnly: boolean;
}

interface FilterSectionProps {
	filters: FilterOptions;
	onFilterChange: (filters: FilterOptions) => void;
	onClearFilters: () => void;
}

const FilterSection: React.FC<FilterSectionProps> = ({
	filters,
	onFilterChange,
	onClearFilters,
}) => {
	const handleCheckboxChange = (key: keyof FilterOptions) => {
		onFilterChange({
			...filters,
			[key]: !filters[key],
		});
	};

	return (
		<div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
			<div className="flex items-center gap-6 flex-wrap">
				{/* Show Organization */}
				<label className="flex items-center gap-2 cursor-pointer">
					<input
						type="checkbox"
						checked={filters.showOrganization}
						onChange={() => handleCheckboxChange("showOrganization")}
						className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
					/>
					<span className="text-sm font-medium text-gray-700">
						Show Organization
					</span>
				</label>

				{/* Show API Name */}
				<label className="flex items-center gap-2 cursor-pointer">
					<input
						type="checkbox"
						checked={filters.showAPIName}
						onChange={() => handleCheckboxChange("showAPIName")}
						className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
					/>
					<span className="text-sm font-medium text-gray-700">
						Show API Name
					</span>
				</label>

				{/* Show Reasoning Models */}
				<label className="flex items-center gap-2 cursor-pointer">
					<input
						type="checkbox"
						checked={filters.showReasoningModels}
						onChange={() => handleCheckboxChange("showReasoningModels")}
						className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
					/>
					<span className="text-sm font-medium text-gray-700">
						Show Reasoning Models
					</span>
				</label>

				{/* Show Open Weight Models Only */}
				<label className="flex items-center gap-2 cursor-pointer">
					<input
						type="checkbox"
						checked={filters.showOpenWeightOnly}
						onChange={() => handleCheckboxChange("showOpenWeightOnly")}
						className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
					/>
					<span className="text-sm font-medium text-gray-700">
						Show Open Weight Models Only
					</span>
				</label>

				{/* Clear Filters Button */}
				<button
					onClick={onClearFilters}
					className="ml-auto px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-150 shadow-sm"
				>
					Clear Filters
				</button>
			</div>
		</div>
	);
};

export default FilterSection;
