// website/src/lib/api.ts
import axios from 'axios';

// determine API base URL based on environment
const getApiBaseUrl = () => {
    // check for explicit environment variable first
    if (process.env.NEXT_PUBLIC_API_URL) {
        return process.env.NEXT_PUBLIC_API_URL;
    }

    // fallback based on hostname
    if (typeof window !== 'undefined') {
        const hostname = window.location.hostname;

        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://127.0.0.1:8000/api';
        }

        // production - use your deployed backend
        return 'https://your-api-domain.com/api';
    }

    // server-side fallback (demo - configure for your deployment)
    return 'https://your-api-domain.com/api';
};

const API_BASE_URL = getApiBaseUrl();

console.log('🌐 API Base URL:', API_BASE_URL);

// create axios instance with configuration
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000, // 10 second timeout
    headers: {
        'Content-Type': 'application/json',
    },
});

// request interceptor to add auth token
apiClient.interceptors.request.use(
    (config) => {
        // only add token on client side
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem('access_token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// response interceptor for token refresh
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // handle 401 errors (token expired)
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                // only try refresh on client side
                if (typeof window !== 'undefined') {
                    const refreshToken = localStorage.getItem('refresh_token');

                    if (refreshToken) {
                        console.log('🔄 attempting token refresh...');

                        const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
                            refresh: refreshToken
                        });

                        const newAccessToken = response.data.access;
                        localStorage.setItem('access_token', newAccessToken);

                        // retry original request with new token
                        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                        return apiClient(originalRequest);
                    }
                }
            } catch (refreshError) {
                console.log('❌ token refresh failed:', refreshError);

                // clear tokens and redirect to login
                if (typeof window !== 'undefined') {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    window.location.href = '/login';
                }
            }
        }

        return Promise.reject(error);
    }
);

export default apiClient;