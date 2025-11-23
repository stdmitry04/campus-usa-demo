'use client';

import { useState } from 'react';
import { Essay } from '@/types';
import {
    BsLightning,
    BsPlus
} from 'react-icons/bs';

const essaysMock: Essay[] = [
    {
        id: '1',
        title: 'MIT SOP',
        createdOn: '25/04/2025',
        content: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce scelerisque urna mi, eget amet pellentesque eros placerat. Et ut ornare or luctus tortor, ding mass vitae tempus.',
    },
];

export default function EssaysPage() {

    return (
        <>
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center text-sm text-blue-800">
                        <BsLightning className="h-4 w-4 text-amber-400 mr-2" />
                        AI-powered essay generation
                    </div>
                    <button className="text-xs text-blue-600 font-medium">
                        Try beta version
                    </button>
                </div>
            </div>

            <div className="space-y-4 mb-6">
                {essaysMock.map((essay) => (
                    <div key={essay.id} className="bg-white rounded-lg p-4 border border-gray-200">
                        <h3 className="font-medium text-gray-900 mb-1">{essay.title}</h3>
                        <div className="text-xs text-gray-500 mb-3">Created on {essay.createdOn}</div>
                        <p className="text-sm text-gray-700 mb-4">
                            {essay.content}
                        </p>
                        <div className="flex space-x-3">
                            <button className="flex-1 text-sm text-gray-700 bg-gray-100 py-1.5 rounded-md hover:bg-gray-200">
                                Edit
                            </button>
                            <button className="flex-1 text-sm text-gray-700 bg-gray-100 py-1.5 rounded-md hover:bg-gray-200">
                                Download
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            <div className="fixed bottom-6 right-6">
                <button className="h-12 w-12 bg-blue-600 text-white rounded-full shadow-lg flex items-center justify-center hover:bg-blue-700">
                    <BsPlus className="h-6 w-6" />
                </button>
            </div>
        </>
    );
}
