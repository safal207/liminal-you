import { useEffect, useState } from 'react';
import { getDeviceInfo } from '../api/client';
import type { DeviceInfo as DeviceInfoType } from '../types';

export default function DeviceInfo() {
  const [info, setInfo] = useState<DeviceInfoType | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (!token) return;
    getDeviceInfo().then(setInfo).catch(() => setError('Failed to fetch device info'));
  }, []);

  if (!localStorage.getItem('auth_token')) {
    return <div className="text-sm opacity-70">Login to view device memory</div>;
  }

  if (error) return <div className="text-sm text-red-400">{error}</div>;
  if (!info) return <div className="text-sm opacity-70">Loading device info…</div>;

  return (
    <div className="rounded-xl border border-accent/30 bg-white/5 p-4">
      <div className="text-accent mb-2 text-sm">Device Memory</div>
      <div className="text-sm">
        <div>Device: {info.device_id}</div>
        <div>User: {info.user_id}</div>
        <div>Trust: {info.trust_level.toFixed(2)}</div>
        <div>Interactions: {info.interaction_count}</div>
      </div>
      {info.resonance_map && (
        <div className="mt-2 text-sm">
          <div className="opacity-70">Resonance:</div>
          {Object.entries(info.resonance_map).map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span className="truncate">{k}</span>
              <span>{v.toFixed(3)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

