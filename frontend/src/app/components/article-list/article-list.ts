import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

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
  private readonly router = inject(Router);

  readonly pageSize = 18;

  readonly articles = signal<Article[]>([]);
  readonly page = signal(1);
  readonly totalPages = signal(1);
  readonly loading = signal(false);
  readonly query = signal('');
  readonly source = signal('');
  readonly sources = signal<string[]>([]);

  ngOnInit(): void {
    this.articleService.listSources().subscribe((sources) => this.sources.set(sources));

    this.route.queryParamMap.subscribe((params) => {
      this.query.set(params.get('q') ?? '');
      this.source.set(params.get('source') ?? '');
      this.page.set(1);
      this.load();
    });
  }

  load(): void {
    this.loading.set(true);
    this.articleService
      .list(this.page(), this.pageSize, { q: this.query(), source: this.source() })
      .subscribe({
        next: (result) => {
          this.articles.set(result.items);
          this.totalPages.set(result.total_pages);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }

  filterBySource(source: string): void {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { source: source || null },
      queryParamsHandling: 'merge',
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
