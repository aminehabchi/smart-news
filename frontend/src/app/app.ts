import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { LucideIconConfig } from 'lucide-angular';

import { Header } from './components/header/header';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Header],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  constructor() {
    // Medium's icons are thin line glyphs -- match that app-wide.
    const iconConfig = inject(LucideIconConfig);
    iconConfig.size = 20;
    iconConfig.strokeWidth = 1.5;
  }
}
