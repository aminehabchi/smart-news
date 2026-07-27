import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';

import { PipelineRun } from '../../models/pipeline.model';
import { PipelineService } from '../../services/pipeline';

@Component({
  selector: 'app-pipeline-page',
  imports: [DatePipe],
  templateUrl: './pipeline-page.html',
  styleUrl: './pipeline-page.scss',
})
export class PipelinePage implements OnInit, OnDestroy {
  private readonly pipelineService = inject(PipelineService);
  private pollHandle: ReturnType<typeof setInterval> | null = null;

  readonly runs = signal<PipelineRun[]>([]);
  readonly loading = signal(true);
  readonly triggering = signal(false);
  readonly triggerError = signal('');

  readonly isRunning = computed(() => this.runs().some((run) => run.status === 'running'));

  ngOnInit(): void {
    this.loadRuns();
    this.pollHandle = setInterval(() => {
      if (this.isRunning()) {
        this.loadRuns();
      }
    }, 5000);
  }

  ngOnDestroy(): void {
    if (this.pollHandle !== null) {
      clearInterval(this.pollHandle);
    }
  }

  loadRuns(): void {
    this.pipelineService.listRuns().subscribe({
      next: (runs) => {
        this.runs.set(runs);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  runNow(): void {
    this.triggering.set(true);
    this.triggerError.set('');
    this.pipelineService.triggerRun().subscribe({
      next: () => {
        this.triggering.set(false);
        this.loadRuns();
      },
      error: (err: HttpErrorResponse) => {
        this.triggering.set(false);
        this.triggerError.set(err.error?.detail ?? 'Failed to start pipeline run.');
      },
    });
  }

  durationFor(run: PipelineRun): string {
    if (!run.finished_at) {
      return run.status === 'running' ? 'Running…' : '—';
    }
    const seconds = Math.round((new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()) / 1000);
    const minutes = Math.floor(seconds / 60);
    const rest = seconds % 60;
    return minutes > 0 ? `${minutes}m ${rest}s` : `${rest}s`;
  }
}
