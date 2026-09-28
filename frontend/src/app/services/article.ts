import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from '../config';
import { Article, ArticlePage } from '../models/article.model';

export interface ArticleListFilters {
  q?: string;
  source?: string;
  predicted_topic?: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
  title?: string;
  body?: string;
  persons?: string;
  organizations?: string;
  locations?: string;
  dates_times?: string;
  quantities_percentages?: string;
  order?: 'newest' | 'oldest';
}

const FILTER_KEYS: (keyof ArticleListFilters)[] = [
  'q',
  'source',
  'predicted_topic',
  'sentiment',
  'title',
  'body',
  'persons',
  'organizations',
  'locations',
  'dates_times',
  'quantities_percentages',
  'order',
];

@Injectable({
  providedIn: 'root',
})
export class ArticleService {
  private readonly http = inject(HttpClient);

  list(page: number, pageSize: number, filters: ArticleListFilters = {}): Observable<ArticlePage> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    for (const key of FILTER_KEYS) {
      const value = filters[key];
      if (value) {
        params = params.set(key, value);
      }
    }
    return this.http.get<ArticlePage>(`${API_BASE_URL}/articles`, { params });
  }

  get(id: string): Observable<Article> {
    return this.http.get<Article>(`${API_BASE_URL}/articles/${id}`);
  }

  getRelated(id: string): Observable<Article[]> {
    return this.http.get<Article[]>(`${API_BASE_URL}/articles/${id}/related`);
  }

  listSources(): Observable<string[]> {
    return this.http.get<string[]>(`${API_BASE_URL}/sources`);
  }

  listTopics(): Observable<string[]> {
    return this.http.get<string[]>(`${API_BASE_URL}/topics`);
  }

  buildExportUrl(filters: ArticleListFilters = {}): string {
    let params = new HttpParams();
    for (const key of FILTER_KEYS) {
      const value = filters[key];
      if (value) {
        params = params.set(key, value);
      }
    }
    const query = params.toString();
    return `${API_BASE_URL}/articles/export${query ? '?' + query : ''}`;
  }

  listSaved(): Observable<Article[]> {
    return this.http.get<Article[]>(`${API_BASE_URL}/saved`);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${API_BASE_URL}/articles/${id}`);
  }

  setSaved(id: string, saved: boolean): Observable<Article> {
    const params = new HttpParams().set('saved', saved);
    return this.http.put<Article>(`${API_BASE_URL}/articles/${id}/save`, null, { params });
  }
}
