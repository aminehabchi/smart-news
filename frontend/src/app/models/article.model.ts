export interface Author {
  name: string | null;
  link: string | null;
}

export interface Article {
  id: string;
  creation_date: string | null;
  publish_date: string | null;
  title: string | null;
  body: string | null;
  topics: string[];
  author: Author;
  url: string | null;
  source: string | null;
}

export interface ArticlePage {
  items: Article[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}
