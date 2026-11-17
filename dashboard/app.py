import datetime

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="SportGuard AI", page_icon="🛡️")
st.title("🛡️ SportGuard AI")
st.caption("Suivi de la charge d'entraînement et du risque de blessure")

athlete_id = st.sidebar.number_input("ID de l'athlète", min_value=1, value=1, step=1)


def call_api(method, path, **kwargs):
    try:
        return requests.request(method, f"{API_URL}{path}", timeout=10, **kwargs)
    except requests.exceptions.ConnectionError:
        st.error("Impossible de joindre l'API. Vérifie que uvicorn tourne.")
        st.stop()


tab_risk, tab_session, tab_wellness = st.tabs(["Risque", "Séance", "Bien-être"])

with tab_risk:
    if st.button("Calculer le risque"):
        r = call_api("GET", f"/athletes/{athlete_id}/risk")
        if r.status_code != 200:
            st.error(str(r.json().get("detail", "Erreur")))
        else:
            data = r.json()
            labels = {"low": "🟢 Faible", "medium": "🟠 Moyen", "high": "🔴 Élevé"}
            st.subheader(f"Niveau de risque : {labels[data['risk_level']]}")
            st.progress(min(data["risk_score"], 1.0))
            st.write(f"Score : {data['risk_score']}")

            f = data["features"]
            c1, c2, c3 = st.columns(3)
            c1.metric("ACWR", f["acwr"])
            c2.metric("Charge 7 jours", f["acute_load"])
            c3.metric("Charge chronique", round(f["chronic_load"], 1))

            c4, c5, c6 = st.columns(3)
            c4.metric("Sommeil moyen (h)", round(f["sleep_avg"], 1))
            c5.metric("Fatigue moyenne", round(f["fatigue_avg"], 1))
            c6.metric("Stress moyen", round(f["stress_avg"], 1))

with tab_session:
    with st.form("session_form"):
        s_date = st.date_input("Date", datetime.date.today(), key="s_date")
        duration = st.number_input("Durée (minutes)", min_value=1, value=60)
        intensity = st.slider("Intensité (1 à 10)", 1, 10, 6)
        training_type = st.selectbox("Type", ["force", "cardio", "technique", "match"])
        submitted = st.form_submit_button("Enregistrer la séance")
    if submitted:
        r = call_api(
            "POST",
            "/sessions",
            json={
                "athlete_id": int(athlete_id),
                "date": s_date.isoformat(),
                "duration": int(duration),
                "intensity": intensity,
                "training_type": training_type,
            },
        )
        if r.status_code == 200:
            st.success(f"Séance enregistrée (charge : {r.json()['load']})")
        else:
            st.error(str(r.json().get("detail", "Erreur")))

with tab_wellness:
    with st.form("wellness_form"):
        w_date = st.date_input("Date", datetime.date.today(), key="w_date")
        sleep = st.number_input("Heures de sommeil", min_value=0.0, max_value=24.0, value=7.5, step=0.5)
        fatigue = st.slider("Fatigue (1 à 10)", 1, 10, 4)
        stress = st.slider("Stress (1 à 10)", 1, 10, 4)
        soreness = st.slider("Courbatures (1 à 10)", 1, 10, 4)
        submitted_w = st.form_submit_button("Enregistrer le bien-être")
    if submitted_w:
        r = call_api(
            "POST",
            "/wellness",
            json={
                "athlete_id": int(athlete_id),
                "date": w_date.isoformat(),
                "sleep_hours": sleep,
                "fatigue": fatigue,
                "stress": stress,
                "muscle_soreness": soreness,
            },
        )
        if r.status_code == 200:
            st.success("Bien-être enregistré")
        else:
            st.error(str(r.json().get("detail", "Erreur")))