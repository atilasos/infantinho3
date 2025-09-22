'use client';

import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';

import { API_BASE_URL } from '@/lib/config';
import type { AppUser } from '@/types/api';

const ACCESS_TOKEN_KEY = 'infantinho_access_token';

type AuthContextValue = {
  user: AppUser | null;
  accessToken: string | null;
  loading: boolean;
  isAuthenticated: boolean;
  signIn: () => Promise<void>;
  signInLocal: (payload: { identifier: string; password: string }) => Promise<void>;
  registerGuardian: (payload: GuardianRegistrationPayload) => Promise<void>;
  completePasswordChange: (payload: PasswordChangePayload) => Promise<void>;
  handleAzureCallback: (params: { code: string; state: string }) => Promise<void>;
  fetchWithAuth: (path: string, init?: RequestInit) => Promise<Response>;
  logout: () => Promise<void>;
};

type GuardianRegistrationPayload = {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
  studentNumber: string;
  relationship?: string;
};

type PasswordChangePayload = {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

function storeToken(token: string | null): void {
  if (typeof window === 'undefined') return;
  if (token) {
    window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
  } else {
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<AppUser | null>(null);
  const [loading, setLoading] = useState(true);

  const updateToken = useCallback((token: string | null) => {
    storeToken(token);
    setAccessToken(token);
  }, []);

  const refreshAccessToken = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/token/refresh`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) {
        updateToken(null);
        setUser(null);
        return false;
      }
      const data = await res.json();
      if (data.access) {
        updateToken(data.access as string);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to refresh token', error);
      updateToken(null);
      setUser(null);
      return false;
    }
  }, [updateToken]);

  const fetchWithAuth = useCallback(
    async (path: string, init?: RequestInit, retry = true): Promise<Response> => {
      const headers = new Headers(init?.headers);
      const token = accessToken ?? getStoredToken();
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      const response = await fetch(`${API_BASE_URL}${path}`, {
        ...init,
        credentials: 'include',
        headers,
      });

      if (response.status === 401 && retry) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
          return fetchWithAuth(path, init, false);
        }
      }
      return response;
    },
    [accessToken, refreshAccessToken],
  );

  const fetchCurrentUser = useCallback(async () => {
    try {
      const res = await fetchWithAuth('/me', { method: 'GET' }, false);
      if (!res.ok) {
        setUser(null);
        return;
      }
      const data = await res.json();
      setUser(data);
    } catch (error) {
      console.error('Failed to load current user', error);
      setUser(null);
    }
  }, [fetchWithAuth]);

  useEffect(() => {
    const initialise = async () => {
      try {
        let token = accessToken ?? getStoredToken();
        if (!token) {
          const refreshed = await refreshAccessToken();
          if (!refreshed) {
            setLoading(false);
            return;
          }
          token = getStoredToken();
        }
        if (token) {
          await fetchCurrentUser();
        }
      } finally {
        setLoading(false);
      }
    };
    initialise();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const signIn = useCallback(async () => {
    const res = await fetch(`${API_BASE_URL}/auth/microsoft/login`, {
      method: 'GET',
      credentials: 'include',
    });
    if (!res.ok) {
      throw new Error('Failed to initialise Microsoft login');
    }
    const data = await res.json();
    const url = data.authorization_url as string | undefined;
    if (url) {
      window.location.href = url;
    }
  }, []);

  const signInLocal = useCallback(
    async ({ identifier, password }: { identifier: string; password: string }) => {
      const res = await fetch(`${API_BASE_URL}/auth/login/local`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username: identifier, password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const message = (data && (data.error as string)) || 'Falha no login.';
        throw new Error(message);
      }
      if (data.access) {
        updateToken(data.access as string);
      }
      if (data.user) {
        setUser(data.user as AppUser);
      } else {
        await fetchCurrentUser();
      }
      if (data.must_change_password || (data.user as AppUser | undefined)?.must_change_password) {
        router.push('/force-password');
      } else {
        router.push('/');
      }
    },
    [fetchCurrentUser, router, updateToken],
  );

  const registerGuardian = useCallback(
    async ({
      firstName,
      lastName,
      email,
      password,
      confirmPassword,
      studentNumber,
      relationship,
    }: GuardianRegistrationPayload) => {
      const res = await fetch(`${API_BASE_URL}/auth/register/guardian`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email,
          password1: password,
          password2: confirmPassword,
          student_number: studentNumber,
          relationship,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const message =
          (data && (data.error as string)) ||
          (data?.errors && JSON.stringify(data.errors)) ||
          'Não foi possível criar a conta.';
        throw new Error(message);
      }
      if (data.access) {
        updateToken(data.access as string);
      }
      if (data.user) {
        setUser(data.user as AppUser);
      } else {
        await fetchCurrentUser();
      }
      router.push('/');
    },
    [fetchCurrentUser, router, updateToken],
  );

  const handleAzureCallback = useCallback(
    async ({ code, state }: { code: string; state: string }) => {
      const query = new URLSearchParams({ code, state }).toString();
      const res = await fetch(`${API_BASE_URL}/auth/microsoft/callback?${query}`, {
        method: 'GET',
        credentials: 'include',
      });
      if (!res.ok) {
        throw new Error('Falha na autenticação Microsoft.');
      }
      const data = await res.json();
      if (data.access) {
        updateToken(data.access as string);
      }
      if (data.user) {
        setUser(data.user as AppUser);
      } else {
        await fetchCurrentUser();
      }
      router.replace('/');
    },
    [fetchCurrentUser, router, updateToken],
  );

  const completePasswordChange = useCallback(
    async ({ oldPassword, newPassword, confirmPassword }: PasswordChangePayload) => {
      const res = await fetchWithAuth('/auth/password/change', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          old_password: oldPassword,
          new_password1: newPassword,
          new_password2: confirmPassword,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const errors = data?.errors;
        if (errors) {
          throw new Error(JSON.stringify(errors));
        }
        throw new Error('Não foi possível atualizar a password.');
      }
      if (data.access) {
        updateToken(data.access as string);
      }
      if (data.user) {
        setUser(data.user as AppUser);
      } else {
        await fetchCurrentUser();
      }
      router.push('/');
    },
    [fetchCurrentUser, fetchWithAuth, router, updateToken],
  );

  const logout = useCallback(async () => {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    updateToken(null);
    setUser(null);
    router.push('/login');
  }, [router, updateToken]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken,
      loading,
      isAuthenticated: Boolean(user),
      signIn,
      signInLocal,
      registerGuardian,
      completePasswordChange,
      handleAzureCallback,
      fetchWithAuth,
      logout,
    }),
    [
      accessToken,
      completePasswordChange,
      fetchWithAuth,
      handleAzureCallback,
      loading,
      logout,
      registerGuardian,
      signIn,
      signInLocal,
      user,
    ],
  );

  useEffect(() => {
    if (loading) return;
    if (typeof window === 'undefined') return;
    if (user?.must_change_password) {
      if (window.location.pathname !== '/force-password') {
        router.push('/force-password');
      }
    } else if (user && window.location.pathname === '/force-password') {
      router.push('/');
    }
  }, [loading, router, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
