'use client';

import { useState, useEffect, useMemo } from 'react';
import { useProfile } from '@/hooks/useProfile';
import { useDocuments } from '@/hooks/useDocuments';
import { ChecklistItem, ChecklistSection } from '@/types';
import PageHeader from '@/components/layout/PageHeader';
import ApplicationChecklist from '@/components/dashboard/ApplicationChecklist';
import QuickActions from '@/components/dashboard/QuickActions';
import ProgressOverview from '@/components/dashboard/ProgressOverview';
import {
    BsCheckCircleFill,
    BsCircle,
    BsExclamationCircle,
    BsClock,
    BsTrophy,
    BsFileEarmarkText,
    BsPersonCheck,
    BsGlobe
} from 'react-icons/bs';

// define what documents we need for each section
const REQUIRED_DOCUMENTS = {
    academic: [
        { type: 'transcript', label: 'high school transcript', required: true },
        { type: 'sat_score', label: 'SAT score report', required: false },
        { type: 'act_score', label: 'ACT score report', required: false },
        { type: 'toefl_score', label: 'TOEFL score report', required: false },
        { type: 'ielts_score', label: 'IELTS score report', required: false },
    ],
    application: [
        { type: 'recommendation', label: 'letters of recommendation', required: true },
        { type: 'resume', label: 'resume/CV', required: true },
        { type: 'portfolio', label: 'portfolio (if applicable)', required: false },
        { type: 'other', label: 'additional documents', required: false },
    ],
    visa: [
        { type: 'passport', label: 'passport copy', required: true },
        { type: 'financial_statement', label: 'bank statements', required: true },
        { type: 'sponsor_letter', label: 'sponsor letter', required: false },
        { type: 'i20_form', label: 'I-20 form (after admission)', required: false },
    ]
};

export default function DashboardPage() {
    const { profile, loading: profileLoading } = useProfile();
    const { documents, loading: documentsLoading } = useDocuments();

    // calculate checklist sections based on current data
    const checklistSections = useMemo((): ChecklistSection[] => {
        if (!profile) return [];

        const documentsByType = documents.reduce((acc, doc) => {
            acc[doc.documentType] = doc;
            return acc;
        }, {} as Record<string, any>);

        // academic information section
        const academicItems: ChecklistItem[] = [
            {
                id: 'basic_info',
                label: 'basic profile information',
                completed: !!(profile.user.firstName && profile.user.lastName && profile.phoneNumber),
                required: true,
                description: 'name, email, phone number'
            },
            {
                id: 'academic_info',
                label: 'academic background',
                completed: !!profile.academic,
                required: true,
                description: 'GPA, graduation year, school info'
            },
            ...REQUIRED_DOCUMENTS.academic.map(doc => ({
                id: `doc_${doc.type}`,
                label: doc.label,
                completed: !!documentsByType[doc.type],
                required: doc.required,
                description: `upload your ${doc.label}`
            }))
        ];

        // application documents section
        const applicationItems: ChecklistItem[] = [
            {
                id: 'preferences',
                label: 'application preferences',
                completed: profile.preferences.fieldsOfInterest.length > 0,
                required: true,
                description: 'degree type, fields of interest, financial aid'
            },
            ...REQUIRED_DOCUMENTS.application.map(doc => ({
                id: `doc_${doc.type}`,
                label: doc.label,
                completed: !!documentsByType[doc.type],
                required: doc.required,
                description: `upload your ${doc.label}`
            }))
        ];

        // statement of purpose section
        const sopItems: ChecklistItem[] = [
            {
                id: 'personal_statement',
                label: 'personal statement draft',
                completed: false, // would need to check essays system
                required: true,
                description: 'write your compelling personal story'
            },
            {
                id: 'sop_review',
                label: 'statement review',
                completed: false,
                required: true,
                description: 'get feedback from mentors or AI assistant'
            },
            {
                id: 'final_sop',
                label: 'final statement version',
                completed: false,
                required: true,
                description: 'polished, final version ready for submission'
            }
        ];

        // visa documents section
        const visaItems: ChecklistItem[] = [
            {
                id: 'university_acceptance',
                label: 'university acceptance letter',
                completed: false, // would track based on applications
                required: true,
                description: 'acceptance from chosen university'
            },
            ...REQUIRED_DOCUMENTS.visa.map(doc => ({
                id: `visa_${doc.type}`,
                label: doc.label,
                completed: !!documentsByType[doc.type],
                required: doc.required,
                description: `upload your ${doc.label}`
            })),
            {
                id: 'visa_application',
                label: 'F-1 visa application',
                completed: false,
                required: true,
                description: 'complete DS-160 form and schedule interview'
            }
        ];

        // calculate section status
        const calculateSectionStatus = (items: ChecklistItem[]): ChecklistSection['status'] => {
            const requiredItems = items.filter(item => item.required);
            const completedRequired = requiredItems.filter(item => item.completed).length;

            if (completedRequired === requiredItems.length) return 'complete';
            if (completedRequired > 0) return 'partial';
            return 'incomplete';
        };

        return [
            {
                id: 'academic',
                title: 'academic information',
                icon: <BsPersonCheck className="h-5 w-5" />,
                items: academicItems,
                completedCount: academicItems.filter(item => item.completed).length,
                totalRequired: academicItems.filter(item => item.required).length,
                totalItems: academicItems.length,
                status: calculateSectionStatus(academicItems)
            },
            {
                id: 'application',
                title: 'application documents',
                icon: <BsFileEarmarkText className="h-5 w-5" />,
                items: applicationItems,
                completedCount: applicationItems.filter(item => item.completed).length,
                totalRequired: applicationItems.filter(item => item.required).length,
                totalItems: applicationItems.length,
                status: calculateSectionStatus(applicationItems)
            },
            {
                id: 'sop',
                title: 'statement of purpose',
                icon: <BsTrophy className="h-5 w-5" />,
                items: sopItems,
                completedCount: sopItems.filter(item => item.completed).length,
                totalRequired: sopItems.filter(item => item.required).length,
                totalItems: sopItems.length,
                status: calculateSectionStatus(sopItems)
            },
            {
                id: 'visa',
                title: 'visa documents',
                icon: <BsGlobe className="h-5 w-5" />,
                items: visaItems,
                completedCount: visaItems.filter(item => item.completed).length,
                totalRequired: visaItems.filter(item => item.required).length,
                totalItems: visaItems.length,
                status: calculateSectionStatus(visaItems)
            }
        ];
    }, [profile, documents]);

    // calculate overall progress
    const overallProgress = useMemo(() => {
        if (checklistSections.length === 0) return 0;

        const totalCompleted = checklistSections.reduce((sum, section) => sum + section.completedCount, 0);
        const totalItems = checklistSections.reduce((sum, section) => sum + section.totalItems, 0);

        return totalItems > 0 ? Math.round((totalCompleted / totalItems) * 100) : 0;
    }, [checklistSections]);

    const loading = profileLoading || documentsLoading;

    if (loading) {
        return (
            <>
                <PageHeader title="checklist" />
                <div className="flex justify-center items-center h-64">
                    <div className="text-gray-500">loading your application progress...</div>
                </div>
            </>
        );
    }

    if (!profile) {
        return (
            <>
                <PageHeader title="checklist" />
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
                    <BsExclamationCircle className="h-5 w-5 text-red-500 mr-2" />
                    <div>
                        <div className="text-red-800 font-medium">unable to load profile</div>
                        <div className="text-red-600 text-sm">please try refreshing the page</div>
                    </div>
                </div>
            </>
        );
    }

    return (
        <>
            <PageHeader title="checklist" />

            {/* welcome section */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 mb-8 border border-blue-100">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-semibold text-gray-900 mb-2">
                            welcome back, {profile.user.firstName || profile.user.username}! 👋
                        </h2>
                        <p className="text-gray-600">
                            let's continue working on your college application journey
                        </p>
                    </div>
                    <div className="text-right">
                        <div className="text-2xl font-bold text-blue-600 mb-1">{overallProgress}%</div>
                        <div className="text-sm text-gray-500">complete</div>
                    </div>
                </div>

                {/* progress bar */}
                <div className="mt-4">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${overallProgress}%` }}
                        />
                    </div>
                </div>
            </div>

            {/* progress overview */}
            <ProgressOverview sections={checklistSections} />

            {/* checklist sections */}
            <div className="grid gap-6 mb-8">
                {checklistSections.map(section => (
                    <ApplicationChecklist
                        key={section.id}
                        section={section}
                    />
                ))}
            </div>

            {/* quick actions */}
            <QuickActions profile={profile} />
        </>
    );
}