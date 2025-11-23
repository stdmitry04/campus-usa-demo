// src/app/(dashboard)/universities/page.tsx
'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { University } from '@/types';
import { useUniversities } from '@/hooks/useUniversities';
import { useDebounce } from '@/hooks/useDebounce';
import PageHeader from '@/components/layout/PageHeader';
import UniversityTabs from '@/components/universities/UniversityTabs';
import UniversitySearchFilters from '@/components/universities/UniversitySearchFilters';
import UniversityList from '@/components/universities/UniversityList';
import { BsExclamationTriangle } from 'react-icons/bs';

export default function UniversitiesPage() {
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState<'Browse' | 'Saved'>('Browse');
    const [sortType, setSortType] = useState<string>('ranking');
    const [savedUniversities, setSavedUniversities] = useState<University[]>([]);
    const [savedUniversityIds, setSavedUniversityIds] = useState<Set<number>>(new Set());
    const [loadingSaved, setLoadingSaved] = useState(false);

    // debounce search query to avoid too many filters
    const debouncedSearchQuery = useDebounce(searchQuery, 300);

    const {
        universities,
        loading,
        error,
        refetch,
        toggleSaveUniversity,
        getSavedUniversities,
    } = useUniversities();

    // load saved universities when needed
    const loadSavedUniversities = useCallback(async () => {
        setLoadingSaved(true);
        try {
            const saved: University[] = await getSavedUniversities();
            setSavedUniversities(saved);

            const savedIds = new Set(saved.map((uni: University) => uni.id));
            setSavedUniversityIds(savedIds);
            console.log('loaded saved university IDs:', Array.from(savedIds));
        } catch (err) {
            console.log('failed to load saved universities:', err);
        } finally {
            setLoadingSaved(false);
        }
    }, [getSavedUniversities]);

    // load saved universities on mount
    useEffect(() => {
        loadSavedUniversities();
    }, [loadSavedUniversities]);

    // memoize filtered and sorted universities - expensive operation
    const filteredUniversities = useMemo(() => {
        let filtered = universities;

        // apply search filter
        if (debouncedSearchQuery.trim()) {
            const query = debouncedSearchQuery.toLowerCase();
            filtered = filtered.filter((uni) =>
                uni.name.toLowerCase().includes(query) ||
                uni.location.toLowerCase().includes(query)
            );
        }

        // apply sorting
        switch (sortType) {
            case 'ranking':
                filtered = [...filtered].sort((a, b) => a.rank - b.rank);
                break;
            case 'top10':
                filtered = filtered.filter(uni => uni.rank <= 10);
                break;
            case 'financial_aid':
                filtered = filtered.filter(uni => uni.hasFinancialAid);
                break;
            default:
                break;
        }

        return filtered;
    }, [universities, debouncedSearchQuery, sortType]);

    // handle saving a university - use callback to prevent child re-renders
    const handleToggleSaveUniversity = useCallback(async (universityId: number) => {
        try {
            const university = universities.find(uni => uni.id === universityId) ||
                savedUniversities.find(uni => uni.id === universityId);

            if (!university) {
                console.log('university not found', universityId);
                return;
            }

            console.log('toggling save for:', universityId);
            const result = await toggleSaveUniversity(universityId);

            // update saved ids immediately for ui feedback
            setSavedUniversityIds(prev => {
                const newSet = new Set(prev);
                if (result.saved) {
                    newSet.add(universityId);
                    console.log('added to saved:', universityId);
                } else {
                    newSet.delete(universityId);
                    console.log('removed from saved:', universityId);
                }
                return newSet;
            });

            // update saved universities list
            if (result.saved) {
                setSavedUniversities(prev => {
                    const exists = prev.some(uni => uni.id === universityId);
                    return exists ? prev : [...prev, university];
                });
            } else {
                setSavedUniversities(prev => prev.filter(uni => uni.id !== universityId));
            }

        } catch (err) {
            console.log('failed to save university:', err);
        }
    }, [universities, savedUniversities, toggleSaveUniversity]);

    // handle search change
    const handleSearchChange = useCallback((query: string) => {
        setSearchQuery(query);
    }, []);

    // handle tab change
    const handleTabChange = useCallback((tab: 'Browse' | 'Saved') => {
        setActiveTab(tab);
    }, []);

    // handle sort change
    const handleSortChange = useCallback((sort: string) => {
        setSortType(sort);
    }, []);

    // handle filter click
    const handleFilterClick = useCallback(() => {
        // implement filter modal
        console.log('open filter modal');
    }, []);

    // preload university details on hover
    const handleUniversityHover = useCallback((universityId: number) => {
        // prefetch university details for faster navigation
        console.log('preloading university:', universityId);
    }, []);

    // error state
    if (error) {
        return (
            <>
                <PageHeader title="Universities" />
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
                    <BsExclamationTriangle className="h-5 w-5 text-red-500 mr-2 flex-shrink-0" />
                    <div>
                        <div className="text-red-800 font-medium">failed to load universities</div>
                        <div className="text-red-600 text-sm">{error}</div>
                        <button
                            onClick={refetch}
                            className="text-red-600 underline text-sm mt-1 hover:text-red-700"
                        >
                            try again
                        </button>
                    </div>
                </div>
            </>
        );
    }

    // determine which universities to show
    const currentUniversities = activeTab === 'Browse' ? filteredUniversities : savedUniversities;
    const isCurrentlyLoading = activeTab === 'Browse' ? loading : loadingSaved;

    // determine empty message
    const emptyMessage = activeTab === 'Browse'
        ? debouncedSearchQuery
            ? `no universities found matching "${debouncedSearchQuery}"`
            : 'no universities available'
        : 'no saved universities yet';

    return (
        <>
            <PageHeader title="Universities" />

            <UniversityTabs
                activeTab={activeTab}
                onTabChange={handleTabChange}
                browseCount={universities.length}
                savedCount={savedUniversities.length}
            />

            {activeTab === 'Browse' && (
                <UniversitySearchFilters
                    searchQuery={searchQuery}
                    onSearchChange={handleSearchChange}
                    onFilterClick={handleFilterClick}
                    onSortChange={handleSortChange}
                />
            )}

            <UniversityList
                universities={currentUniversities}
                savedUniversityIds={savedUniversityIds}
                onSave={handleToggleSaveUniversity}
                onHover={handleUniversityHover}
                loading={isCurrentlyLoading}
                emptyMessage={emptyMessage}
            />

            {currentUniversities.length > 0 && (
                <div className="flex space-x-4">
                    <button className="flex-1 bg-blue-50 text-blue-600 py-2 rounded-md border border-blue-200 hover:bg-blue-100">
                        save selected
                    </button>
                    <button className="flex-1 bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700">
                        apply now
                    </button>
                </div>
            )}
        </>
    );
}