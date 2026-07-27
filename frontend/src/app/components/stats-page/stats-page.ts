import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';

import { BarList } from '../bar-list/bar-list';
import { Stats } from '../../models/stats.model';
import { StatsService } from '../../services/stats';

@Component({
  selector: 'app-stats-page',
  imports: [BarList, DatePipe],
  templateUrl: './stats-page.html',
  styleUrl: './stats-page.scss',
})
export class StatsPage implements OnInit {
  private readonly statsService = inject(StatsService);

  readonly stats = signal<Stats | null>(null);
  readonly loading = signal(true);

  readonly topicItems = computed(() => this.stats()?.topics ?? []);
  readonly sourceItems = computed(() => this.stats()?.sources ?? []);

  readonly personItems = computed(
    () => this.stats()?.top_persons.map((e) => ({ label: e.value, count: e.count })) ?? [],
  );
  readonly organizationItems = computed(
    () => this.stats()?.top_organizations.map((e) => ({ label: e.value, count: e.count })) ?? [],
  );
  readonly locationItems = computed(
    () => this.stats()?.top_locations.map((e) => ({ label: e.value, count: e.count })) ?? [],
  );

  readonly trendBars = computed(() => {
    const trend = this.stats()?.sentiment_trend ?? [];
    const maxTotal = trend.reduce((max, d) => Math.max(max, d.positive + d.neutral + d.negative), 0) || 1;
    return trend.map((d) => {
      const total = d.positive + d.neutral + d.negative;
      return {
        date: d.date,
        positiveHeight: (d.positive / maxTotal) * 100,
        neutralHeight: (d.neutral / maxTotal) * 100,
        negativeHeight: (d.negative / maxTotal) * 100,
        tooltip: `${d.date}: ${total} article${total === 1 ? '' : 's'} — ${d.positive} positive, ${d.neutral} neutral, ${d.negative} negative`,
      };
    });
  });

  readonly sentimentSegments = computed(() => {
    const sentiment = this.stats()?.sentiment ?? [];
    const total = sentiment.reduce((sum, item) => sum + item.count, 0);
    if (total === 0) {
      return [];
    }
    return sentiment.map((item) => ({
      key: item.label,
      label: item.label.charAt(0).toUpperCase() + item.label.slice(1),
      count: item.count,
      width: (item.count / total) * 100,
      percent: Math.round((item.count / total) * 100),
    }));
  });

  ngOnInit(): void {
    this.statsService.get().subscribe({
      next: (stats) => {
        this.stats.set(stats);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
