import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService, readError } from '../../core/api.service';

@Component({
  selector: 'app-wellness',
  imports: [FormsModule],
  templateUrl: './wellness.html',
  styleUrl: './wellness.css',
})
export class Wellness {
  private api = inject(ApiService);

  athleteId = 1;
  date = new Date().toLocaleDateString('en-CA');
  sleepHours = 7.5;
  fatigue = 4;
  stress = 4;
  soreness = 4;

  message = signal('');
  error = signal('');

  save() {
    this.message.set('');
    this.error.set('');
    this.api
      .createWellness({
        athlete_id: this.athleteId,
        date: this.date,
        sleep_hours: this.sleepHours,
        fatigue: this.fatigue,
        stress: this.stress,
        muscle_soreness: this.soreness,
      })
      .subscribe({
        next: () => this.message.set('Bien-être enregistré'),
        error: (e) => this.error.set(readError(e)),
      });
  }
}