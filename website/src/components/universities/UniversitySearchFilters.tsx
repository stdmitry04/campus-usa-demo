import { memo, useCallback } from 'react';
import { BsSearch, BsFilter, BsSortDown } from 'react-icons/bs';

interface UniversitySearchFiltersProps {
    searchQuery: string;
    onSearchChange: (query: string) => void;
    onFilterClick: () => void;
    onSortChange: (sortType: string) => void;
}

const UniversitySearchFilters = memo(({
                                          searchQuery,
                                          onSearchChange,
                                          onFilterClick,
                                          onSortChange
                                      }: UniversitySearchFiltersProps) => {

    const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        onSearchChange(e.target.value);
    }, [onSearchChange]);

    const handleRankingSort = useCallback(() => {
        onSortChange('ranking');
    }, [onSortChange]);

    const handleTop10Click = useCallback(() => {
        onSortChange('top10');
    }, [onSortChange]);

    const handleFinancialAidClick = useCallback(() => {
        onSortChange('financial_aid');
    }, [onSortChange]);

    return (
        <div className="mb-6">
            <div className="flex mb-4">
                <div className="relative flex-1">
                    <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-400">
                        <BsSearch />
                    </div>
                    <input
                        type="text"
                        placeholder="search universities..."
                        className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={searchQuery}
                        onChange={handleSearchChange}
                    />
                </div>
                <button
                    className="flex items-center bg-blue-50 text-blue-600 px-4 border border-l-0 border-gray-300 rounded-r-md hover:bg-blue-100"
                    onClick={onFilterClick}
                >
                    <BsFilter className="mr-2" />
                    filter
                </button>
            </div>

            <div className="flex space-x-2 mb-4 overflow-x-auto py-1">
                <button
                    className="inline-flex items-center bg-gray-100 px-3 py-1.5 rounded text-sm whitespace-nowrap"
                    onClick={handleRankingSort}
                >
                    <BsSortDown className="mr-2" />
                    sort by ranking
                </button>
                <button
                    className="bg-gray-100 px-3 py-1.5 rounded text-sm whitespace-nowrap"
                    onClick={handleTop10Click}
                >
                    top 10 ranked
                </button>
                <button
                    className="bg-gray-100 px-3 py-1.5 rounded text-sm whitespace-nowrap"
                    onClick={handleFinancialAidClick}
                >
                    has financial aid
                </button>
            </div>
        </div>
    );
});

export default UniversitySearchFilters;