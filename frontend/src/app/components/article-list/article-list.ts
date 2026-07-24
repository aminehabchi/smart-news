import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { Article } from '../../models/article.model';
import { ReadingTimePipe } from '../../pipes/reading-time-pipe';
import { SourceNamePipe } from '../../pipes/source-name-pipe';
import { ArticleListFilters, ArticleService } from '../../services/article';

const ADVANCED_FILTER_KEYS: (keyof ArticleListFilters)[] = [
  'title',
  'body',
  'persons',
  'organizations',
  'locations',
  'dates_times',
  'quantities_percentages',
];

@Component({
  selector: 'app-article-list',
  imports: [RouterLink, DatePipe, SourceNamePipe, ReadingTimePipe],
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
  readonly showAdvanced = signal(false);
  readonly advancedFilters = signal<ArticleListFilters>({});
  readonly order = signal<'newest' | 'oldest'>('newest');

  ngOnInit(): void {
    this.articleService.listSources().subscribe((sources) => this.sources.set(sources));

    this.route.queryParamMap.subscribe((params) => {
      this.query.set(params.get('q') ?? '');
      this.source.set(params.get('source') ?? '');
      this.order.set(params.get('order') === 'oldest' ? 'oldest' : 'newest');

      const advanced: Record<string, string> = {};
      for (const key of ADVANCED_FILTER_KEYS) {
        const value = params.get(key);
        if (value) {
          advanced[key] = value;
        }
      }
      this.advancedFilters.set(advanced as ArticleListFilters);
      if (Object.keys(advanced).length > 0) {
        this.showAdvanced.set(true);
      }

      const pageParam = Number(params.get('page'));
      this.page.set(pageParam > 0 ? pageParam : 1);
      this.load();
    });
  }

  load(): void {
    this.loading.set(true);
    this.articleService
      .list(this.page(), this.pageSize, {
        q: this.query(),
        source: this.source(),
        order: this.order(),
        ...this.advancedFilters(),
      })
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
      queryParams: { source: source || null, page: null },
      queryParamsHandling: 'merge',
    });
  }

  toggleAdvanced(): void {
    this.showAdvanced.update((value) => !value);
  }

  toggleOrder(): void {
    const next = this.order() === 'newest' ? 'oldest' : 'newest';
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { order: next === 'newest' ? null : next, page: null },
      queryParamsHandling: 'merge',
    });
  }

  applyAdvancedFilters(filters: ArticleListFilters): void {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        title: filters.title?.trim() || null,
        body: filters.body?.trim() || null,
        persons: filters.persons?.trim() || null,
        organizations: filters.organizations?.trim() || null,
        locations: filters.locations?.trim() || null,
        dates_times: filters.dates_times?.trim() || null,
        quantities_percentages: filters.quantities_percentages?.trim() || null,
        page: null,
      },
      queryParamsHandling: 'merge',
    });
  }

  clearAdvancedFilters(): void {
    this.applyAdvancedFilters({});
  }

  onApplyAdvanced(
    title: string,
    body: string,
    persons: string,
    organizations: string,
    locations: string,
    datesTimes: string,
    quantitiesPercentages: string,
  ): void {
    this.applyAdvancedFilters({
      title,
      body,
      persons,
      organizations,
      locations,
      dates_times: datesTimes,
      quantities_percentages: quantitiesPercentages,
    });
  }

  goToPage(page: number): void {
    if (page < 1 || page > this.totalPages()) {
      return;
    }
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { page: page === 1 ? null : page },
      queryParamsHandling: 'merge',
    });
  }
}
