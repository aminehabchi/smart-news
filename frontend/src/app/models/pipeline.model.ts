export interface PipelineRun {
  id: string;
  started_at: string;
  finished_at: string | null;
  status: 'running' | 'success' | 'failed';
  trigger: 'scheduled' | 'manual';
  output: string | null;
  error: string | null;
}
