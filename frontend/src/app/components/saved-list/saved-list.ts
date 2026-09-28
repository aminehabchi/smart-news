import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';

import { Article } from '../../models/article.model';
import { ArticleService } from '../../services/article';
import { SavedArticlesService } from '../../services/saved-articles';

@Component({
  selector: 'app-saved-list',
  imports: [RouterLink, DatePipe, LucideAngularModule],
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
    this.loading.set(true);
    this.articleService.listSaved().subscribe({
      next: (articles) => {
        this.articles.set(articles);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  unsave(id: string): void {
    this.savedArticles.toggle(id);
    this.articles.update((articles) => articles.filter((article) => article.id !== id));
  }
}
