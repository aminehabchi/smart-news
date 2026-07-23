import { Injectable, inject, signal } from '@angular/core';

import { ArticleService } from './article';

@Injectable({
  providedIn: 'root',
})
export class SavedArticlesService {
  private readonly articleService = inject(ArticleService);

  private readonly savedIds = signal<Record<string, true>>({});

  readonly ids = this.savedIds.asReadonly();

  constructor() {
    this.articleService.listSaved().subscribe((articles) => {
      this.savedIds.set(Object.fromEntries(articles.map((article) => [article.id, true as const])));
    });
  }

  isSaved(id: string): boolean {
    return !!this.savedIds()[id];
  }

  toggle(id: string): void {
    const saved = !this.isSaved(id);
    const previous = this.savedIds();

    const next = { ...previous };
    if (saved) {
      next[id] = true;
    } else {
      delete next[id];
    }
    this.savedIds.set(next);

    this.articleService.setSaved(id, saved).subscribe({
      error: () => this.savedIds.set(previous),
    });
  }
}
