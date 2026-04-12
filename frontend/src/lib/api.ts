import type { FeedItem, GeneratedContent, AnnotatedItem, UserProfile, FeedbackPayload } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  // Feed
  getFeed: (date?: string) => fetchAPI<FeedItem[]>(`/api/feed${date ? `?date=${date}` : ''}`),
  getFeedItem: (id: string) => fetchAPI<FeedItem>(`/api/feed/${id}`),
  refreshFeed: () => fetchAPI<void>('/api/feed/refresh', { method: 'POST' }),
  generateContent: (id: string, mode: string) =>
    fetchAPI<GeneratedContent>(`/api/feed/${id}/generate`, {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),

  // Raw data
  getRawItems: (date?: string, source?: string, topic?: string) => {
    const params = new URLSearchParams();
    if (date) params.set('date', date);
    if (source) params.set('source', source);
    if (topic) params.set('topic', topic);
    return fetchAPI<AnnotatedItem[]>(`/api/raw?${params}`);
  },

  // Profile
  getProfile: () => fetchAPI<UserProfile>('/api/profile'),
  updateProfile: (profile: Partial<UserProfile>) =>
    fetchAPI<UserProfile>('/api/profile', {
      method: 'PUT',
      body: JSON.stringify(profile),
    }),
  checkOnboarding: () => fetchAPI<{ needed: boolean }>('/api/profile/onboarding-needed'),

  // Feedback
  submitFeedback: (feedback: FeedbackPayload) =>
    fetchAPI<void>('/api/feedback/item', {
      method: 'POST',
      body: JSON.stringify(feedback),
    }),
  submitPrompt: (prompt: string) =>
    fetchAPI<void>('/api/prompt', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    }),
};
