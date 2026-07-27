import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { Article } from '../../models/article.model';
import { SourceNamePipe } from '../../pipes/source-name-pipe';
import { ArticleListFilters, ArticleService } from '../../services/article';

const ADVANCED_FILTER_KEYS: (keyof ArticleListFilters)[] = [
  'predicted_topic',
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
  readonly sentiment = signal<'positive' | 'neutral' | 'negative' | ''>('');
  readonly sources = signal<string[]>([]);
  readonly topics = signal<string[]>([]);
  readonly showAdvanced = signal(false);
  readonly advancedFilters = signal<ArticleListFilters>({});
  readonly order = signal<'newest' | 'oldest'>('newest');

  ngOnInit(): void {
    this.articleService.listSources().subscribe((sources) => this.sources.set(sources));
    this.articleService.listTopics().subscribe((topics) => this.topics.set(topics));

    this.route.queryParamMap.subscribe((params) => {
      this.query.set(params.get('q') ?? '');
      this.source.set(params.get('source') ?? '');
      const sentimentParam = params.get('sentiment');
      this.sentiment.set(
        sentimentParam === 'positive' || sentimentParam === 'neutral' || sentimentParam === 'negative'
          ? sentimentParam
          : '',
      );
      this.order.set(params.get('order') === 'oldest' ? 'oldest' : 'newest');

      const advanced: Record<string, string> = {};
      for (const key of ADVANCED_FILTER_KEYS) {
        const value = params.get(key);
        if (value) {
          advanced[key] = value;
        }
      }
      this.advancedFilters.set(advanced as ArticleListFilters);
      if (Object.keys(advanced).length > 0 || sentimentParam) {
        this.showAdvanced.set(true);
      }

      const pageParam = Number(params.get('page'));
      this.page.set(pageParam > 0 ? pageParam : 1);
      this.load();
    });
  }

  readonly exportUrl = computed(() =>
    this.articleService.buildExportUrl({
      q: this.query(),
      source: this.source(),
      sentiment: this.sentiment() || undefined,
      order: this.order(),
      ...this.advancedFilters(),
    }),
  );

  load(): void {
    this.loading.set(true);
    this.articleService
      .list(this.page(), this.pageSize, {
        q: this.query(),
        source: this.source(),
        sentiment: this.sentiment() || undefined,
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

  filterByTopic(topic: string, event: Event): void {
    event.preventDefault();
    event.stopPropagation();
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { predicted_topic: topic || null, page: null },
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
        sentiment: filters.sentiment || null,
        predicted_topic: filters.predicted_topic || null,
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
    predictedTopic: string,
    title: string,
    body: string,
    persons: string,
    organizations: string,
    locations: string,
    datesTimes: string,
    quantitiesPercentages: string,
    sentiment: string,
  ): void {
    this.applyAdvancedFilters({
      predicted_topic: predictedTopic,
      title,
      body,
      persons,
      organizations,
      locations,
      dates_times: datesTimes,
      quantities_percentages: quantitiesPercentages,
      sentiment: sentiment === 'positive' || sentiment === 'neutral' || sentiment === 'negative' ? sentiment : undefined,
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
