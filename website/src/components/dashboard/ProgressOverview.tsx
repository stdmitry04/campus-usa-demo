// src/components/dashboard/ProgressOverview.tsx
import { memo } from 'react';
import { ChecklistItem, ChecklistSection } from "@/types";
import {
    BsCheckCircleFill,
    BsClockFill,
    BsXCircleFill,
    BsArrowRight
} from 'react-icons/bs';

interface ProgressOverviewProps {
    sections: ChecklistSection[];
}

const ProgressOverview = memo(({ sections }: ProgressOverviewProps) => {
    // calculate overall stats
    const overallStats = sections.reduce(
        (acc, section) => ({
            completed: acc.completed + (section.status === 'complete' ? 1 : 0),
            partial: acc.partial + (section.status === 'partial' ? 1 : 0),
            incomplete: acc.incomplete + (section.status === 'incomplete' ? 1 : 0),
            totalItems: acc.totalItems + section.totalItems,
            completedItems: acc.completedItems + section.completedCount,
        }),
        { completed: 0, partial: 0, incomplete: 0, totalItems: 0, completedItems: 0 }
    );

    // get next action recommendation
    const getNextAction = () => {
        // find first incomplete section
        const incompleteSection = sections.find(section => section.status === 'incomplete');
        if (incompleteSection) {
            return {
                title: `complete ${incompleteSection.title}`,
                description: `start with ${incompleteSection.items.find(item => !item.completed && item.required)?.label || 'required items'}`,
                sectionId: incompleteSection.id
            };
        }

        // find first partial section
        const partialSection = sections.find(section => section.status === 'partial');
        if (partialSection) {
            const nextItem = partialSection.items.find(item => !item.completed && item.required);
            return {
                title: `finish ${partialSection.title}`,
                description: nextItem ? `complete ${nextItem.label}` : 'finish remaining items',
                sectionId: partialSection.id
            };
        }

        // all sections complete
        return {
            title: 'review applications',
            description: 'all sections complete - ready to submit!',
            sectionId: 'application'
        };
    };

    const nextAction = getNextAction();
    const progressPercentage = overallStats.totalItems > 0
        ? Math.round((overallStats.completedItems / overallStats.totalItems) * 100)
        : 0;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* overall progress card */}
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">overall progress</h3>
                    <div className="text-2xl font-bold text-blue-600">{progressPercentage}%</div>
                </div>

                <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-600">completed items</span>
                        <span className="font-medium">{overallStats.completedItems} / {overallStats.totalItems}</span>
                    </div>

                    <div className="w-full bg-gray-200 rounded-full h-3">
                        <div
                            className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                            style={{ width: `${progressPercentage}%` }}
                        />
                    </div>

                    <div className="grid grid-cols-3 gap-1 text-xs">
                        <div className="text-center">
                            <div className="font-medium text-green-600">{overallStats.completed}</div>
                            <div className="text-gray-500">complete</div>
                        </div>
                        <div className="text-center">
                            <div className="font-medium text-yellow-600">{overallStats.partial}</div>
                            <div className="text-gray-500">in progress</div>
                        </div>
                        <div className="text-center">
                            <div className="font-medium text-red-600">{overallStats.incomplete}</div>
                            <div className="text-gray-500">not started</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* sections status overview */}
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">sections status</h3>

                <div className="space-y-3">
                    {sections.map((section) => {
                        const percentage = section.totalItems > 0
                            ? Math.round((section.completedCount / section.totalItems) * 100)
                            : 0;

                        return (
                            <div key={section.id} className="flex items-center justify-between">
                                <div className="flex items-center">
                                    <div className="mr-3">
                                        {section.status === 'complete' ? (
                                            <BsCheckCircleFill className="h-4 w-4 text-green-500" />
                                        ) : section.status === 'partial' ? (
                                            <BsClockFill className="h-4 w-4 text-yellow-500" />
                                        ) : (
                                            <BsXCircleFill className="h-4 w-4 text-red-500" />
                                        )}
                                    </div>
                                    <span className="text-sm font-medium text-gray-900 capitalize">
                                        {section.title}
                                    </span>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <span className="text-xs text-gray-500">
                                        {section.completedCount}/{section.totalItems}
                                    </span>
                                    <div className="w-16 bg-gray-200 rounded-full h-1.5">
                                        <div
                                            className={`h-1.5 rounded-full transition-all duration-300 ${
                                                section.status === 'complete' ? 'bg-green-500' :
                                                    section.status === 'partial' ? 'bg-yellow-500' : 'bg-red-500'
                                            }`}
                                            style={{ width: `${percentage}%` }}
                                        />
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* next action card */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
                <h3 className="text-lg font-semibold text-blue-900 mb-4">next action</h3>

                <div className="space-y-4">
                    <div>
                        <h4 className="font-medium text-blue-800 mb-1">{nextAction.title}</h4>
                        <p className="text-sm text-blue-600">{nextAction.description}</p>
                    </div>

                    {progressPercentage < 100 && (
                        <button className="w-full flex items-center justify-center bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
                            continue setup
                            <BsArrowRight className="ml-2 h-3 w-3" />
                        </button>
                    )}

                    {progressPercentage === 100 && (
                        <div className="text-center">
                            <div className="text-2xl mb-2">🎉</div>
                            <div className="text-sm font-medium text-green-700">
                                amazing work! you're ready to apply!
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
});

ProgressOverview.displayName = 'ProgressOverview';
export default ProgressOverview;