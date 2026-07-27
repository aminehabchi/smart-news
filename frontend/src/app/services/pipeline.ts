import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from '../config';
import { PipelineRun } from '../models/pipeline.model';

@Injectable({
  providedIn: 'root',
})
export class PipelineService {
  private readonly http = inject(HttpClient);

  listRuns(): Observable<PipelineRun[]> {
    return this.http.get<PipelineRun[]>(`${API_BASE_URL}/pipeline/runs`);
  }

  triggerRun(): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(`${API_BASE_URL}/pipeline/run`, null);
  }
}
