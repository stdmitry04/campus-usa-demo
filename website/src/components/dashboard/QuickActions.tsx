// src/components/dashboard/QuickActions.tsx
import { memo } from 'react';
import Link from 'next/link';
import { UserProfile } from '@/types';
import {
    BsSearch,
    BsChatDots,
    BsFileEarmarkText,
    BsPerson,
    BsUpload,
    BsPencilSquare,
    BsBookmark,
    BsQuestionCircle
} from 'react-icons/bs';

interface QuickActionsProps {
    profile: UserProfile;
}

const QuickActions = memo(({ profile }: QuickActionsProps) => {
    // determine which actions to show based on profile completion
    const getRecommendedActions = () => {
        const actions = [];

        // if basic profile isn't complete, suggest completing it
        if (!profile.user.firstName || !profile.user.lastName || !profile.phoneNumber) {
            actions.push({
                id: 'complete_profile',
                title: 'complete profile',
                description: 'add your basic information',
                icon: <BsPerson className="h-5 w-5" />,
                href: '/profile',
                color: 'red'
            });
        }

        // if no academic info, suggest adding it
        if (!profile.academic) {
            actions.push({
                id: 'add_academic',
                title: 'add academic info',
                description: 'enter your GPA and test scores',
                icon: <BsPencilSquare className="h-5 w-5" />,
                href: '/profile',
                color: 'orange'
            });
        }

        // if no preferences set, suggest setting them
        if (profile.preferences.fieldsOfInterest.length === 0) {
            actions.push({
                id: 'set_preferences',
                title: 'set preferences',
                description: 'choose your fields of interest',
                icon: <BsBookmark className="h-5 w-5" />,
                href: '/profile',
                color: 'yellow'
            });
        }

        return actions;
    };

    const recommendedActions = getRecommendedActions();

    // all available quick actions
    const allActions = [
        {
            id: 'search_universities',
            title: 'search universities',
            description: 'find your perfect match',
            icon: <BsSearch className="h-5 w-5" />,
            href: '/universities',
            color: 'blue'
        },
        {
            id: 'ai_assistant',
            title: 'ask AI assistant',
            description: 'get personalized advice',
            icon: <BsChatDots className="h-5 w-5" />,
            href: '/ai-assistant',
            color: 'purple'
        },
        {
            id: 'upload_documents',
            title: 'upload documents',
            description: 'add transcripts and scores',
            icon: <BsUpload className="h-5 w-5" />,
            href: '/documents_essays/documents',
            color: 'green'
        },
        {
            id: 'write_essays',
            title: 'write essays',
            description: 'craft your personal statement',
            icon: <BsFileEarmarkText className="h-5 w-5" />,
            href: '/documents_essays/essays',
            color: 'indigo'
        }
    ];

    // combine recommended and regular actions
    const displayActions = [...recommendedActions, ...allActions];

    const getColorClasses = (color: string) => {
        const colorMap: Record<string, string> = {
            red: 'bg-red-50 border-red-200 text-red-700 hover:bg-red-100',
            orange: 'bg-orange-50 border-orange-200 text-orange-700 hover:bg-orange-100',
            yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700 hover:bg-yellow-100',
            green: 'bg-green-50 border-green-200 text-green-700 hover:bg-green-100',
            blue: 'bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100',
            indigo: 'bg-indigo-50 border-indigo-200 text-indigo-700 hover:bg-indigo-100',
            purple: 'bg-purple-50 border-purple-200 text-purple-700 hover:bg-purple-100',
        };
        return colorMap[color] || colorMap.blue;
    };

    return (
        <div className="space-y-6">
            {/* recommended actions section */}
            {recommendedActions.length > 0 && (
                <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <BsQuestionCircle className="h-5 w-5 text-orange-500 mr-2" />
                        recommended next steps
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                        {recommendedActions.map((action) => (
                            <Link
                                key={action.id}
                                href={action.href}
                                className={`block p-4 rounded-xl border transition-all duration-200 hover:shadow-md ${getColorClasses(action.color)}`}
                            >
                                <div className="flex items-start">
                                    <div className="mr-3 mt-0.5">
                                        {action.icon}
                                    </div>
                                    <div>
                                        <h4 className="font-medium mb-1">{action.title}</h4>
                                        <p className="text-sm opacity-80">{action.description}</p>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>
            )}

            {/* regular quick actions */}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">quick actions</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {allActions.map((action) => (
                        <Link
                            key={action.id}
                            href={action.href}
                            className={`block p-4 rounded-xl border transition-all duration-200 hover:shadow-md ${getColorClasses(action.color)}`}
                        >
                            <div className="text-center">
                                <div className="flex justify-center mb-3">
                                    {action.icon}
                                </div>
                                <h4 className="font-medium mb-1">{action.title}</h4>
                                <p className="text-sm opacity-80">{action.description}</p>
                            </div>
                        </Link>
                    ))}
                </div>
            </div>

            {/* helpful tips section */}
            <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">💡 helpful tips</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div className="space-y-2">
                        <div className="flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            <span>start early - give yourself plenty of time for each step</span>
                        </div>
                        <div className="flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            <span>use our AI assistant for personalized guidance and tips</span>
                        </div>
                        <div className="flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            <span>save universities as you browse to create your shortlist</span>
                        </div>
                    </div>
                    <div className="space-y-2">
                        <div className="flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            <span>upload documents early to avoid last-minute rushes</span>
                        </div>
                        <div className="flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            <span>keep track of application deadlines for each university</span>
                        </div>
                        <div className="flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            <span>review and update your profile information regularly</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
});

QuickActions.displayName = 'QuickActions';
export default QuickActions;