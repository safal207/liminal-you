import { useState } from 'react';
import { login, setAuthToken } from '../api/client';
import type { LoginResponse } from '../types';

type Props = {
  onLogin?: (resp: LoginResponse) => void;
};

export default function LoginForm({ onLogin }: Props) {
  const [userId, setUserId] = useState('user-001');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await login(userId);
      onLogin?.(resp);
    } catch (e) {
      setError('Auth failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setAuthToken(null);
    onLogin?.({
      access_token: '',
      token_type: 'Bearer',
      user_id: '',
      device_id: '',
      emotional_seed: [0.5, 0.35, 0.45],
    });
  };

  if (token) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-sm opacity-80">{userId}</span>
        <button
          onClick={handleLogout}
          className="rounded-full border border-accent px-3 py-1 text-xs hover:bg-accent hover:text-bg"
        >
          Logout
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <input
        className="w-36 rounded-md border border-accent/40 bg-transparent px-2 py-1 text-sm"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
        placeholder="user-id"
      />
      <button
        onClick={handleLogin}
        disabled={loading || userId.trim() === ''}
        className="rounded-full border border-accent px-3 py-1 text-xs hover:bg-accent hover:text-bg disabled:opacity-50"
      >
        {loading ? 'Signing…' : 'Login'}
      </button>
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  );
}

