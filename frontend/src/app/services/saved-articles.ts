import { Injectable, signal } from '@angular/core';

const STORAGE_KEY = 'saved-articles';

@Injectable({
  providedIn: 'root',
})
export class SavedArticlesService {
  private readonly savedIds = signal<Record<string, true>>(this.readFromStorage());

  readonly ids = this.savedIds.asReadonly();

  isSaved(id: string): boolean {
    return !!this.savedIds()[id];
  }

  toggle(id: string): void {
    const current = { ...this.savedIds() };
    if (current[id]) {
      delete current[id];
    } else {
      current[id] = true;
    }
    this.savedIds.set(current);
    this.writeToStorage(current);
  }

  private readFromStorage(): Record<string, true> {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  }

  private writeToStorage(value: Record<string, true>): void {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  }
}
