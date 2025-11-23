// src/hooks/usePreload.ts
import { useRouter } from 'next/navigation';
import { useCallback } from 'react';

export const usePreload = () => {
    const router = useRouter();

    // preload any route
    const preloadRoute = useCallback((href: string) => {
        router.prefetch(href);
    }, [router]);

    // specific preload functions for common routes
    const preloadUniversities = useCallback(() => {
        preloadRoute('/universities');
    }, [preloadRoute]);

    const preloadAIAssistant = useCallback(() => {
        preloadRoute('/ai-assistant');
    }, [preloadRoute]);

    const preloadDocuments = useCallback(() => {
        preloadRoute('/documents_essays');
    }, [preloadRoute]);

    const preloadProfile = useCallback(() => {
        preloadRoute('/profile');
    }, [preloadRoute]);

    const preloadLogin = useCallback(() => {
        preloadRoute('/login');
    }, [preloadRoute]);

    const preloadRegister = useCallback(() => {
        preloadRoute('/register');
    }, [preloadRoute]);

    // preload university detail page
    const preloadUniversity = useCallback((universityId: number) => {
        preloadRoute(`/universities/${universityId}`);
    }, [preloadRoute]);

    return {
        preloadRoute,
        preloadUniversities,
        preloadAIAssistant,
        preloadDocuments,
        preloadProfile,
        preloadLogin,
        preloadRegister,
        preloadUniversity,
    };
};
