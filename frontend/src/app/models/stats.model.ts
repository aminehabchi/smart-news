export interface CountItem {
  label: string;
  count: number;
}

export interface EntityCount {
  value: string;
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
}
