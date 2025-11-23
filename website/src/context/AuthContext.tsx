'use client'

import {createContext, useContext, useState, useEffect, ReactNode} from 'react';
import apiClient from '@/lib/api';

interface User {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
}

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    login: (username: string, password: string) => Promise<{ success: boolean; error?: string}>;
    logout: () => void;
    loading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null)

interface AuthProviderProps {
    children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (token) {
            console.log('Found token, checking validity...');
            // fetchUserProfile();
        } else {
            console.log('No token found');
        }
        setLoading(false);
    }, []);

    const fetchUserProfile = async (): Promise<void> => {
        try {
            const response = await apiClient.get('/profile/');
            setUser(response.data.user);
            console.log('✅ User loaded:', response.data.user);
        } catch (error: any) {
            console.log('❌ failed to fetch profile:', error);

            // only clear tokens on actual auth errors (401, 403)
            if (error.response?.status === 401 || error.response?.status === 403) {
                console.log('🔑 authentication error - clearing tokens');
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                setUser(null);
            } else if (error.response?.status >= 500) {
                // server error - don't clear tokens, but don't set user either
                console.log('🚨 server error on profile fetch - keeping tokens');
                // you could show an error message to user here
            } else {
                // network error or other issues
                console.log('🌐 network or other error on profile fetch');
            }
        } finally {
            setLoading(false);
        }
    };

    const login = async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
        try {
            console.log('Attempting login...');
            const response = await apiClient.post('/auth/login/', {
                username,
                password
            });

            localStorage.setItem('access_token', response.data.access);
            localStorage.setItem('refresh_token', response.data.refresh);
            console.log('tokens saved successfully');
            await fetchUserProfile();

            console.log('✅ Login successful');
            return { success: true };
        } catch (error: any) {
            console.log('❌ Login failed:', error.response?.data);
            return {
                success: false,
                error: 'Invalid username or password'
            };
        }
    };

    const logout = (): void => {
        console.log('Logging out...');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
    };

    // check if user is authenticated (has valid tokens)
    const isAuthenticated = !!user && !!localStorage.getItem('access_token');

    return (
        <AuthContext.Provider value={{
            user,
            isAuthenticated,
            login,
            logout,
            loading
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};
