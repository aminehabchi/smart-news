import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

import { BarList } from '../bar-list/bar-list';
import { Stats } from '../../models/stats.model';
import { StatsService } from '../../services/stats';

const TOPIC_CHART_WIDTH = 700;
const TOPIC_CHART_HEIGHT = 220;
const TOPIC_CHART_PADDING = { left: 30, right: 8, top: 10, bottom: 24 };

@Component({
  selector: 'app-stats-page',
  imports: [BarList, DatePipe, LucideAngularModule],
  templateUrl: './stats-page.html',
  styleUrl: './stats-page.scss',
})
export class StatsPage implements OnInit {
  private readonly statsService = inject(StatsService);

  readonly stats = signal<Stats | null>(null);
  readonly loading = signal(true);
  readonly hoveredTopicPoint = signal<{ xPercent: number; yPercent: number; tooltip: string } | null>(null);

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
        total,
        positiveWidth: (d.positive / maxTotal) * 100,
        neutralWidth: (d.neutral / maxTotal) * 100,
        negativeWidth: (d.negative / maxTotal) * 100,
        tooltip: `${d.date}: ${total} article${total === 1 ? '' : 's'} — ${d.positive} positive, ${d.neutral} neutral, ${d.negative} negative`,
      };
    });
  });

  readonly topicTrendChart = computed(() => {
    const points = this.stats()?.topic_trend ?? [];
    if (!points.length) {
      return null;
    }

    const dates: string[] = [];
    const topics: string[] = [];
    const byKey = new Map<string, number>();
    for (const p of points) {
      if (!dates.includes(p.date)) {
        dates.push(p.date);
      }
      if (!topics.includes(p.topic)) {
        topics.push(p.topic);
      }
      byKey.set(`${p.date}|${p.topic}`, p.count);
    }

    const maxCount = Math.max(1, ...points.map((p) => p.count));
    const { left, right, top, bottom } = TOPIC_CHART_PADDING;
    const plotWidth = TOPIC_CHART_WIDTH - left - right;
    const plotHeight = TOPIC_CHART_HEIGHT - top - bottom;
    const xFor = (i: number) => left + (dates.length > 1 ? (i / (dates.length - 1)) * plotWidth : plotWidth / 2);
    const yFor = (v: number) => top + plotHeight - (v / maxCount) * plotHeight;

    const series = topics.map((topic, i) => {
      const values = dates.map((date) => byKey.get(`${date}|${topic}`) ?? 0);
      const total = values.reduce((sum, v) => sum + v, 0);
      const lastIndex = values.length - 1;
      const label = topic.charAt(0).toUpperCase() + topic.slice(1);
      return {
        topic,
        label,
        colorClass: `series-${(i % 6) + 1}`,
        pointsAttr: values.map((v, idx) => `${xFor(idx)},${yFor(v)}`).join(' '),
        endX: xFor(lastIndex),
        endY: yFor(values[lastIndex]),
        tooltip: `${topic}: ${total} article${total === 1 ? '' : 's'} in the last 30 days, ${values[lastIndex]} today`,
        hoverPoints: values.map((v, idx) => ({
          x: xFor(idx),
          y: yFor(v),
          xPercent: (xFor(idx) / TOPIC_CHART_WIDTH) * 100,
          yPercent: (yFor(v) / TOPIC_CHART_HEIGHT) * 100,
          tooltip: `${label} — ${new Date(dates[idx] + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}: ${v} article${v === 1 ? '' : 's'}`,
        })),
      };
    });

    const gridLines = [0, 0.5, 1].map((frac) => ({
      y: top + plotHeight - frac * plotHeight,
      label: Math.round(frac * maxCount),
    }));

    const xTicks = dates
      .map((date, idx) => ({
        date,
        x: xFor(idx),
        idx,
        anchor: idx === 0 ? 'start' : idx === dates.length - 1 ? 'end' : 'middle',
      }))
      .filter((t) => t.idx % 5 === 0 || t.idx === dates.length - 1);

    return {
      width: TOPIC_CHART_WIDTH,
      height: TOPIC_CHART_HEIGHT,
      plotLeft: left,
      plotRight: TOPIC_CHART_WIDTH - right,
      series,
      gridLines,
      xTicks,
    };
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

  showTopicPoint(point: { xPercent: number; yPercent: number; tooltip: string }): void {
    this.hoveredTopicPoint.set(point);
  }

  hideTopicPoint(): void {
    this.hoveredTopicPoint.set(null);
  }
}
