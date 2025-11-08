'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import apiClient from '../api/client';

interface User {
  id: string;
  email: string;
  tenant_id: string;
  role: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, tenantName: string) => Promise<void>;
  logout: () => void;
  setToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        try {
          const response = await apiClient.post('/api/v1/auth/login', {
            email: email,
            password: password,
          });

          const { access_token, user } = response.data;

          set({
            token: access_token,
            user: user,
            isAuthenticated: true
          });

          // Set token in axios defaults
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        } catch (error) {
          console.error('Login failed:', error);
          throw error;
        }
      },

      signup: async (email: string, password: string, tenantName: string) => {
        try {
          const response = await apiClient.post('/api/v1/auth/signup', {
            email,
            password,
            tenant_name: tenantName,
          });

          const { access_token, user } = response.data;

          set({
            token: access_token,
            user: user,
            isAuthenticated: true
          });

          // Set token in axios defaults
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        } catch (error) {
          console.error('Signup failed:', error);
          throw error;
        }
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false
        });
        delete apiClient.defaults.headers.common['Authorization'];

        // Clear local storage
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth-storage');
        }
      },

      setToken: (token: string) => {
        set({ token });
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      },
    }),
    {
      name: 'auth-storage',
      onRehydrateStorage: () => (state) => {
        // Set token in axios when rehydrating from storage
        if (state?.token) {
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${state.token}`;
        }
      },
    }
  )
);
