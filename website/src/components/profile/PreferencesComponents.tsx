// src/components/profile/PreferencesComponents.tsx
import { memo, useState } from 'react';
import { BsX } from 'react-icons/bs';
import { UserProfile, PreferencesUpdateData, AidLevel, DegreeType } from '@/types';

// preferences display component
interface PreferencesDisplayProps {
    profile: UserProfile;
    getAidLevelOptions: () => any[];
    getDegreeTypeOptions: () => any[];
}

export const PreferencesDisplay = memo(({
                                            profile,
                                            getAidLevelOptions,
                                            getDegreeTypeOptions
                                        }: PreferencesDisplayProps) => {
    const aidOptions = getAidLevelOptions();
    const degreeOptions = getDegreeTypeOptions();

    const aidLabel = aidOptions.find(opt => opt.value === profile.preferences.needFinancialAid)?.label || 'unknown';
    const degreeLabel = degreeOptions.find(opt => opt.value === profile.preferences.applyingFor)?.label || 'unknown';

    return (
        <div className="grid grid-cols-2 gap-x-8 gap-y-4">
            <div>
                <div className="text-sm text-gray-600 mb-1">applying for</div>
                <div className="text-sm text-gray-900">{degreeLabel}</div>
            </div>
            <div>
                <div className="text-sm text-gray-600 mb-1">financial aid</div>
                <div className="text-sm text-gray-900">{aidLabel}</div>
            </div>
            <div>
                <div className="text-sm text-gray-600 mb-1">university ranking preference</div>
                <div className="text-sm text-gray-900">{profile.preferences.universityRankingMin} - {profile.preferences.universityRankingMax}</div>
            </div>
            <div>
                <div className="text-sm text-gray-600 mb-1">fields of interest</div>
                <div className="text-sm text-gray-900">
                    {profile.preferences.fieldsOfInterest.length > 0
                        ? profile.preferences.fieldsOfInterest.join(', ')
                        : 'not specified'
                    }
                </div>
            </div>
        </div>
    );
});

// preferences form component
interface PreferencesFormProps {
    profile: UserProfile;
    onSave: (data: PreferencesUpdateData) => Promise<void>;
    onCancel: () => void;
    updating: boolean;
    getAidLevelOptions: () => any[];
    getDegreeTypeOptions: () => any[];
}

export const PreferencesForm = memo(({
                                         profile,
                                         onSave,
                                         onCancel,
                                         updating,
                                         getAidLevelOptions,
                                         getDegreeTypeOptions
                                     }: PreferencesFormProps) => {
    const [formData, setFormData] = useState({
        applyingFor: profile.preferences.applyingFor,
        needFinancialAid: profile.preferences.needFinancialAid,
        universityRankingMin: profile.preferences.universityRankingMin,
        universityRankingMax: profile.preferences.universityRankingMax,
        fieldsOfInterest: [...profile.preferences.fieldsOfInterest],
        newField: '',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const { newField, ...saveData } = formData;
            await onSave(saveData);
        } catch (error) {
            console.log('failed to save preferences:', error);
        }
    };

    const addField = () => {
        if (formData.newField.trim() && !formData.fieldsOfInterest.includes(formData.newField.trim())) {
            setFormData(prev => ({
                ...prev,
                fieldsOfInterest: [...prev.fieldsOfInterest, prev.newField.trim()],
                newField: ''
            }));
        }
    };

    const removeField = (fieldToRemove: string) => {
        setFormData(prev => ({
            ...prev,
            fieldsOfInterest: prev.fieldsOfInterest.filter(field => field !== fieldToRemove)
        }));
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        applying for
                    </label>
                    <select
                        value={formData.applyingFor}
                        onChange={(e) => setFormData(prev => ({ ...prev, applyingFor: e.target.value as DegreeType }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {getDegreeTypeOptions().map(option => (
                            <option key={option.value} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        financial aid
                    </label>
                    <select
                        value={formData.needFinancialAid}
                        onChange={(e) => setFormData(prev => ({ ...prev, needFinancialAid: Number(e.target.value) as AidLevel }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {getAidLevelOptions().map(option => (
                            <option key={option.value} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        min university ranking
                    </label>
                    <input
                        type="number"
                        value={formData.universityRankingMin}
                        onChange={(e) => setFormData(prev => ({ ...prev, universityRankingMin: Number(e.target.value) }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        min="0"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        max university ranking
                    </label>
                    <input
                        type="number"
                        value={formData.universityRankingMax}
                        onChange={(e) => setFormData(prev => ({ ...prev, universityRankingMax: Number(e.target.value) }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        min="0"
                    />
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    fields of interest
                </label>
                <div className="flex gap-2 mb-2">
                    <input
                        type="text"
                        value={formData.newField}
                        onChange={(e) => setFormData(prev => ({ ...prev, newField: e.target.value }))}
                        className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="add a field of interest"
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addField())}
                    />
                    <button
                        type="button"
                        onClick={addField}
                        className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200"
                    >
                        add
                    </button>
                </div>
                <div className="flex flex-wrap gap-2">
                    {formData.fieldsOfInterest.map((field, index) => (
                        <span
                            key={index}
                            className="inline-flex items-center bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
                        >
                            {field}
                            <button
                                type="button"
                                onClick={() => removeField(field)}
                                className="ml-1 text-blue-600 hover:text-blue-800"
                            >
                                <BsX className="h-3 w-3" />
                            </button>
                        </span>
                    ))}
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

PreferencesDisplay.displayName = 'PreferencesDisplay';
PreferencesForm.displayName = 'PreferencesForm';