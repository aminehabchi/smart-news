export interface CountItem {
  label: string;
  count: number;
}

export interface EntityCount {
  value: string;
  count: number;
}

export interface DailySentimentCount {
  date: string;
  positive: number;
  neutral: number;
  negative: number;
}

export interface TopicTrendPoint {
  date: string;
  topic: string;
  count: number;
}

export interface Stats {
  total_articles: number;
  topics: CountItem[];
  sources: CountItem[];
  sentiment: CountItem[];
  top_persons: EntityCount[];
  top_organizations: EntityCount[];
  top_locations: EntityCount[];
  sentiment_trend: DailySentimentCount[];
  topic_trend: TopicTrendPoint[];
}
