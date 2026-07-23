import { Pipe, PipeTransform } from '@angular/core';

const WORDS_PER_MINUTE = 200;

@Pipe({
  name: 'readingTime',
})
export class ReadingTimePipe implements PipeTransform {
  transform(body: string | null | undefined): string {
    const words = body?.trim() ? body.trim().split(/\s+/).length : 0;
    if (!words) {
      return '';
    }
    const minutes = Math.max(1, Math.round(words / WORDS_PER_MINUTE));
    return `${words} words · ${minutes} min read`;
  }
}
