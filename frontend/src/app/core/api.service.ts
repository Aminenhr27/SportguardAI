import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface RiskResult {
  athlete_id: number;
  date: string;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high';
  features: {
    acute_load: number;
    chronic_load: number;
    acwr: number;
    sleep_avg: number;
    fatigue_avg: number;
    stress_avg: number;
  };
}

export interface SessionPayload {
  athlete_id: number;
  date: string;
  duration: number;
  intensity: number;
  training_type: string;
}

export interface WellnessPayload {
  athlete_id: number;
  date: string;
  sleep_hours: number;
  fatigue: number;
  stress: number;
  muscle_soreness: number;
}

export interface AthleteItem {
  id: number;
  name: string;
  sport: string | null;
}

export interface LoadPoint {
  date: string;
  load: number;
}

export interface RiskPoint {
  date: string;
  risk_score: number;
  risk_level: string;
}

// Transforme l'erreur de l'API en texte lisible
export function readError(e: any): string {
  const d = e?.error?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return d.map((x) => x.msg).join(', ');
  return "Impossible de joindre l'API";
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = 'http://127.0.0.1:8000';

  getAthletes(): Observable<AthleteItem[]> {
    return this.http.get<AthleteItem[]>(`${this.baseUrl}/athletes`);
  }

  getRisk(athleteId: number): Observable<RiskResult> {
    return this.http.get<RiskResult>(`${this.baseUrl}/athletes/${athleteId}/risk`);
  }

  getLoadHistory(athleteId: number, days = 28): Observable<LoadPoint[]> {
    return this.http.get<LoadPoint[]>(
      `${this.baseUrl}/athletes/${athleteId}/load-history?days=${days}`,
    );
  }

  getRiskHistory(athleteId: number): Observable<RiskPoint[]> {
    return this.http.get<RiskPoint[]>(`${this.baseUrl}/athletes/${athleteId}/risk-history`);
  }

  createSession(data: SessionPayload): Observable<{ id: number; load: number }> {
    return this.http.post<{ id: number; load: number }>(`${this.baseUrl}/sessions`, data);
  }

  createWellness(data: WellnessPayload): Observable<{ id: number; date: string }> {
    return this.http.post<{ id: number; date: string }>(`${this.baseUrl}/wellness`, data);
  }
}