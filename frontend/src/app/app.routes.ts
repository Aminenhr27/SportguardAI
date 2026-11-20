import { Routes } from '@angular/router';
import { Dashboard } from './pages/dashboard/dashboard';
import { Movements } from './pages/movements/movements';
import { Risk } from './pages/risk/risk';
import { Sessions } from './pages/sessions/sessions';
import { Wellness } from './pages/wellness/wellness';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: Dashboard },
  { path: 'risk', component: Risk },
  { path: 'sessions', component: Sessions },
  { path: 'wellness', component: Wellness },
  { path: 'movements', component: Movements },
];