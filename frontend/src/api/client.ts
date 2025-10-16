import axios from 'axios';
import { Profile, Reflection, ReflectionPayload } from '../types';

const api = axios.create({
  baseURL: '/api'
});

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
