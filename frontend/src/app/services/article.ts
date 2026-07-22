import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from '../config';
import { Article, ArticlePage } from '../models/article.model';

export interface ArticleListFilters {
  q?: string;
  source?: string;
}

@Injectable({
  providedIn: 'root',
})
export class ArticleService {
  private readonly http = inject(HttpClient);

  list(page: number, pageSize: number, filters: ArticleListFilters = {}): Observable<ArticlePage> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (filters.q) {
      params = params.set('q', filters.q);
    }
    if (filters.source) {
      params = params.set('source', filters.source);
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
