import axios from 'axios';
import {
  Profile,
  Reflection,
  ReflectionPayload,
  LoginResponse,
  DeviceInfo,
  EmotionInfo,
  EmotionsResponse,
  Snapshot,
  StatisticsResponse,
  TrendsResponse,
  PeaksValleysResponse,
  TranslationsResponse,
} from '../types';

const api = axios.create({
  baseURL: '/api'
});

export const setAuthToken = (token: string | null) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    localStorage.setItem('auth_token', token);
  } else {
    delete api.defaults.headers.common['Authorization'];
    localStorage.removeItem('auth_token');
  }
};

// Initialize from localStorage if present
(() => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  if (token) setAuthToken(token);
})();

export const fetchFeed = async (): Promise<Reflection[]> => {
  const { data } = await api.get<Reflection[]>('/feed');
  return data;
};

export const createReflection = async (payload: ReflectionPayload): Promise<Reflection> => {
  const { data } = await api.post<Reflection>('/reflection', payload);
  return data;
};

export const fetchProfile = async (profileId: string): Promise<Profile> => {
  const { data } = await api.get<Profile>(`/profile/${profileId}`);
  return data;
};

export const updateAstroPreference = async (
  profileId: string,
  astroOptOut: boolean
): Promise<Profile> => {
  const { data } = await api.patch<Profile>(`/profile/${profileId}/astro`, {
    astro_opt_out: astroOptOut
  });
  return data;
};

export const updateFeedbackPreference = async (
  profileId: string,
  enabled: boolean
): Promise<Profile> => {
  const { data } = await api.patch<Profile>(`/profile/${profileId}/settings`, {
    feedback_enabled: enabled
  });
  return data;
};

// Auth
export const login = async (userId: string, password?: string): Promise<LoginResponse> => {
  const { data } = await api.post<LoginResponse>('/auth/login', { user_id: userId, password });
  setAuthToken(data.access_token);
  return data;
};

export const getDeviceInfo = async (): Promise<DeviceInfo> => {
  const { data } = await api.get<DeviceInfo>('/auth/device');
  return data;
};

// Emotions
export const listEmotions = async (): Promise<EmotionsResponse> => {
  const { data } = await api.get<EmotionsResponse>('/emotions');
  return data;
};

export const suggestEmotions = async (query: string, limit = 5): Promise<EmotionInfo[]> => {
  const { data } = await api.get<EmotionInfo[]>(`/emotions/suggest/${encodeURIComponent(query)}?limit=${limit}`);
  return data;
};

// Analytics
export const getSnapshots = async (count = 100): Promise<Snapshot[]> => {
  const { data } = await api.get<Snapshot[]>(`/analytics/snapshots?count=${count}`);
  return data;
};

export const getStatistics = async (windowSeconds?: number): Promise<StatisticsResponse> => {
  const url = windowSeconds ? `/analytics/statistics?window_seconds=${windowSeconds}` : '/analytics/statistics';
  const { data } = await api.get<StatisticsResponse>(url);
  return data;
};

export const getTrends = async (windowSeconds = 3600): Promise<TrendsResponse> => {
  const { data } = await api.get<TrendsResponse>(`/analytics/trends?window_seconds=${windowSeconds}`);
  return data;
};

export const getPeaks = async (count = 10): Promise<PeaksValleysResponse> => {
  const { data } = await api.get<PeaksValleysResponse>(`/analytics/peaks?count=${count}`);
  return data;
};

// i18n
export const listLanguages = async (): Promise<string[]> => {
  const { data } = await api.get<{ languages: string[] }>('/i18n/languages');
  return data.languages;
};

export const getTranslations = async (language: string): Promise<TranslationsResponse> => {
  const { data } = await api.get<TranslationsResponse>(`/i18n/translations?language=${language}`);
  return data;
};

export const translateEmotion = async (emotion: string, language: string): Promise<string> => {
  const { data } = await api.get<{ original: string; translation: string; language: string }>(
    `/i18n/emotion/${encodeURIComponent(emotion)}?language=${language}`
  );
  return data.translation;
};
