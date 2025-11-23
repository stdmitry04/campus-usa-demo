'use client';

import {useEffect, useState} from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { FcGoogle } from 'react-icons/fc';
import { BsEnvelope, BsLock } from 'react-icons/bs';

export default function SignInPage() {
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const { login, isAuthenticated } = useAuth(); // Get auth functions
    const router = useRouter();

    useEffect(() => {
        if (isAuthenticated) {
            console.log('Authenticated, redirecting...');
            router.push('/checklist');
        }
    }, [isAuthenticated, router]);

    if (isAuthenticated) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div>Redirecting to dashboard...</div>
            </div>
        );
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        console.log('Attempting login with:', formData.username);

        const result = await login(formData.username, formData.password);

        if (result.success) {
            console.log('✅ Login successful, redirecting...');
            router.push('/');
        } else {
            console.log('❌ Login failed:', result.error);
            setError(result.error || 'Login failed');
        }

        setLoading(false);
    };

    return (
        <div className="flex flex-col min-h-screen">
            <div className="mx-auto w-full max-w-md px-4 py-16">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center mb-2">
                        <span className="bg-blue-500 text-white px-2 py-1 rounded text-sm mr-1">Campus</span>
                        <span className="font-bold text-sm">USA</span>
                    </div>
                    <h1 className="text-2xl font-bold mt-4">Welcome Back</h1>
                    <p className="text-gray-500 text-sm mt-1">Sign in to continue to Campus USA</p>
                </div>

                <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200">
                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                                Username
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-400">
                                    <BsEnvelope />
                                </div>
                                <input
                                    type="text"
                                    id="username"
                                    value={formData.username}
                                    onChange={(e) => setFormData({...formData, username: e.target.value})}
                                    placeholder="Enter your username"
                                    className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <div className="flex justify-between items-center mb-1">
                                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                                    Password
                                </label>
                                <a href="#" className="text-xs text-blue-600 hover:underline">Forgot Password?</a>
                            </div>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-400">
                                    <BsLock />
                                </div>
                                <input
                                    type="password"
                                    id="password"
                                    value={formData.password}
                                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                                    placeholder="Enter your password"
                                    className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    required
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center"
                        >
                            {loading ? 'Signing In...' : 'Sign In'}
                        </button>
                    </form>

                    <div className="mt-6">
                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-gray-300"></div>
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="px-2 bg-white text-gray-500">Or continue with</span>
                            </div>
                        </div>

                        <div className="mt-6">
                            <button className="w-full border border-gray-300 bg-white py-2 px-4 rounded-md hover:bg-gray-50 flex items-center justify-center">
                                <FcGoogle className="h-5 w-5 mr-2" />
                                <span>Google</span>
                            </button>
                        </div>
                    </div>
                </div>

                <p className="text-center mt-6 text-sm text-gray-600">
                    Don't have an account?{''}
                    <a href="/register" className="text-blue-600 hover:underline">
                        Sign up
                    </a>
                </p>
            </div>
        </div>
    );
}