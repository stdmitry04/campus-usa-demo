// src/components/profile/ContactInfoComponents.tsx
import { memo, useState } from 'react';
import { UserProfile, ProfileUpdateData, ContactInfoFormProps } from '@/types';

// contact info display component
interface ContactInfoDisplayProps {
    profile: UserProfile;
}

export const ContactInfoDisplay = memo(({ profile }: ContactInfoDisplayProps) => {
    return (
        <div className="grid grid-cols-1 gap-4">
            <div>
                <div className="text-sm text-gray-600 mb-1">phone number</div>
                <div className="text-sm text-gray-900">{profile.phoneNumber || 'not set'}</div>
            </div>
        </div>
    );
});

export const ContactInfoForm = memo(({
    profile,
    onSave,
    onCancel,
    updating
}: ContactInfoFormProps) => {
    const [formData, setFormData] = useState({
        phoneNumber: profile.phoneNumber || '',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await onSave(formData);
        } catch (error) {
            console.log('failed to save profile info:', error);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    phone number
                </label>
                <input
                    type="tel"
                    value={formData.phoneNumber}
                    onChange={(e) => setFormData({phoneNumber: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="enter your phone number"
                />
            </div>

            <div className="flex space-x-3 pt-2">
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

ContactInfoDisplay.displayName = 'ContactInfoDisplay';
ContactInfoForm.displayName = 'ContactInfoForm';