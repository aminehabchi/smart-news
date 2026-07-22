import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from '../config';
import { Article, ArticlePage } from '../models/article.model';

export interface ArticleListFilters {
  q?: string;
  source?: string;
  title?: string;
  body?: string;
  persons?: string;
  organizations?: string;
  locations?: string;
  dates_times?: string;
  quantities_percentages?: string;
}

const FILTER_KEYS: (keyof ArticleListFilters)[] = [
  'q',
  'source',
  'title',
  'body',
  'persons',
  'organizations',
  'locations',
  'dates_times',
  'quantities_percentages',
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

  listSources(): Observable<string[]> {
    return this.http.get<string[]>(`${API_BASE_URL}/sources`);
  }
}
