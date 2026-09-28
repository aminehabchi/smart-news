import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';

import { Article } from '../../models/article.model';
import { ReadingTimePipe } from '../../pipes/reading-time-pipe';
import { SourceNamePipe } from '../../pipes/source-name-pipe';
import { ArticleListFilters, ArticleService } from '../../services/article';
import { SavedArticlesService } from '../../services/saved-articles';

@Component({
  selector: 'app-article-detail',
  imports: [DatePipe, RouterLink, SourceNamePipe, ReadingTimePipe, LucideAngularModule],
  templateUrl: './article-detail.html',
  styleUrl: './article-detail.scss',
})
export class ArticleDetail implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly articleService = inject(ArticleService);
  readonly savedArticles = inject(SavedArticlesService);

  readonly article = signal<Article | null>(null);
  readonly relatedArticles = signal<Article[]>([]);
  readonly confirmingDelete = signal(false);
  readonly deleting = signal(false);
  readonly deleteError = signal('');

  readonly entityGroups = computed(() => {
    const entities = this.article()?.entities;
    if (!entities) {
      return [];
    }
    return (
      [
        { label: 'Persons', key: 'persons', icon: 'users', values: entities.persons },
        { label: 'Organizations', key: 'organizations', icon: 'building-2', values: entities.organizations },
        { label: 'Locations', key: 'locations', icon: 'map-pin', values: entities.locations },
        { label: 'Dates & Times', key: 'dates_times', icon: 'calendar-clock', values: entities.dates_times },
        {
          label: 'Quantities & Percentages',
          key: 'quantities_percentages',
          icon: 'hash',
          values: entities.quantities_percentages,
        },
      ] satisfies { label: string; key: keyof ArticleListFilters; icon: string; values: string[] }[]
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
      this.confirmingDelete.set(false);
      this.deleteError.set('');
      this.articleService.get(id).subscribe((article) => this.article.set(article));
      this.articleService.getRelated(id).subscribe((articles) => this.relatedArticles.set(articles));
    });
  }

  filterParams(key: keyof ArticleListFilters, value: string): ArticleListFilters {
    return { [key]: value } as ArticleListFilters;
  }

  goToTopic(topic: string, event: Event): void {
    event.preventDefault();
    event.stopPropagation();
    this.router.navigate(['/'], { queryParams: { predicted_topic: topic } });
  }

  toggleSave(): void {
    const id = this.article()?.id;
    if (id) {
      this.savedArticles.toggle(id);
    }
  }

  deleteArticle(): void {
    const id = this.article()?.id;
    if (!id) {
      return;
    }
    this.deleting.set(true);
    this.deleteError.set('');
    this.articleService.delete(id).subscribe({
      next: () => this.router.navigate(['/']),
      error: () => {
        this.deleting.set(false);
        this.deleteError.set("Couldn't delete this article. Please try again.");
      },
    });
  }
}
