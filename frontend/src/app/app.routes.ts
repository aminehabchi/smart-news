import { Routes } from '@angular/router';

import { About } from './components/about/about';
import { ArticleDetail } from './components/article-detail/article-detail';
import { ArticleList } from './components/article-list/article-list';
import { SavedList } from './components/saved-list/saved-list';
import { StatsPage } from './components/stats-page/stats-page';

export const routes: Routes = [
  { path: '', component: ArticleList },
  { path: 'saved', component: SavedList },
  { path: 'stats', component: StatsPage },
  { path: 'about', component: About },
  { path: 'articles/:id', component: ArticleDetail },
];
