import { Component, computed, input } from '@angular/core';

export interface BarListItem {
  label: string;
  count: number;
}

@Component({
  selector: 'app-bar-list',
  templateUrl: './bar-list.html',
  styleUrl: './bar-list.scss',
})
export class BarList {
  readonly items = input<BarListItem[]>([]);

  readonly maxCount = computed(() => Math.max(1, ...this.items().map((item) => item.count)));
}
