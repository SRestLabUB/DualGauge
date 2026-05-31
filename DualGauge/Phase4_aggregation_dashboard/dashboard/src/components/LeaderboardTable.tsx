import React from "react";
import { FiArrowUp, FiArrowDown } from "react-icons/fi";
import { ModelData, SortKey, SortDirection } from "../types/models";
import { getScoreClass } from "../utils/helpers";

interface LeaderboardTableProps {
	data: ModelData[];
	sortKey: SortKey | null;
	sortDirection: SortDirection;
	onSort: (key: SortKey) => void;
	kValue?: number;
	onKValueChange?: (k: number) => void;
	showOrganization?: boolean;
	showAPIName?: boolean;
}

const LeaderboardTable: React.FC<LeaderboardTableProps> = ({
	data,
	sortKey,
	sortDirection,
	onSort,
	kValue = 1,
	onKValueChange,
	showOrganization = true,
	showAPIName = false,
}) => {
	const renderSortIcon = (columnKey: SortKey) => {
		if (sortKey !== columnKey) return null;

		return sortDirection === "asc" ? (
			<FiArrowUp className="inline ml-2 h-4 w-4 text-gray-500" />
		) : (
			<FiArrowDown className="inline ml-2 h-4 w-4 text-gray-500" />
		);
	};

	const columnHeaders = React.useMemo(() => {
		const headers: Array<{ key: SortKey; label: string }> = [
			{ key: "rank" as SortKey, label: "Rank" },
			{ key: "model" as SortKey, label: "Model" },
		];

		if (showOrganization) {
			headers.push({ key: "organization" as SortKey, label: "Organization" });
		}

		if (showAPIName) {
			headers.push({ key: "apiName" as SortKey, label: "API Name" });
		}

		headers.push(
			{ key: "pass@k" as SortKey, label: `PASS@${kValue}` },
			{ key: "secure@k_pass" as SortKey, label: `SECURE@${kValue}_PASS` },
			{ key: "secure_pass@k" as SortKey, label: `SECURE_PASS@${kValue}` },
			{ key: "type" as SortKey, label: "Type" }
		);

		return headers;
	}, [kValue, showOrganization, showAPIName]);

	if (data.length === 0) {
		return (
			<div className="bg-white border border-gray-200 rounded-lg shadow-sm p-16 text-center">
				<div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gray-100 flex items-center justify-center">
					<svg
						className="w-10 h-10 text-gray-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							strokeLinecap="round"
							strokeLinejoin="round"
							strokeWidth={1.5}
							d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
						/>
					</svg>
				</div>
				<h3 className="text-xl font-semibold text-gray-900 mb-3">
					No Models Found
				</h3>
				<p className="text-gray-600 max-w-md mx-auto">
					No models match your search criteria. Try adjusting your search or
					filter settings.
				</p>
			</div>
		);
	}

	const handleKValueChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
		const newK = parseInt(e.target.value, 10);
		if (onKValueChange && !isNaN(newK) && newK > 0) {
			onKValueChange(newK);
		}
	};

	const handleCustomKInput = (e: React.ChangeEvent<HTMLInputElement>) => {
		const newK = parseInt(e.target.value, 10);
		if (onKValueChange && !isNaN(newK) && newK > 0) {
			onKValueChange(newK);
		}
	};

	return (
		<div>
			{/* K Value Selector */}
			<div
				className="bg-white border border-gray-200 rounded-lg shadow-sm p-4"
				style={{ marginBottom: "2rem" }}
			>
				<div className="flex items-center gap-4 flex-wrap">
					<label
						htmlFor="k-value"
						className="text-sm font-semibold text-gray-700"
					>
						Select K Value:
					</label>
					<select
						id="k-value"
						value={kValue}
						onChange={handleKValueChange}
						className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-150"
					>
						<option value={1}>k = 1</option>
						<option value={20}>k = 20</option>
						<option value={50}>k = 50</option>
						<option value={100}>k = 100</option>
					</select>

					<div className="flex items-center gap-2">
						<span className="text-sm text-gray-600">or</span>
						<label
							htmlFor="k-custom"
							className="text-sm font-semibold text-gray-700"
						>
							Custom K:
						</label>
						<input
							id="k-custom"
							type="number"
							// min="1"
							value={kValue}
							onChange={handleCustomKInput}
							placeholder="Enter k"
							className="w-24 px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-150"
						/>
					</div>

					<span className="text-xs text-gray-500 ml-auto">
						Showing metrics calculated with k={kValue}
					</span>
				</div>
			</div>

			{/* Leaderboard Table */}
			<div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
				<div className="overflow-x-auto">
					<table className="min-w-full">
						{/* Table Header */}
						<thead className="bg-gray-100 border-b border-gray-200">
							<tr>
								{columnHeaders.map(({ key, label }) => (
									<th
										key={key}
										className="px-5 py-3 text-left text-[16px] font-bold text-gray-800 uppercase tracking-wide cursor-pointer hover:bg-gray-200/50 transition-colors duration-150 select-none"
										onClick={() => onSort(key)}
									>
										<div className="flex items-center">
											<span className="font-semibold">{label}</span>
											{renderSortIcon(key)}
										</div>
									</th>
								))}
							</tr>
						</thead>

						{/* Table Body */}
						<tbody className="divide-y divide-gray-100">
							{data.map((model, index) => (
								<tr
									key={`${model.model}-${index}`}
									className="hover:bg-gray-50 transition-colors duration-150"
								>
									{/* Rank Column */}
									<td className="px-6 py-5 whitespace-nowrap">
										<div className="flex items-center">
											<div
												className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
													model.rank <= 3
														? "bg-gradient-to-br from-yellow-400 to-yellow-600 text-white shadow-lg"
														: model.rank <= 10
														? "bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-md"
														: "bg-gray-100 text-gray-700"
												}`}
											>
												{model.rank <= 3 ? (
													<span className="text-lg">🏆</span>
												) : (
													model.rank
												)}
											</div>
										</div>
									</td>

									{/* Model Column */}
									<td className="px-6 py-5 whitespace-nowrap">
										<div className="flex items-center">
											<div className="flex-shrink-0 w-8 h-8">
												<div className="w-8 h-8 rounded-md bg-gray-100 flex items-center justify-center border border-gray-200">
													<span className="text-gray-700 font-semibold text-xs">
														{model.model.charAt(0).toUpperCase()}
													</span>
												</div>
											</div>
											<div className="ml-3">
												<div className="text-sm font-semibold text-gray-900">
													{model.model}
												</div>
											</div>
										</div>
									</td>

									{/* Organization Column */}
									{showOrganization && (
										<td className="px-6 py-4 whitespace-nowrap">
											<div className="text-sm text-gray-900 font-medium">
												{model.organization || "N/A"}
											</div>
										</td>
									)}

									{/* API Name Column */}
									{showAPIName && (
										<td className="px-6 py-4 whitespace-nowrap">
											<div className="text-sm text-gray-600 font-mono">
												{model.apiName || "N/A"}
											</div>
										</td>
									)}

									{/* PASS@K Column */}
									<td className="px-6 py-4 whitespace-nowrap">
										<div className="flex items-center">
											<div
												className={`text-sm font-semibold px-3 py-2 rounded-lg ${getScoreClass(
													model["pass@k"]
												)} border`}
											>
												{model["pass@k"]}%
											</div>
										</div>
									</td>

									{/* SECURE@K_PASS Column */}
									<td className="px-6 py-4 whitespace-nowrap">
										<div className="flex items-center">
											<div
												className={`text-sm font-semibold px-3 py-2 rounded-lg ${getScoreClass(
													model["secure@k_pass"]
												)} border`}
											>
												{model["secure@k_pass"]}%
											</div>
										</div>
									</td>

									{/* SECURE_PASS@K Column */}
									<td className="px-6 py-4 whitespace-nowrap">
										<div className="flex items-center">
											<div
												className={`text-sm font-semibold px-3 py-2 rounded-lg ${getScoreClass(
													model["secure_pass@k"]
												)} border`}
											>
												{model["secure_pass@k"]}%
											</div>
										</div>
									</td>

									{/* Type Column */}
									<td className="px-6 py-4 whitespace-nowrap">
										<span
											className={`inline-flex items-center px-3 py-1.5 text-xs font-semibold rounded-full border ${
												model.type === "Open"
													? "bg-green-50 text-green-700 border-green-200"
													: "bg-blue-50 text-blue-700 border-blue-200"
											}`}
										>
											<div
												className={`w-2 h-2 rounded-full mr-2 ${
													model.type === "Open" ? "bg-green-500" : "bg-blue-500"
												}`}
											></div>
											{model.type}
										</span>
									</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	);
};

export default LeaderboardTable;
