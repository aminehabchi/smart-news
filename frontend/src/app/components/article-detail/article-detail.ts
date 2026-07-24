import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { Article } from '../../models/article.model';
import { ReadingTimePipe } from '../../pipes/reading-time-pipe';
import { SourceNamePipe } from '../../pipes/source-name-pipe';
import { ArticleListFilters, ArticleService } from '../../services/article';
import { SavedArticlesService } from '../../services/saved-articles';

@Component({
  selector: 'app-article-detail',
  imports: [DatePipe, RouterLink, SourceNamePipe, ReadingTimePipe],
  templateUrl: './article-detail.html',
  styleUrl: './article-detail.scss',
})
export class ArticleDetail implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly articleService = inject(ArticleService);
  readonly savedArticles = inject(SavedArticlesService);

  readonly article = signal<Article | null>(null);
  readonly relatedArticles = signal<Article[]>([]);

  readonly entityGroups = computed(() => {
    const entities = this.article()?.entities;
    if (!entities) {
      return [];
    }
    return (
      [
        { label: 'Persons', key: 'persons', values: entities.persons },
        { label: 'Organizations', key: 'organizations', values: entities.organizations },
        { label: 'Locations', key: 'locations', values: entities.locations },
        { label: 'Dates & Times', key: 'dates_times', values: entities.dates_times },
        {
          label: 'Quantities & Percentages',
          key: 'quantities_percentages',
          values: entities.quantities_percentages,
        },
      ] satisfies { label: string; key: keyof ArticleListFilters; values: string[] }[]
    ).filter((group) => group.values.length > 0);
  });

  readonly sentimentSegments = computed(() => {
    const sentiment = this.article()?.sentiment;
    if (!sentiment) {
      return [];
    }
    return [
      { key: 'neg', label: 'Negative', width: sentiment.neg * 100, percent: Math.round(sentiment.neg * 100) },
      { key: 'neu', label: 'Neutral', width: sentiment.neu * 100, percent: Math.round(sentiment.neu * 100) },
      { key: 'pos', label: 'Positive', width: sentiment.pos * 100, percent: Math.round(sentiment.pos * 100) },
    ];
  });

  readonly sentimentOverall = computed(() => {
    const compound = this.article()?.sentiment?.compound;
    if (compound === undefined) {
      return null;
    }
    const label = compound >= 0.05 ? 'Positive' : compound <= -0.05 ? 'Negative' : 'Neutral';
    return `${label} (compound ${compound.toFixed(2)})`;
  });

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      const id = params.get('id');
      if (!id) {
        return;
      }
      this.article.set(null);
      this.relatedArticles.set([]);
      this.articleService.get(id).subscribe((article) => this.article.set(article));
      this.articleService.getRelated(id).subscribe((articles) => this.relatedArticles.set(articles));
    });
  }

  filterParams(key: keyof ArticleListFilters, value: string): ArticleListFilters {
    return { [key]: value } as ArticleListFilters;
  }

  toggleSave(): void {
    const id = this.article()?.id;
    if (id) {
      this.savedArticles.toggle(id);
    }
  }
}
