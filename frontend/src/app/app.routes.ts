import { Routes } from '@angular/router';
import { Risk } from './pages/risk/risk';
import { Sessions } from './pages/sessions/sessions';
import { Wellness } from './pages/wellness/wellness';

export const routes: Routes = [
  { path: '', redirectTo: 'risk', pathMatch: 'full' },
  { path: 'risk', component: Risk },
  { path: 'sessions', component: Sessions },
  { path: 'wellness', component: Wellness },
];