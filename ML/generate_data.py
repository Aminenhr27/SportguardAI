from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

N_ATHLETES = 200
N_DAYS = 120
rows = []

for athlete_id in range(1, N_ATHLETES + 1):
    base = rng.uniform(250, 450)  # charge moyenne de l'athlète
    sleep_base = rng.uniform(6.5, 8.5)

    # charge journalière : 2 jours de repos par semaine
    loads = np.zeros(N_DAYS)
    for d in range(N_DAYS):
        if d % 7 not in (2, 6):
            loads[d] = max(0, rng.normal(base, base * 0.25))

    # pics de charge (stage, reprise brutale)
    for _ in range(rng.integers(2, 5)):
        start = rng.integers(30, N_DAYS - 10)
        loads[start:start + 7] *= rng.uniform(1.4, 2.0)

    # bien-être journalier
    rolling = pd.Series(loads).rolling(3, min_periods=1).mean().to_numpy()
    sleep = np.clip(rng.normal(sleep_base, 0.8, N_DAYS), 4, 10)
    fatigue = np.clip(3 + (rolling / base - 1) * 3 + rng.normal(0, 1, N_DAYS), 1, 10)
    stress = np.clip(rng.normal(4, 1.5, N_DAYS), 1, 10)

    for d in range(28, N_DAYS - 7):
        acute = loads[d - 6:d + 1].sum()
        chronic = loads[d - 27:d + 1].sum() / 4
        acwr = acute / chronic if chronic > 0 else 0
        sleep_avg = sleep[d - 6:d + 1].mean()
        fatigue_avg = fatigue[d - 6:d + 1].mean()
        stress_avg = stress[d - 6:d + 1].mean()

        # probabilité de blessure (règle inventée pour le prototype)
        z = (
            -3.5
            + 5.0 * max(acwr - 1.3, 0)
            + 0.7 * (fatigue_avg - 4)
            + 1.0 * (7.5 - sleep_avg)
            + 0.4 * (stress_avg - 4)
        )
        p = 1 / (1 + np.exp(-z))

        rows.append({
            "athlete_id": athlete_id,
            "day": d,
            "acute_load": round(acute, 1),
            "chronic_load": round(chronic, 1),
            "acwr": round(acwr, 2),
            "sleep_avg": round(sleep_avg, 2),
            "fatigue_avg": round(fatigue_avg, 2),
            "stress_avg": round(stress_avg, 2),
            "injury_next_7d": int(rng.random() < p),
        })

df = pd.DataFrame(rows)
out = Path(__file__).parent / "synthetic_data.csv"
df.to_csv(out, index=False)

print("Lignes :", len(df))
print("Taux de blessure :", round(df["injury_next_7d"].mean() * 100, 1), "%")
print("Fichier :", out)