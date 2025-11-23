// src/components/dashboard/ApplicationChecklist.tsx
import { memo, useState } from 'react';
import Link from 'next/link';
import { ChecklistItem, ChecklistSection} from "@/types";
import {
    BsCheckCircleFill,
    BsCircle,
    BsChevronDown,
    BsChevronRight,
    BsArrowRight,
    BsClock
} from 'react-icons/bs';

interface ApplicationChecklistProps {
    section: ChecklistSection;
}

const ApplicationChecklist = memo(({ section }: ApplicationChecklistProps) => {
    const [isExpanded, setIsExpanded] = useState(true);

    // get the right link for each section
    const getSectionLink = (sectionId: string): string => {
        switch (sectionId) {
            case 'academic':
                return '/profile';
            case 'application':
                return '/documents_essays/documents';
            case 'sop':
                return '/documents_essays/essays';
            case 'visa':
                return '/documents_essays/documents';
            default:
                return '/profile';
        }
    };

    // get status styling
    const getStatusStyles = () => {
        switch (section.status) {
            case 'complete':
                return {
                    container: 'border-green-200 bg-green-50',
                    header: 'text-green-800',
                    badge: 'bg-green-100 text-green-800'
                };
            case 'partial':
                return {
                    container: 'border-yellow-200 bg-yellow-50',
                    header: 'text-yellow-800',
                    badge: 'bg-yellow-100 text-yellow-800'
                };
            case 'incomplete':
                return {
                    container: 'border-red-200 bg-red-50',
                    header: 'text-red-800',
                    badge: 'bg-red-100 text-red-800'
                };
        }
    };

    const styles = getStatusStyles();
    const progressPercentage = section.totalItems > 0
        ? Math.round((section.completedCount / section.totalItems) * 100)
        : 0;

    return (
        <div className={`rounded-xl border ${styles.container} transition-all duration-200`}>
            {/* section header */}
            <div
                className="p-6 cursor-pointer"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center justify-between">
                    <div className="flex items-center">
                        <div className={`h-10 w-10 rounded-lg flex items-center justify-center mr-4 ${styles.badge}`}>
                            {section.icon}
                        </div>
                        <div>
                            <h3 className={`text-lg font-semibold ${styles.header} capitalize`}>
                                {section.title}
                            </h3>
                            <div className="flex items-center space-x-4 mt-1">
                                <span className="text-sm text-gray-600">
                                    {section.completedCount} of {section.totalItems} completed
                                </span>
                                <span className={`text-xs px-2 py-1 rounded-full font-medium ${styles.badge}`}>
                                    {progressPercentage}%
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center space-x-3">
                        {/* action button */}
                        <Link
                            href={getSectionLink(section.id)}
                            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-100 rounded-lg hover:bg-blue-200 transition-colors"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {section.status === 'complete' ? 'review' : 'continue'}
                            <BsArrowRight className="ml-1 h-3 w-3" />
                        </Link>

                        {/* expand/collapse button */}
                        <button className="text-gray-400 hover:text-gray-600">
                            {isExpanded ? <BsChevronDown className="h-4 w-4" /> : <BsChevronRight className="h-4 w-4" />}
                        </button>
                    </div>
                </div>

                {/* progress bar */}
                <div className="mt-4">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                            className={`h-2 rounded-full transition-all duration-500 ${
                                section.status === 'complete' ? 'bg-green-500' :
                                    section.status === 'partial' ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${progressPercentage}%` }}
                        />
                    </div>
                </div>
            </div>

            {/* expanded content */}
            {isExpanded && (
                <div className="px-6 pb-6">
                    <div className="space-y-3">
                        {section.items.map((item) => (
                            <div
                                key={item.id}
                                className="flex items-start p-3 bg-white rounded-lg border border-gray-200"
                            >
                                {/* status indicator */}
                                <div className="mr-3 mt-0.5">
                                    {item.completed ? (
                                        <BsCheckCircleFill className="h-4 w-4 text-green-500" />
                                    ) : (
                                        <BsCircle className={`h-4 w-4 ${item.required ? 'text-red-400' : 'text-gray-400'}`} />
                                    )}
                                </div>

                                {/* item content */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center">
                                        <h4 className={`text-sm font-medium ${
                                            item.completed ? 'text-gray-600 line-through' : 'text-gray-900'
                                        }`}>
                                            {item.label}
                                        </h4>
                                        {item.required && !item.completed && (
                                            <span className="ml-2 text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded">
                                                required
                                            </span>
                                        )}
                                        {item.completed && (
                                            <span className="ml-2 text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                                                done
                                            </span>
                                        )}
                                    </div>
                                    {item.description && (
                                        <p className="text-xs text-gray-500 mt-1">{item.description}</p>
                                    )}
                                </div>

                                {/* time indicator for incomplete items */}
                                {!item.completed && item.required && (
                                    <div className="flex items-center text-xs text-orange-600 ml-2">
                                        <BsClock className="h-3 w-3 mr-1" />
                                        pending
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* section tips */}
                    <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <div className="text-sm text-blue-800">
                            <span className="font-medium">💡 tip: </span>
                            {getSectionTip(section.id)}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
});

// helper function to get section-specific tips
const getSectionTip = (sectionId: string): string => {
    switch (sectionId) {
        case 'academic':
            return 'complete your academic profile first - this helps us recommend the best universities for you';
        case 'application':
            return 'upload documents early to give yourself time for any revisions or additional requirements';
        case 'sop':
            return 'use our AI assistant to help brainstorm and refine your personal statement';
        case 'visa':
            return 'start gathering visa documents after getting university acceptances - timing is important';
        default:
            return 'complete each section step by step for the best results';
    }
};

ApplicationChecklist.displayName = 'ApplicationChecklist';
export default ApplicationChecklist;