export interface RawItem {
  id: string;
  source: string;
  source_id: string;
  title: string;
  url: string;
  content: string;
  authors: string[];
  published_at: string;
  fetch_date: string;
  metadata: Record<string, any>;
}

export interface ItemAnnotation {
  item_id: string;
  relevance_score: number;
  quality_score: number;
  novelty_score: number;
  importance_score: number;
  topic_tag: string;
}

export interface AnnotatedItem extends RawItem {
  annotation: ItemAnnotation;
}

export interface FeedItem {
  id: string;
  cluster_id: string;
  final_rank: number;
  presentation_mode: 'news' | 'explainer_basics' | 'explainer_delta' | 'discussion';
  summary: string;
  why_it_matters: string;
  source_links: { url: string; title: string; source: string }[];
  feed_date: string;
  is_read: boolean;
  source_count: number;
  topic_label: string;
}

export interface GeneratedContent {
  feed_item_id: string;
  mode: string;
  content: string;
}

export interface UserProfile {
  goals: string[];
  working_topics: string[];
  learning_topics: string[];
}

export interface FeedbackPayload {
  feed_item_id: string;
  action: 'like' | 'dislike' | 'more_like_this' | 'less_like_this' | 'too_basic' | 'too_advanced' | 'save';
  comment?: string;
}
