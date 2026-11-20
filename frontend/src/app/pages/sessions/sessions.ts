import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService, readError } from '../../core/api.service';

@Component({
  selector: 'app-sessions',
  imports: [FormsModule],
  templateUrl: './sessions.html',
  styleUrl: './sessions.css',
})
export class Sessions {
  private api = inject(ApiService);

  athleteId = 1;
  date = new Date().toLocaleDateString('en-CA');
  duration = 60;
  intensity = 6;
  trainingType = 'force';

  message = signal('');
  error = signal('');

  save() {
    this.message.set('');
    this.error.set('');
    this.api
      .createSession({
        athlete_id: this.athleteId,
        date: this.date,
        duration: this.duration,
        intensity: this.intensity,
        training_type: this.trainingType,
      })
      .subscribe({
        next: (r) => this.message.set(`Séance enregistrée (charge : ${r.load})`),
        error: (e) => this.error.set(readError(e)),
      });
  }
}