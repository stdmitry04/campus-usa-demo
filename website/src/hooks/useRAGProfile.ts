// src/hooks/useRAGProfile.ts - fixed to call embedProfile() without parameters
import { useEffect, useRef, useState } from 'react';
import { useProfile } from '@/hooks/useProfile';
import { useAuth} from '@/context/AuthContext';
import { ragClient } from '@/lib/ragClient';

export const useRAGProfile = () => {
    const profileHook = useProfile();
    const { profile, loading, error } = profileHook;
    const lastEmbeddedProfile = useRef<string | null>(null);
    const [embeddingStatus, setEmbeddingStatus] = useState<'idle' | 'embedding' | 'success' | 'error'>('idle');
    const [embeddingError, setEmbeddingError] = useState<string | null>(null);
    const { user } = useAuth();
    const [readyToEmbed, setReadyToEmbed] = useState(false);

    useEffect(() => {
        if (!loading && profile && user) {
            setReadyToEmbed(true);
        }
    }, [loading, profile, user]);

    // auto-embed profile when it changes
    useEffect(() => {
        if (!readyToEmbed || !profile || !user) return;

        // create a profile signature to detect changes
        const profileKey = JSON.stringify({
            user: {
                firstName: profile.user.firstName,
                lastName: profile.user.lastName,
                email: profile.user.email
            },
            phoneNumber: profile.phoneNumber,
            preferences: profile.preferences,
            academic: profile.academic,
            savedUniversityIds: profile.savedUniversityIds
        });
        // only re-embed if profile actually changed
        if (lastEmbeddedProfile.current !== profileKey) {
            console.log('🔄 profile changed, re-embedding...');
            embedProfile(profileKey);
        }

        setReadyToEmbed(false);
    }, [readyToEmbed, profile, user]);

    const embedProfile = async (profileKey: string) => {
        setEmbeddingStatus('embedding');
        setEmbeddingError(null);

        try {
            // call backend to embed profile (backend builds text from user's database data)
            const result = await ragClient.embedProfile();

            if (result.success) {
                lastEmbeddedProfile.current = profileKey;
                setEmbeddingStatus('success');
                console.log('✅ profile embedded successfully');
            } else {
                setEmbeddingStatus('error');
                setEmbeddingError(result.error || 'profile embedding failed');
                console.error('❌ profile embedding failed:', result.error);
            }
        } catch (error: any) {
            console.error('❌ failed to embed profile:', error);
            setEmbeddingStatus('error');
            setEmbeddingError(error.message || 'failed to embed profile');
        }
    };

    // manual re-embed function
    const forceReEmbed = async () => {
        if (!profile) return;

        const profileKey = JSON.stringify({
            user: {
                firstName: profile.user.firstName,
                lastName: profile.user.lastName,
                email: profile.user.email
            },
            phoneNumber: profile.phoneNumber,
            preferences: profile.preferences,
            academic: profile.academic,
            savedUniversityIds: profile.savedUniversityIds
        });

        // force re-embed by calling backend (backend reads profile from database)
        await embedProfile(profileKey);
    };

    return {
        ...profileHook,
        isEmbedded: embeddingStatus === 'success',
        embeddingStatus,
        embeddingError,
        forceReEmbed
    };
};