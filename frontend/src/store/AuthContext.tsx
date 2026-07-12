/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { api } from '../services/api';

interface User {
  id: string;
  name: string;
  email: string;
  createdAt: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('invoxio_token'));
  const [loading, setLoading] = useState(true);

  // On mount, re-validate the stored JWT and hydrate the user state
  useEffect(() => {
    const hydrate = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const data = await api<User>('/api/auth/me', { token });
        if (data.success && data.user) {
          setUser(data.user);
        } else {
          localStorage.removeItem('invoxio_token');
          setToken(null);
        }
      } catch {
        localStorage.removeItem('invoxio_token');
        setToken(null);
      } finally {
        setLoading(false);
      }
    };
    hydrate();
  }, [token]);

  const login = async (email: string, password: string) => {
    const data = await api<User>('/api/auth/login', {
      method: 'POST',
      body: { email, password },
    });
    if (data.token && data.user) {
      localStorage.setItem('invoxio_token', data.token);
      setToken(data.token);
      setUser(data.user);
    }
  };

  const register = async (name: string, email: string, password: string) => {
    const data = await api<User>('/api/auth/register', {
      method: 'POST',
      body: { name, email, password },
    });
    if (data.token && data.user) {
      localStorage.setItem('invoxio_token', data.token);
      setToken(data.token);
      setUser(data.user);
    }
  };

  const logout = () => {
    localStorage.removeItem('invoxio_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        loading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
