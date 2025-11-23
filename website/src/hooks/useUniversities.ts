// src/hooks/useUniversities.ts - OPTIMIZED VERSION
import { useState, useEffect, useCallback, useMemo } from 'react';
import apiClient from '@/lib/api';
import { BackendUniversity, University } from "@/types";

const transformUniversity = (backendUni: BackendUniversity): University => ({
    id: backendUni.id,
    name: backendUni.name,
    location: backendUni.location,
    rank: backendUni.rank,
    admissionChance: backendUni.admission_chance_display,
    acceptanceRate: backendUni.acceptance_rate_display,
    avgSAT: backendUni.avg_sat_score,
    avgGPA: backendUni.avg_gpa,
    annualTuition: backendUni.tuition_display,
    hasFinancialAid: backendUni.has_financial_aid,
    websiteUrl: backendUni.website_url,
    logo: backendUni.logo,
});

export const useUniversities = () => {
    const [universities, setUniversities] = useState<University[]>([]);
    const [savedUniversityIds, setSavedUniversityIds] = useState<Set<number>>(new Set());
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // memoize universities by ID for O(1) lookups
    const universitiesById = useMemo(() => {
        return universities.reduce((acc, uni) => {
            acc[uni.id] = uni;
            return acc;
        }, {} as Record<number, University>);
    }, [universities]);

    // memoize universities by ranking for sorting
    const universitiesByRank = useMemo(() => {
        return [...universities].sort((a, b) => a.rank - b.rank);
    }, [universities]);

    // fetch universities from API
    const fetchUniversities = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            console.log('fetching universities from api...');
            const response = await apiClient.get('/universities/');

            const transformedUniversities = response.data.results.map(transformUniversity);
            console.log('universities loaded:', transformedUniversities.length);

            setUniversities(transformedUniversities);
        } catch (err: any) {
            console.log('failed to fetch universities:', err);
            setError(err.response?.data?.detail || 'failed to load universities');
        } finally {
            setLoading(false);
        }
    }, []);

    // toggle save status with optimistic updates
    const toggleSaveUniversity = useCallback(async (universityId: number) => {
        // optimistic update for immediate ui feedback
        const wasalreadySaved = savedUniversityIds.has(universityId);

        setSavedUniversityIds(prev => {
            const newSet = new Set(prev);
            if (wasalreadySaved) {
                newSet.delete(universityId);
            } else {
                newSet.add(universityId);
            }
            return newSet;
        });

        try {
            const response = await apiClient.post(`/universities/${universityId}/toggle_save/`);
            console.log('university save status:', response.data);

            // sync with server response if needed
            if (response.data.saved !== !wasalreadySaved) {
                // server response differs from optimistic update, fix it
                setSavedUniversityIds(prev => {
                    const newSet = new Set(prev);
                    if (response.data.saved) {
                        newSet.add(universityId);
                    } else {
                        newSet.delete(universityId);
                    }
                    return newSet;
                });
            }

            return response.data;
        } catch (err: any) {
            // revert optimistic update on error
            setSavedUniversityIds(prev => {
                const newSet = new Set(prev);
                if (wasalreadySaved) {
                    newSet.add(universityId);
                } else {
                    newSet.delete(universityId);
                }
                return newSet;
            });

            console.log('failed to save university:', err);
            throw err;
        }
    }, [savedUniversityIds]);

    // get saved universities
    const getSavedUniversities = useCallback(async () => {
        try {
            const response = await apiClient.get('/universities/saved/');
            const savedUniversities = response.data.map(transformUniversity);

            // update saved IDs set
            const savedIds: Set<number> = new Set(savedUniversities.map((uni: University) => uni.id));
            setSavedUniversityIds(savedIds);

            return savedUniversities;
        } catch (err: any) {
            console.log('failed to fetch saved universities:', err);
            throw err;
        }
    }, []);

    // filter universities by criteria
    const filterUniversities = useCallback((
        searchQuery?: string,
        maxRank?: number,
        hasFinancialAid?: boolean,
        minGPA?: number,
        maxTuition?: number
    ) => {
        return universities.filter(uni => {
            if (searchQuery) {
                const query = searchQuery.toLowerCase();
                if (!uni.name.toLowerCase().includes(query) &&
                    !uni.location.toLowerCase().includes(query)) {
                    return false;
                }
            }

            if (maxRank && uni.rank > maxRank) return false;
            if (hasFinancialAid && !uni.hasFinancialAid) return false;
            if (minGPA && uni.avgGPA < minGPA) return false;
            // add more filters as needed

            return true;
        });
    }, [universities]);

    // initialize data on mount
    useEffect(() => {
        fetchUniversities();
    }, [fetchUniversities]);

    return {
        universities,
        universitiesById,
        universitiesByRank,
        savedUniversityIds,
        loading,
        error,
        refetch: fetchUniversities,
        toggleSaveUniversity,
        getSavedUniversities,
        filterUniversities,
    };
};
