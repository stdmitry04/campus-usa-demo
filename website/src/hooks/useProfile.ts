// src/hooks/useProfile.ts - Enhanced profile hook with new structure
import { useState, useEffect } from 'react';
import apiClient from '@/lib/api';
import {
    UserProfile,
    UserUpdateData,
    ProfileUpdateData,
    PreferencesUpdateData,
    AcademicUpdateData,
    AidLevel,
    DegreeType,
    transformBackendProfile,
    transformFrontendUser,
    transformFrontendAcademic,
    transformFrontendPreferences,
    validateAcademicInfo,
    validatePreferences
} from '@/types';

export const useProfile = () => {
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [loading, setLoading] = useState(true);
    const [updating, setUpdating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // fetch complete profile data
    const fetchProfile = async () => {
        try {
            setLoading(true);
            setError(null);

            console.log('📱 fetching user profile...');
            const response = await apiClient.get('/profile/');

            const transformedProfile = transformBackendProfile(response.data);
            console.log('✅ profile loaded:', transformedProfile);

            setProfile(transformedProfile);
        } catch (err: any) {
            console.log('❌ failed to fetch profile:', err);
            setError(err.response?.data?.detail || 'failed to load profile');
        } finally {
            setLoading(false);
        }
    };

    // update user information (name, email)
    const updateUser = async (updates: UserUpdateData): Promise<void> => {
        try {
            setUpdating(true);
            setError(null);

            // transform frontend data to backend format
            const backendUpdates = transformFrontendUser(updates);

            // remove undefined values
            Object.keys(backendUpdates).forEach(key => {
                if (backendUpdates[key as keyof typeof backendUpdates] === undefined) {
                    delete backendUpdates[key as keyof typeof backendUpdates];
                }
            });

            console.log('👤 updating user info with:', backendUpdates);
            await apiClient.patch('/profile/', backendUpdates);

            // refetch profile to get updated data
            await fetchProfile();

        } catch (err: any) {
            console.log('❌ failed to update user info:', err);
            setError(err.response?.data?.detail || 'failed to update user information');
            throw err;
        } finally {
            setUpdating(false);
        }
    };

    // update basic profile information (avatar, phone)
    const updateProfile = async (updates: ProfileUpdateData): Promise<void> => {
        try {
            setUpdating(true);
            setError(null);

            // handle file upload vs regular data
            if (updates.avatar) {
                // avatar upload with FormData
                const formData = new FormData();
                formData.append('avatar', updates.avatar);

                console.log('🖼️ uploading avatar...');
                await apiClient.patch('/profile/', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                });
            } else {
                // regular profile updates
                const cleanUpdates = { ...updates };
                delete cleanUpdates.avatar; // remove avatar from regular updates

                // remove undefined values
                Object.keys(cleanUpdates).forEach(key => {
                    if (cleanUpdates[key as keyof typeof cleanUpdates] === undefined) {
                        delete cleanUpdates[key as keyof typeof cleanUpdates];
                    }
                });

                if (Object.keys(cleanUpdates).length > 0) {
                    console.log('📱 updating profile with:', cleanUpdates);
                    await apiClient.patch('/profile/', cleanUpdates);
                }
            }

            // refetch profile to get updated data
            await fetchProfile();

        } catch (err: any) {
            console.log('❌ failed to update profile:', err);
            setError(err.response?.data?.detail || 'failed to update profile');
            throw err;
        } finally {
            setUpdating(false);
        }
    };

    const updateContact = async (updates: { phoneNumber?: string }) => {
        try {
            setUpdating(true);
            setError(null);

            const backendUpdates = {
                phone_number: updates.phoneNumber
            };

            console.log('📞 updating contact info with:', backendUpdates);
            await apiClient.patch('/profile/', backendUpdates);
            await fetchProfile();

        } catch (err: any) {
            console.log('❌ failed to update contact info:', err);
            setError(err.response?.data?.detail || 'failed to update contact information');
            throw err;
        } finally {
            setUpdating(false);
        }
    };


    // update application preferences
    const updatePreferences = async (updates: PreferencesUpdateData): Promise<void> => {
        try {
            setUpdating(true);
            setError(null);

            // validate preferences before sending
            const validationErrors = validatePreferences(updates);
            if (validationErrors.length > 0) {
                setError(validationErrors[0]);
                throw new Error(validationErrors.join(', '));
            }

            // transform frontend data to backend format
            const backendUpdates = transformFrontendPreferences(updates);

            // remove undefined values
            Object.keys(backendUpdates).forEach(key => {
                if (backendUpdates[key as keyof typeof backendUpdates] === undefined) {
                    delete backendUpdates[key as keyof typeof backendUpdates];
                }
            });

            console.log('⚙️ updating preferences with:', backendUpdates);
            await apiClient.patch('/preferences/', backendUpdates);

            // refetch profile to get updated data
            await fetchProfile();

        } catch (err: any) {
            console.log('❌ failed to update preferences:', err);
            setError(err.response?.data?.detail || 'failed to update preferences');
            throw err;
        } finally {
            setUpdating(false);
        }
    };

    // update academic information
    const updateAcademic = async (updates: AcademicUpdateData): Promise<void> => {
        try {
            setUpdating(true);
            setError(null);

            // validate academic info before sending
            const validationErrors = validateAcademicInfo(updates);
            if (validationErrors.length > 0) {
                setError(validationErrors[0]);
                throw new Error(validationErrors.join(', '));
            }

            // transform frontend data to backend format
            const backendUpdates = transformFrontendAcademic(updates);

            // remove undefined values
            Object.keys(backendUpdates).forEach(key => {
                if (backendUpdates[key as keyof typeof backendUpdates] === undefined) {
                    delete backendUpdates[key as keyof typeof backendUpdates];
                }
            });

            console.log('🎓 updating academic info with:', backendUpdates);
            await apiClient.patch('/academic-info/', backendUpdates);

            // refetch profile to get updated data
            await fetchProfile();

        } catch (err: any) {
            console.log('❌ failed to update academic info:', err);
            setError(err.response?.data?.detail || 'failed to update academic information');
            throw err;
        } finally {
            setUpdating(false);
        }
    };

    // delete academic information
    const deleteAcademic = async (): Promise<void> => {
        try {
            setUpdating(true);
            setError(null);

            console.log('🗑️ deleting academic info...');
            await apiClient.delete('/academic-info/');

            // refetch profile to get updated data
            await fetchProfile();

        } catch (err: any) {
            console.log('❌ failed to delete academic info:', err);
            setError(err.response?.data?.detail || 'failed to delete academic information');
            throw err;
        } finally {
            setUpdating(false);
        }
    };

    // upload avatar specifically
    const uploadAvatar = async (file: File): Promise<void> => {
        try {
            setUpdating(true);
            setError(null);

            // basic validation
            if (file.size > 5 * 1024 * 1024) { // 5MB limit
                throw new Error('avatar file too large (max 5MB)');
            }

            if (!file.type.startsWith('image/')) {
                throw new Error('please select an image file');
            }

            console.log('🖼️ uploading avatar...');
            await updateProfile({ avatar: file });

        } catch (err: any) {
            console.log('❌ failed to upload avatar:', err);
            if (err.message.includes('avatar file too large') || err.message.includes('please select an image')) {
                setError(err.message);
            } else {
                setError(err.response?.data?.detail || 'failed to upload avatar');
            }
            throw err;
        }
    };

    // get profile statistics
    const getProfileStats = async () => {
        try {
            const response = await apiClient.get('/user-stats/');
            return response.data;
        } catch (err: any) {
            console.log('❌ failed to get profile stats:', err);
            throw err;
        }
    };

    // helper functions for form data
    const getAidLevelOptions = () => [
        { value: AidLevel.None, label: 'no financial aid needed' },
        { value: AidLevel.Partial, label: 'partial financial aid' },
        { value: AidLevel.Full, label: 'full financial aid needed' }
    ];

    const getDegreeTypeOptions = () => [
        { value: DegreeType.Bachelor, label: "bachelor's degree" },
        { value: DegreeType.Master, label: "master's degree" },
        { value: DegreeType.PhD, label: 'phd' }
    ];

    const getGpaScaleOptions = () => [
        { value: '4.0', label: '4.0 scale' },
        { value: '5.0', label: '5.0 scale' },
        { value: '100', label: '100 point scale' }
    ];

    // initialize profile on mount
    useEffect(() => {
        fetchProfile();
    }, []);

    return {
        // state
        profile,
        loading,
        updating,
        error,

        // actions
        updateUser,
        updateProfile,
        updatePreferences,
        updateContact,
        updateAcademic,
        deleteAcademic,
        uploadAvatar,
        getProfileStats,
        refetch: fetchProfile,
        setError,

        // helpers
        getAidLevelOptions,
        getDegreeTypeOptions,
        getGpaScaleOptions,

        // computed values
        isProfileComplete: profile ? profile.user.firstName && profile.user.lastName && profile.phoneNumber : false,
        isAcademicComplete: profile?.academic ? true : false,
        isPreferencesComplete: profile?.preferences ? profile.preferences.fieldsOfInterest.length > 0 : false,
    };
};