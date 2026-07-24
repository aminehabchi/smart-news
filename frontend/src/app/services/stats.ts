import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from '../config';
import { Stats } from '../models/stats.model';

@Injectable({
  providedIn: 'root',
})
export class StatsService {
  private readonly http = inject(HttpClient);

  get(): Observable<Stats> {
    return this.http.get<Stats>(`${API_BASE_URL}/stats`);
  }
}
