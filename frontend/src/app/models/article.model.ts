export interface Author {
  name: string | null;
  link: string | null;
}

export interface Entities {
  persons: string[];
  organizations: string[];
  locations: string[];
  dates_times: string[];
  quantities_percentages: string[];
}

export interface Sentiment {
  neg: number;
  neu: number;
  pos: number;
  compound: number;
}

export interface Article {
  id: string;
  creation_date: string | null;
  publish_date: string | null;
  title: string | null;
  body: string | null;
  entities: Entities | null;
  sentiment: Sentiment | null;
  topics: string[];
  predicted_topic: string | null;
  author: Author;
  url: string | null;
  source: string | null;
  saved: boolean;
}

export interface ArticlePage {
  items: Article[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}
