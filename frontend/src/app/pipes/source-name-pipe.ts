import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'sourceName',
})
export class SourceNamePipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    if (!value) {
      return '';
    }
    const name = value.replace(/^www\./, '').split('.')[0];
    return name.charAt(0).toUpperCase() + name.slice(1);
  }
}
