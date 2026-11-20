import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Chart, registerables } from 'chart.js';
import { ApiService, AthleteItem, RiskResult, readError } from '../../core/api.service';

Chart.register(...registerables);

@Component({
  selector: 'app-dashboard',
  imports: [FormsModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements AfterViewInit, OnDestroy {
  private api = inject(ApiService);

  @ViewChild('loadCanvas') loadCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('riskCanvas') riskCanvas!: ElementRef<HTMLCanvasElement>;

  athletes = signal<AthleteItem[]>([]);
  athleteId: number | null = null;
  risk = signal<RiskResult | null>(null);
  error = signal('');

  private loadChart?: Chart;
  private riskChart?: Chart;

  ngAfterViewInit() {
    this.api.getAthletes().subscribe({
      next: (list) => {
        this.athletes.set(list);
        if (list.length > 0) {
          this.athleteId = list[0].id;
          this.refresh();
        }
      },
      error: (e) => this.error.set(readError(e)),
    });
  }

  ngOnDestroy() {
    this.loadChart?.destroy();
    this.riskChart?.destroy();
  }

  onSelect(id: number) {
    this.athleteId = id;
    this.refresh();
  }

  refresh() {
    if (this.athleteId === null) return;
    const id = this.athleteId;
    this.error.set('');

    this.api.getRisk(id).subscribe({
      next: (r) => {
        this.risk.set(r);
        this.drawRiskHistory(id);
      },
      error: (e) => {
        this.risk.set(null);
        this.error.set(readError(e));
        this.drawRiskHistory(id);
      },
    });

    this.api.getLoadHistory(id).subscribe((points) => {
      this.loadChart?.destroy();
      this.loadChart = new Chart(this.loadCanvas.nativeElement, {
        type: 'bar',
        data: {
          labels: points.map((p) => p.date.slice(5)),
          datasets: [{ label: 'Charge (durée × intensité)', data: points.map((p) => p.load) }],
        },
      });
    });
  }

  private drawRiskHistory(id: number) {
    this.api.getRiskHistory(id).subscribe((points) => {
      this.riskChart?.destroy();
      this.riskChart = new Chart(this.riskCanvas.nativeElement, {
        type: 'line',
        data: {
          labels: points.map((p) => p.date.slice(5)),
          datasets: [{ label: 'Score de risque', data: points.map((p) => p.risk_score) }],
        },
        options: { scales: { y: { min: 0, max: 1 } } },
      });
    });
  }
}