// src/components/profile/AcademicInfoComponents.tsx
import { memo, useState } from 'react';
import { UserProfile, AcademicUpdateData } from '@/types';

// academic info display component
interface AcademicInfoDisplayProps {
    profile: UserProfile;
}

export const AcademicInfoDisplay = memo(({ profile }: AcademicInfoDisplayProps) => {
    const academic = profile.academic;

    if (!academic) {
        return (
            <div className="text-sm text-gray-500 italic">
                no academic information added yet
            </div>
        );
    }

    return (
        <div className="grid grid-cols-4 gap-4">
            <div>
                <div className="text-sm text-gray-600 mb-1">high school</div>
                <div className="text-sm text-gray-900">{academic.highSchoolName}</div>
            </div>
            <div>
                <div className="text-sm text-gray-600 mb-1">graduation year</div>
                <div className="text-sm text-gray-900">{academic.graduationYear}</div>
            </div>
            <div>
                <div className="text-sm text-gray-600 mb-1">gpa ({academic.gpaScale})</div>
                <div className="text-sm text-gray-900">{academic.gpa}</div>
            </div>
            <div>
                <div className="text-sm text-gray-600 mb-1">sat score</div>
                <div className="text-sm text-gray-900">{academic.satScore || 'not taken'}</div>
            </div>
            <div>
                <div className="text-sm text-gray-600 mb-1">act score</div>
                <div className="text-sm text-gray-900">{academic.actScore || 'not taken'}</div>
            </div>
            <div>
                <div className="text-sm text-gray-600 mb-1">toefl score</div>
                <div className="text-sm text-gray-900">{academic.toeflScore || 'not taken'}</div>
            </div>
            <div>
                <div className="text-sm text-gray-600 mb-1">ielts score</div>
                <div className="text-sm text-gray-900">{academic.ieltsScore || 'not taken'}</div>
            </div>
            <div>
                <div className="text-sm text-gray-600 mb-1">class rank</div>
                <div className="text-sm text-gray-900">
                    {academic.classRank && academic.classSize
                        ? `${academic.classRank} / ${academic.classSize}`
                        : 'not set'
                    }
                </div>
            </div>
        </div>
    );
});

// academic info form component
interface AcademicInfoFormProps {
    profile: UserProfile;
    onSave: (data: AcademicUpdateData) => Promise<void>;
    onCancel: () => void;
    updating: boolean;
    getGpaScaleOptions: () => any[];
}

export const AcademicInfoForm = memo(({
                                          profile,
                                          onSave,
                                          onCancel,
                                          updating,
                                          getGpaScaleOptions
                                      }: AcademicInfoFormProps) => {
    const academic = profile.academic;
    const [formData, setFormData] = useState({
        highSchoolName: academic?.highSchoolName || '',
        graduationYear: academic?.graduationYear || new Date().getFullYear(),
        gpa: academic?.gpa || 0,
        gpaScale: academic?.gpaScale || '4.0',
        satScore: academic?.satScore || '',
        actScore: academic?.actScore || '',
        toeflScore: academic?.toeflScore || '',
        ieltsScore: academic?.ieltsScore || '',
        classRank: academic?.classRank || '',
        classSize: academic?.classSize || '',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            // convert empty strings to undefined for optional fields
            const cleanData = {
                ...formData,
                satScore: formData.satScore ? Number(formData.satScore) : undefined,
                actScore: formData.actScore ? Number(formData.actScore) : undefined,
                toeflScore: formData.toeflScore ? Number(formData.toeflScore) : undefined,
                ieltsScore: formData.ieltsScore ? Number(formData.ieltsScore) : undefined,
                classRank: formData.classRank ? Number(formData.classRank) : undefined,
                classSize: formData.classSize ? Number(formData.classSize) : undefined,
            };
            await onSave(cleanData);
        } catch (error) {
            console.log('failed to save academic info:', error);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        high school name *
                    </label>
                    <input
                        type="text"
                        value={formData.highSchoolName}
                        onChange={(e) => setFormData(prev => ({ ...prev, highSchoolName: e.target.value }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        graduation year *
                    </label>
                    <input
                        type="number"
                        value={formData.graduationYear}
                        onChange={(e) => setFormData(prev => ({ ...prev, graduationYear: Number(e.target.value) }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        min="2000"
                        max="2030"
                        required
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        gpa *
                    </label>
                    <input
                        type="number"
                        step="0.01"
                        value={formData.gpa}
                        onChange={(e) => setFormData(prev => ({ ...prev, gpa: Number(e.target.value) }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        min="0"
                        max="4"
                        required
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        gpa scale
                    </label>
                    <select
                        value={formData.gpaScale}
                        onChange={(e) => setFormData(prev => ({ ...prev, gpaScale: e.target.value }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {getGpaScaleOptions().map(option => (
                            <option key={option.value} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-4 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        sat score
                    </label>
                    <input
                        type="number"
                        value={formData.satScore}
                        onChange={(e) => setFormData(prev => ({ ...prev, satScore: e.target.value }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        min="400"
                        max="1600"
                        placeholder="optional"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        act score
                    </label>
                    <input
                        type="number"
                        value={formData.actScore}
                        onChange={(e) => setFormData(prev => ({ ...prev, actScore: e.target.value }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        min="1"
                        max="36"
                        placeholder="optional"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        toefl score
                    </label>
                    <input
                        type="number"
                        value={formData.toeflScore}
                        onChange={(e) => setFormData(prev => ({ ...prev, toeflScore: e.target.value }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        min="0"
                        max="120"
                        placeholder="optional"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        ielts score
                    </label>
                    <input
                        type="number"
                        step="0.5"
                        value={formData.ieltsScore}
                        onChange={(e) => setFormData(prev => ({ ...prev, ieltsScore: e.target.value }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        min="0"
                        max="9"
                        placeholder="optional"
                    />
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        class rank
                    </label>
                    <input
                        type="number"
                        value={formData.classRank}
                        onChange={(e) => setFormData(prev => ({ ...prev, classRank: e.target.value }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        min="1"
                        placeholder="optional"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        class size
                    </label>
                    <input
                        type="number"
                        value={formData.classSize}
                        onChange={(e) => setFormData(prev => ({ ...prev, classSize: e.target.value }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        min="1"
                        placeholder="optional"
                    />
                </div>
            </div>

            <div className="flex space-x-3 pt-4">
                <button
                    type="button"
                    onClick={onCancel}
                    disabled={updating}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                    cancel
                </button>
                <button
                    type="submit"
                    disabled={updating}
                    className="px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                    {updating ? 'saving...' : 'save changes'}
                </button>
            </div>
        </form>
    );
});

AcademicInfoDisplay.displayName = 'AcademicInfoDisplay';
AcademicInfoForm.displayName = 'AcademicInfoForm';