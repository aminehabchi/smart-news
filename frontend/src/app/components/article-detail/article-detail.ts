import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { Article } from '../../models/article.model';
import { SourceNamePipe } from '../../pipes/source-name-pipe';
import { ArticleService } from '../../services/article';
import { SavedArticlesService } from '../../services/saved-articles';

@Component({
  selector: 'app-article-detail',
  imports: [DatePipe, RouterLink, SourceNamePipe],
  templateUrl: './article-detail.html',
  styleUrl: './article-detail.scss',
})
export class ArticleDetail implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly articleService = inject(ArticleService);
  readonly savedArticles = inject(SavedArticlesService);

  readonly article = signal<Article | null>(null);

  readonly entityGroups = computed(() => {
    const entities = this.article()?.entities;
    if (!entities) {
      return [];
    }
    return [
      { label: 'Persons', values: entities.persons },
      { label: 'Organizations', values: entities.organizations },
      { label: 'Locations', values: entities.locations },
      { label: 'Dates & Times', values: entities.dates_times },
      { label: 'Quantities & Percentages', values: entities.quantities_percentages },
    ].filter((group) => group.values.length > 0);
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.articleService.get(id).subscribe((article) => this.article.set(article));
    }
  }

  toggleSave(): void {
    const id = this.article()?.id;
    if (id) {
      this.savedArticles.toggle(id);
    }
  }
}
