export type Reflection = {
  id: string;
  author: string;
  content: string;
  emotion: string;
  pad?: [number, number, number];
};

export type ReflectionPayload = {
  from_node: string;
  to_user: string;
  message: string;
  emotion: string;
  pad?: [number, number, number];
};

export type Profile = {
  id: string;
  name: string;
  bio?: string;
  nodes: { id: string; label: string }[];
  reflections_count: number;
  emotions: Record<string, number>;
  astro_opt_out: boolean;
  feedback_enabled: boolean;
  mirror_enabled: boolean;
};

// Auth / Device
export type LoginResponse = {
  access_token: string;
  token_type: string;
  user_id: string;
  device_id: string;
  emotional_seed: number[]; // [P, A, D]
};

export type DeviceInfo = {
  device_id: string;
  user_id: string;
  interaction_count: number;
  trust_level: number;
  emotional_seed: number[];
  resonance_map?: Record<string, number> | null;
};

// Emotions
export type EmotionInfo = {
  name: string;
  pad: number[]; // [P, A, D]
  category: 'positive' | 'negative' | 'neutral';
};

export type EmotionsResponse = {
  total: number;
  emotions: EmotionInfo[];
  categories: Record<string, number>;
};

// Analytics
export type Snapshot = {
  timestamp: number;
  pad: number[];
  entropy: number;
  coherence: number;
  samples: number;
  tone: string;
};

export type StatisticsResponse = {
  count: number;
  avg_entropy: number;
  avg_coherence: number;
  avg_pad: number[];
  tone_distribution: Record<string, number>;
  time_span_seconds: number;
};

export type TrendsResponse = {
  entropy_trend: 'increasing' | 'decreasing' | 'stable';
  coherence_trend: 'increasing' | 'decreasing' | 'stable';
  overall_mood: 'positive' | 'negative' | 'neutral';
  entropy_change: number;
  coherence_change: number;
};

export type PeaksValleysResponse = {
  highest_entropy: Snapshot[];
  lowest_entropy: Snapshot[];
  highest_coherence: Snapshot[];
  lowest_coherence: Snapshot[];
};

// i18n
export type TranslationsResponse = {
  language: string;
  translations: Record<string, string>;
};

// Mirror loop
export type MirrorEvent = {
  id?: number;
  ts: string;
  tone: string;
  intensity: number;
  reward: number;
  delta_coherence: number;
  delta_entropy: number;
  bucket_key: string;
  intensity_bin: number;
  user_count: number;
  dt_ms: number;
};

export type MirrorSummary = {
  total_events: number;
  avg_reward: number;
  coverage: number;
};

export type MirrorStatsPayload = {
  events: MirrorEvent[];
  summary: MirrorSummary;
  current?: {
    bucket_key?: string | null;
    policy_source?: string | null;
    action?: { tone: string; intensity: number } | null;
  } | null;
};

export type MirrorPolicyEntry = {
  bucket_key: string;
  tone: string;
  intensity_bin: number;
  reward_avg: number;
  n: number;
  updated_at: string;
  intensity: number;
};

export type MirrorPolicyResponse = {
  bucket_key: string | null;
  entries: MirrorPolicyEntry[];
  best: MirrorPolicyEntry | null;
};
