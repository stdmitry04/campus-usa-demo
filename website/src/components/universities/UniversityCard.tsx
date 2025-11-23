// add this to the existing UniversityCard component:

import { memo, useCallback, useState } from 'react';
import { University } from '@/types';
import { usePreload } from '@/hooks/usePreload';
import { BsBookmark, BsBookmarkFill, BsGlobe } from 'react-icons/bs';
import Link from "next/link";

interface UniversityCardProps {
    university: University;
    onSave: (universityId: number) => Promise<void>;
    onHover?: (universityId: number) => void;
    isSaved: boolean;
    linkToDetail?: boolean; // optional prop to make card clickable
}

const UniversityCard = memo(({
                                 university,
                                 onSave,
                                 onHover,
                                 isSaved,
                                 linkToDetail = false
                             }: UniversityCardProps) => {
    const [saving, setSaving] = useState(false);
    const { preloadUniversity } = usePreload();

    // handle save action
    const handleSave = useCallback(async () => {
        if (saving) return;
        setSaving(true);
        try {
            await onSave(university.id);
        } finally {
            setSaving(false);
        }
    }, [onSave, university.id, saving]);

    // handle hover for custom preloading and university detail preload
    const handleMouseEnter = useCallback(() => {
        onHover?.(university.id);
        // preload university detail page if linkable
        if (linkToDetail) {
            preloadUniversity(university.id);
        }
    }, [onHover, university.id, linkToDetail, preloadUniversity]);

    const handleWebsiteClick = useCallback((e: React.MouseEvent) => {
        e.stopPropagation();
        if (university.websiteUrl) {
            window.open(university.websiteUrl, '_blank', 'noopener,noreferrer');
        }
    }, [university.websiteUrl]);

    const cardContent = (
        <div
            className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
            onMouseEnter={handleMouseEnter}
        >
            {/* existing card content stays the same */}
            <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-bold text-lg text-gray-900">{university.name}</h3>
                        <span className="text-sm bg-blue-100 px-1 py-0.5 rounded text-blue-600 font-medium">
                            rank #{university.rank}
                        </span>
                        {university.hasFinancialAid && (
                            <span className="text-xs bg-green-100 px-1.5 py-0.5 rounded text-green-600 font-medium">
                                financial aid
                            </span>
                        )}
                    </div>
                    <div className="text-sm text-gray-500 flex items-center gap-2">
                        <span>{university.location}</span>
                        {university.websiteUrl && (
                            <button
                                onClick={handleWebsiteClick}
                                className="text-blue-600 hover:text-blue-700"
                            >
                                <BsGlobe className="h-3 w-3" />
                            </button>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <div className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-1 rounded">
                        {university.admissionChance} chance
                    </div>

                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className={`p-1.5 rounded transition-all duration-200 ${
                            saving
                                ? 'opacity-50 cursor-not-allowed'
                                : 'opacity-100 hover:scale-105'
                        } ${
                            isSaved
                                ? 'text-blue-600 bg-blue-50 hover:bg-blue-100'
                                : 'text-gray-400 hover:text-blue-600 hover:bg-blue-50'
                        }`}
                        title={isSaved ? `remove ${university.name} from saved` : `save ${university.name}`}
                    >
                        {saving ? (
                            <div className="h-4 w-4 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin" />
                        ) : isSaved ? (
                            <BsBookmarkFill className="h-4 w-4" />
                        ) : (
                            <BsBookmark className="h-4 w-4" />
                        )}
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-4 gap-4 text-sm">
                <div>
                    <div className="text-gray-500 mb-1">acceptance rate</div>
                    <div className="font-medium">{university.acceptanceRate}</div>
                </div>
                <div>
                    <div className="text-gray-500 mb-1">avg. sat</div>
                    <div className="font-medium">{university.avgSAT}</div>
                </div>
                <div>
                    <div className="text-gray-500 mb-1">avg. gpa</div>
                    <div className="font-medium">{university.avgGPA}</div>
                </div>
                <div>
                    <div className="text-gray-500 mb-1">tuition</div>
                    <div className="font-medium">{university.annualTuition}</div>
                </div>
            </div>
        </div>
    );

    // wrap in link if linkToDetail is true
    if (linkToDetail) {
        return (
            <Link href={`/universities/${university.id}`}>
                {cardContent}
            </Link>
        );
    }

    return cardContent;
});

UniversityCard.displayName = 'UniversityCard';
export default UniversityCard;