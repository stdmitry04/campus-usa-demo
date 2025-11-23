// src/components/profile/UserInfoComponents.tsx
import { memo, useState } from 'react';
import { UserProfile, UserUpdateData } from '@/types';

// user info display component
interface UserInfoDisplayProps {
    profile: UserProfile;
}

export const UserInfoDisplay = memo(({ profile }: UserInfoDisplayProps) => {
    return (
        <div className="grid grid-cols-2 gap-x-8 gap-y-4">
            <div>
                <div className="text-sm text-gray-600 mb-1">username</div>
                <div className="text-sm text-gray-900">{profile.user.username}</div>
            </div>
            <div>
                <div className="text-sm text-gray-600 mb-1">email</div>
                <div className="text-sm text-gray-900">{profile.user.email}</div>
            </div>
            <div>
                <div className="text-sm text-gray-600 mb-1">first name</div>
                <div className="text-sm text-gray-900">{profile.user.firstName || 'not set'}</div>
            </div>
            <div>
                <div className="text-sm text-gray-600 mb-1">last name</div>
                <div className="text-sm text-gray-900">{profile.user.lastName || 'not set'}</div>
            </div>
        </div>
    );
});

// user info form component
interface UserInfoFormProps {
    profile: UserProfile;
    onSave: (data: UserUpdateData) => Promise<void>;
    onCancel: () => void;
    updating: boolean;
}

export const UserInfoForm = memo(({
                                      profile,
                                      onSave,
                                      onCancel,
                                      updating
                                  }: UserInfoFormProps) => {
    const [formData, setFormData] = useState({
        firstName: profile.user.firstName || '',
        lastName: profile.user.lastName || '',
        email: profile.user.email || '',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await onSave(formData);
        } catch (error) {
            console.log('failed to save user info:', error);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        first name
                    </label>
                    <input
                        type="text"
                        value={formData.firstName}
                        onChange={(e) => setFormData(prev => ({ ...prev, firstName: e.target.value }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="enter your first name"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        last name
                    </label>
                    <input
                        type="text"
                        value={formData.lastName}
                        onChange={(e) => setFormData(prev => ({ ...prev, lastName: e.target.value }))}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="enter your last name"
                    />
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                    email address
                </label>
                <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
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

UserInfoDisplay.displayName = 'UserInfoDisplay';
UserInfoForm.displayName = 'UserInfoForm';