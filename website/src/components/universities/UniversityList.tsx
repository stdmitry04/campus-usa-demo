// src/components/universities/UniversityList.tsx
import { memo, useCallback } from 'react';
import { University } from '@/types';
import UniversityCard from './UniversityCard';

interface UniversityListProps {
    universities: University[];
    savedUniversityIds: Set<number>;
    onSave: (universityId: number) => Promise<void>;
    onHover?: (universityId: number) => void;
    loading?: boolean;
    emptyMessage?: string;
    onSelectMultiple?: (universityIds: number[]) => void;
}

const UniversityList = memo(({
                                 universities,
                                 savedUniversityIds,
                                 onSave,
                                 onHover,
                                 loading = false,
                                 emptyMessage = 'no universities found',
                                 onSelectMultiple
                             }: UniversityListProps) => {

    // show loading state
    if (loading) {
        return (
            <div className="flex justify-center items-center h-32">
                <div className="text-gray-500">loading...</div>
            </div>
        );
    }

    // show empty state
    if (universities.length === 0) {
        return (
            <div className="text-center py-8">
                <div className="text-gray-500 mb-2">{emptyMessage}</div>
            </div>
        );
    }

    // render universities list
    return (
        <div className="space-y-4 mb-6">
            {universities.map((university) => (
                <UniversityCard
                    key={university.id}
                    university={university}
                    onSave={onSave}
                    onHover={onHover}
                    isSaved={savedUniversityIds.has(university.id)}
                />
            ))}
        </div>
    );
});

// set display name for debugging
UniversityList.displayName = 'UniversityList';

export default UniversityList;