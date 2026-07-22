import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { Article } from '../../models/article.model';
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
  readonly showAdvanced = signal(false);
  readonly advancedFilters = signal<ArticleListFilters>({});

  ngOnInit(): void {
    this.articleService.listSources().subscribe((sources) => this.sources.set(sources));

    this.route.queryParamMap.subscribe((params) => {
      this.query.set(params.get('q') ?? '');
      this.source.set(params.get('source') ?? '');

      const advanced: ArticleListFilters = {};
      for (const key of ADVANCED_FILTER_KEYS) {
        const value = params.get(key);
        if (value) {
          advanced[key] = value;
        }
      }
      this.advancedFilters.set(advanced);
      if (Object.keys(advanced).length > 0) {
        this.showAdvanced.set(true);
      }

      this.page.set(1);
      this.load();
    });
  }

  load(): void {
    this.loading.set(true);
    this.articleService
      .list(this.page(), this.pageSize, {
        q: this.query(),
        source: this.source(),
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
      queryParams: { source: source || null },
      queryParamsHandling: 'merge',
    });
  }

  toggleAdvanced(): void {
    this.showAdvanced.update((value) => !value);
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
    this.page.set(page);
    this.load();
  }
}
