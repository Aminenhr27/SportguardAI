import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService, RiskResult } from '../../core/api.service';

@Component({
  selector: 'app-risk',
  imports: [FormsModule],
  templateUrl: './risk.html',
  styleUrl: './risk.css',
})
export class Risk {
  private api = inject(ApiService);

  athleteId = 1;
  result = signal<RiskResult | null>(null);
  error = signal('');

  load() {
    this.error.set('');
    this.api.getRisk(this.athleteId).subscribe({
      next: (r) => this.result.set(r),
      error: (e) => {
        this.result.set(null);
        this.error.set(e.error?.detail ?? "Impossible de joindre l'API");
      },
    });
  }
}