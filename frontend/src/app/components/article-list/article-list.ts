import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { Article } from '../../models/article.model';
import { SourceNamePipe } from '../../pipes/source-name-pipe';
import { ArticleService } from '../../services/article';

@Component({
  selector: 'app-article-list',
  imports: [RouterLink, DatePipe, SourceNamePipe],
  templateUrl: './article-list.html',
  styleUrl: './article-list.scss',
})
export class ArticleList implements OnInit {
  private readonly articleService = inject(ArticleService);
  private readonly route = inject(ActivatedRoute);

  readonly pageSize = 18;

  readonly articles = signal<Article[]>([]);
  readonly page = signal(1);
  readonly totalPages = signal(1);
  readonly loading = signal(false);
  readonly query = signal('');

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((params) => {
      this.query.set(params.get('q') ?? '');
      this.page.set(1);
      this.load();
    });
  }

  load(): void {
    this.loading.set(true);
    this.articleService.list(this.page(), this.pageSize, this.query()).subscribe({
      next: (result) => {
        this.articles.set(result.items);
        this.totalPages.set(result.total_pages);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  goToPage(page: number): void {
    if (page < 1 || page > this.totalPages()) {
      return;
    }
    this.page.set(page);
    this.load();
  }
}
