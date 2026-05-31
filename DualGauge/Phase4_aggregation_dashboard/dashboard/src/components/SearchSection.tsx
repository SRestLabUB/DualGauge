import React from "react";

export type FilterType =
	| "all"
	| "open"
	| "proprietary"
	| "instruction"
	| "base";

interface SearchSectionProps {
	searchTerm: string;
	onSearchChange: (term: string) => void;
	filterType: FilterType;
	onFilterChange: (filter: FilterType) => void;
}

const SearchSection: React.FC<SearchSectionProps> = ({
	searchTerm,
	onSearchChange,
	filterType,
	onFilterChange,
}) => {
	return (
		<div className="flex flex-col sm:flex-row gap-4">
			{/* Search Bar */}
			<div className="flex-1 relative">
				<div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
					<svg
						className="h-5 w-5 text-gray-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							strokeLinecap="round"
							strokeLinejoin="round"
							strokeWidth={2}
							d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
						/>
					</svg>
				</div>
				<input
					type="text"
					className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 shadow-sm"
					placeholder="Search models by name..."
					value={searchTerm}
					onChange={(e) => onSearchChange(e.target.value)}
				/>
			</div>

			{/* Filter Dropdown */}
			<div className="relative">
				<select
					className="w-full sm:w-48 px-4 py-3 border border-gray-300 rounded-lg bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 cursor-pointer appearance-none pr-10 transition-all duration-200 shadow-sm"
					value={filterType}
					onChange={(e) => onFilterChange(e.target.value as FilterType)}
				>
					<option value="all">All Models</option>
					<option value="open">Open Source</option>
					<option value="proprietary">Proprietary</option>
					<option value="instruction">Instruction Tuned</option>
					<option value="base">Base Models</option>
				</select>
				<div className="absolute inset-y-0 right-0 flex items-center pointer-events-none pr-3">
					<svg
						className="h-5 w-5 text-gray-400"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							strokeLinecap="round"
							strokeLinejoin="round"
							strokeWidth={2}
							d="M19 9l-7 7-7-7"
						/>
					</svg>
				</div>
			</div>
		</div>
	);
};

export default SearchSection;
