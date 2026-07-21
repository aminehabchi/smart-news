import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from '../config';
import { Article, ArticlePage } from '../models/article.model';

@Injectable({
  providedIn: 'root',
})
export class ArticleService {
  private readonly http = inject(HttpClient);

  list(page: number, pageSize: number, q?: string): Observable<ArticlePage> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (q) {
      params = params.set('q', q);
    }
    return this.http.get<ArticlePage>(`${API_BASE_URL}/articles`, { params });
  }

  get(id: string): Observable<Article> {
    return this.http.get<Article>(`${API_BASE_URL}/articles/${id}`);
  }
}
