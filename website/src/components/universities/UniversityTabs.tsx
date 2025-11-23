// src/components/universities/UniversityTabs.tsx - NEW COMPONENT
import { memo, useCallback } from 'react';

interface UniversityTabsProps {
    activeTab: 'Browse' | 'Saved';
    onTabChange: (tab: 'Browse' | 'Saved') => void;
    browseCount: number;
    savedCount: number;
}

const UniversityTabs = memo(({
                                 activeTab,
                                 onTabChange,
                                 browseCount,
                                 savedCount
                             }: UniversityTabsProps) => {
    const handleBrowseClick = useCallback(() => {
        onTabChange('Browse');
    }, [onTabChange]);

    const handleSavedClick = useCallback(() => {
        onTabChange('Saved');
    }, [onTabChange]);

    return (
        <div className="flex space-x-6 border-b border-gray-200 mb-6">
            <button
                className={`py-3 ${
                    activeTab === 'Browse'
                        ? 'text-blue-600 border-b-2 border-blue-600 font-medium'
                        : 'text-gray-500'
                }`}
                onClick={handleBrowseClick}
            >
                Browse ({browseCount})
            </button>
            <button
                className={`py-3 ${
                    activeTab === 'Saved'
                        ? 'text-blue-600 border-b-2 border-blue-600 font-medium'
                        : 'text-gray-500'
                }`}
                onClick={handleSavedClick}
            >
                Saved ({savedCount})
            </button>
        </div>
    );
});

UniversityTabs.displayName = 'UniversityTabs';
export default UniversityTabs;
