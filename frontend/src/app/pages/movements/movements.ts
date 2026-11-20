import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService, MovementItem, readError } from '../../core/api.service';

@Component({
  selector: 'app-movements',
  imports: [FormsModule],
  templateUrl: './movements.html',
  styleUrl: './movements.css',
})
export class Movements implements OnInit {
  private api = inject(ApiService);

  athleteId = 1;
  items = signal<MovementItem[]>([]);
  error = signal('');

  ngOnInit() {
    this.load();
  }

  load() {
    this.error.set('');
    this.api.getMovements(this.athleteId).subscribe({
      next: (list) => this.items.set(list),
      error: (e) => {
        this.items.set([]);
        this.error.set(readError(e));
      },
    });
  }
}