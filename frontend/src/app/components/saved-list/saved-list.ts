import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { catchError, forkJoin, of } from 'rxjs';

import { Article } from '../../models/article.model';
import { ArticleService } from '../../services/article';
import { SavedArticlesService } from '../../services/saved-articles';

@Component({
  selector: 'app-saved-list',
  imports: [RouterLink, DatePipe],
  templateUrl: './saved-list.html',
  styleUrl: './saved-list.scss',
})
export class SavedList implements OnInit {
  private readonly articleService = inject(ArticleService);
  readonly savedArticles = inject(SavedArticlesService);

  readonly articles = signal<Article[]>([]);
  readonly loading = signal(false);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    const ids = Object.keys(this.savedArticles.ids());
    if (ids.length === 0) {
      this.articles.set([]);
      return;
    }

    this.loading.set(true);
    forkJoin(
      ids.map((id) => this.articleService.get(id).pipe(catchError(() => of(null)))),
    ).subscribe((results) => {
      this.articles.set(results.filter((a): a is Article => a !== null));
      this.loading.set(false);
    });
  }

  unsave(id: string): void {
    this.savedArticles.toggle(id);
    this.load();
  }
}
