// src/app/(dashboard)/profile/page.tsx
'use client';

import Image from 'next/image';
import { useState } from 'react';
import { useProfile } from '@/hooks/useProfile';
import PageHeader from '@/components/layout/PageHeader';
import ProfileSection from '@/components/profile/ProfileSection';
import { UserInfoDisplay, UserInfoForm } from '@/components/profile/UserInfoComponents';
import { ContactInfoDisplay, ContactInfoForm } from '@/components/profile/ContactInfoComponents';
import { PreferencesDisplay, PreferencesForm } from '@/components/profile/PreferencesComponents';
import { AcademicInfoDisplay, AcademicInfoForm } from '@/components/profile/AcademicInfoComponents';
import {
    BsCamera,
    BsExclamationTriangle,
    BsCheckCircle,
    BsX,
    BsPerson,
    BsGear
} from 'react-icons/bs';
import { FaGraduationCap } from "react-icons/fa";

type EditSection = 'none' | 'user' | 'profile' | 'academic' | 'preferences';

export default function ProfilePage() {
    const {
        profile,
        loading,
        updating,
        error,
        updateUser,
        updateProfile,
        updatePreferences,
        updateAcademic,
        updateContact,
        deleteAcademic,
        uploadAvatar,
        setError,
        getAidLevelOptions,
        getDegreeTypeOptions,
        getGpaScaleOptions,
        isProfileComplete,
        isAcademicComplete,
        isPreferencesComplete
    } = useProfile();

    const [editingSection, setEditingSection] = useState<EditSection>('none');
    const [successMessage, setSuccessMessage] = useState('');

    // show success message temporarily
    const showSuccess = (message: string) => {
        setSuccessMessage(message);
        setTimeout(() => setSuccessMessage(''), 3000);
    };

    // handle avatar upload
    const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        try {
            await uploadAvatar(file);
            showSuccess('avatar updated successfully!');
        } catch (error) {
            console.log('avatar upload failed:', error);
        }
    };

    if (loading) {
        return (
            <>
                <PageHeader title="profile" />
                <div className="flex justify-center items-center h-64">
                    <div className="text-gray-500">loading profile...</div>
                </div>
            </>
        );
    }

    if (!profile) {
        return (
            <>
                <PageHeader title="profile" />
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
                    <BsExclamationTriangle className="h-5 w-5 text-red-500 mr-2" />
                    <div>
                        <div className="text-red-800 font-medium">failed to load profile</div>
                        {error && <div className="text-red-600 text-sm">{error}</div>}
                    </div>
                </div>
            </>
        );
    }

    return (
        <>
            <PageHeader title="profile" />

            {/* success message */}
            {successMessage && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 flex items-center">
                    <BsCheckCircle className="h-5 w-5 text-green-500 mr-2" />
                    <div className="text-green-800 font-medium">{successMessage}</div>
                </div>
            )}

            {/* error message */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start">
                    <BsExclamationTriangle className="h-5 w-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <div className="text-red-800 font-medium">error</div>
                        <div className="text-red-600 text-sm">{error}</div>
                    </div>
                    <button
                        onClick={() => setError(null)}
                        className="ml-auto text-red-400 hover:text-red-600"
                    >
                        <BsX className="h-4 w-4" />
                    </button>
                </div>
            )}

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                {/* profile header with avatar */}
                <div className="flex items-center mb-8">
                    <div className="relative">
                        {profile.avatar ? (
                            <Image
                                src={profile.avatar}
                                alt="profile avatar"
                                width={96}
                                height={96}
                                className="h-24 w-24 rounded-full object-cover"
                            />
                        ) : (
                            <div className="h-24 w-24 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 text-3xl font-medium">
                                {profile.user.initials}
                            </div>
                        )}

                        {/* avatar upload button */}
                        <label className="absolute bottom-0 right-0 bg-blue-600 text-white p-2 rounded-full cursor-pointer hover:bg-blue-700 transition-colors">
                            <BsCamera className="h-3 w-3" />
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleAvatarUpload}
                                className="hidden"
                                disabled={updating}
                            />
                        </label>
                    </div>

                    <div className="ml-4">
                        <h2 className="text-xl font-semibold text-gray-900">
                            {profile.user.fullName}
                        </h2>
                        <p className="text-gray-500 text-sm">{profile.user.email}</p>
                        {profile.phoneNumber && (
                            <p className="text-gray-500 text-sm">{profile.phoneNumber}</p>
                        )}
                    </div>
                </div>

                {/* completion indicators */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                    <div className={`p-3 rounded-lg border ${isProfileComplete ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
                        <div className="text-sm font-medium">basic info</div>
                        <div className={`text-xs ${isProfileComplete ? 'text-green-600' : 'text-yellow-600'}`}>
                            {isProfileComplete ? 'complete' : 'incomplete'}
                        </div>
                    </div>
                    <div className={`p-3 rounded-lg border ${isAcademicComplete ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
                        <div className="text-sm font-medium">academic info</div>
                        <div className={`text-xs ${isAcademicComplete ? 'text-green-600' : 'text-yellow-600'}`}>
                            {isAcademicComplete ? 'complete' : 'not added'}
                        </div>
                    </div>
                    <div className={`p-3 rounded-lg border ${isPreferencesComplete ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
                        <div className="text-sm font-medium">preferences</div>
                        <div className={`text-xs ${isPreferencesComplete ? 'text-green-600' : 'text-yellow-600'}`}>
                            {isPreferencesComplete ? 'complete' : 'incomplete'}
                        </div>
                    </div>
                </div>

                {/* user information section */}
                <ProfileSection
                    title="user information"
                    icon={<BsPerson className="h-5 w-5" />}
                    isEditing={editingSection === 'user'}
                    onEdit={() => setEditingSection('user')}
                    onCancel={() => setEditingSection('none')}
                >
                    {editingSection === 'user' ? (
                        <UserInfoForm
                            profile={profile}
                            onSave={async (data) => {
                                await updateUser(data);
                                setEditingSection('none');
                                showSuccess('user information updated!');
                            }}
                            onCancel={() => setEditingSection('none')}
                            updating={updating}
                        />
                    ) : (
                        <UserInfoDisplay profile={profile} />
                    )}
                </ProfileSection>

                {/* contact information section */}
                <ProfileSection
                    title="contact information"
                    icon={<BsPerson className="h-5 w-5" />}
                    isEditing={editingSection === 'profile'}
                    onEdit={() => setEditingSection('profile')}
                    onCancel={() => setEditingSection('none')}
                >
                    {editingSection === 'profile' ? (
                        <ContactInfoForm
                            profile={profile}
                            onSave={async (data) => {
                                await updateContact(data);
                                setEditingSection('none');
                                showSuccess('contact information updated!');
                            }}
                            onCancel={() => setEditingSection('none')}
                            updating={updating}
                        />
                    ) : (
                        <ContactInfoDisplay profile={profile} />
                    )}
                </ProfileSection>

                {/* preferences section */}
                <ProfileSection
                    title="application preferences"
                    icon={<BsGear className="h-5 w-5" />}
                    isEditing={editingSection === 'preferences'}
                    onEdit={() => setEditingSection('preferences')}
                    onCancel={() => setEditingSection('none')}
                >
                    {editingSection === 'preferences' ? (
                        <PreferencesForm
                            profile={profile}
                            onSave={async (data) => {
                                await updatePreferences(data);
                                setEditingSection('none');
                                showSuccess('preferences updated!');
                            }}
                            onCancel={() => setEditingSection('none')}
                            updating={updating}
                            getAidLevelOptions={getAidLevelOptions}
                            getDegreeTypeOptions={getDegreeTypeOptions}
                        />
                    ) : (
                        <PreferencesDisplay
                            profile={profile}
                            getAidLevelOptions={getAidLevelOptions}
                            getDegreeTypeOptions={getDegreeTypeOptions}
                        />
                    )}
                </ProfileSection>

                {/* academic information section */}
                <ProfileSection
                    title="academic information"
                    icon={<FaGraduationCap className="h-5 w-5" />}
                    isEditing={editingSection === 'academic'}
                    onEdit={() => setEditingSection('academic')}
                    onCancel={() => setEditingSection('none')}
                    showDelete={!!profile.academic}
                    onDelete={async () => {
                        if (confirm('are you sure you want to delete your academic information?')) {
                            await deleteAcademic();
                            showSuccess('academic information deleted!');
                        }
                    }}
                >
                    {editingSection === 'academic' ? (
                        <AcademicInfoForm
                            profile={profile}
                            onSave={async (data) => {
                                await updateAcademic(data);
                                setEditingSection('none');
                                showSuccess('academic information updated!');
                            }}
                            onCancel={() => setEditingSection('none')}
                            updating={updating}
                            getGpaScaleOptions={getGpaScaleOptions}
                        />
                    ) : (
                        <AcademicInfoDisplay profile={profile} />
                    )}
                </ProfileSection>
            </div>
        </>
    );
}