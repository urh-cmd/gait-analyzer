"""
Haile - Anamnese
================
Patient intake form.
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.components.linear_ui import render_linear_css

st.set_page_config(
    page_title="Haile - Anamnese",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_linear_css()

st.markdown(
    """
    <h3 class="text-xl font-semibold text-white mb-1">Patientenanamnese</h3>
    <p class="text-slate-500 text-sm mb-6">Basisdaten und Beschwerden erfassen</p>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

st.markdown(
    """
    <div class="bg-slate-800/50 border border-slate-700 rounded-xl p-4 border-l-4 border-l-sky-500 mb-6">
        <p class="text-slate-300 text-sm leading-relaxed">
            Die Anamnese-Daten fließen in die KI-Auswertung ein und ermöglichen eine präzisere
            Beurteilung des Gangbildes im klinischen Kontext.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "anamnese_data" not in st.session_state:
    st.session_state.anamnese_data = {}

with st.form("anamnese_form"):
    st.markdown('<p class="text-lg font-medium text-slate-300 mb-4">Basisdaten</p>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        patient_id = st.text_input(
            "Patienten-ID *",
            value=st.session_state.anamnese_data.get("patient_id", ""),
            placeholder="PAT-2026-001"
        )
    with col2:
        alter = st.number_input(
            "Alter (Jahre) *",
            min_value=0,
            max_value=120,
            value=st.session_state.anamnese_data.get("alter", 30)
        )
    with col3:
        geschlecht = st.selectbox(
            "Geschlecht *",
            options=["", "Männlich", "Weiblich", "Divers"],
            index=["", "Männlich", "Weiblich", "Divers"].index(
                st.session_state.anamnese_data.get("geschlecht", "")
            ) if st.session_state.anamnese_data.get("geschlecht") in ["", "Männlich", "Weiblich", "Divers"] else 0
        )

    col1, col2 = st.columns(2)
    with col1:
        gewicht = st.number_input("Gewicht (kg)", min_value=20.0, max_value=200.0, value=70.0, step=0.1)
    with col2:
        groesse = st.number_input("Größe (cm)", min_value=100, max_value=220, value=170)

    bmi = gewicht / ((groesse/100) ** 2) if groesse > 0 else 0
    st.markdown(f'<p class="text-slate-500 text-sm -mt-2 mb-4">BMI: {bmi:.1f}</p>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<p class="text-lg font-medium text-slate-300 mb-4">Hauptbeschwerde</p>', unsafe_allow_html=True)
    hauptbeschwerde = st.text_area(
        "Was ist der Hauptgrund für Ihren Besuch? *",
        value=st.session_state.anamnese_data.get("hauptbeschwerde", ""),
        placeholder="z.B. Schmerzen beim Gehen nach Knie-OP...",
        height=80
    )
    schmerz_intensitaet = 0
    schmerz_dauer = ""
    schmerz_ort = st.multiselect(
        "Lokalisation der Beschwerden",
        options=[
            "Keine Schmerzen",
            "Kopf/Hals",
            "Schulter links", "Schulter rechts",
            "Rücken oben", "Rücken Mitte", "Rücken unten (LWS)",
            "Hüfte links", "Hüfte rechts",
            "Oberschenkel links", "Oberschenkel rechts",
            "Knie links", "Knie rechts",
            "Unterschenkel links", "Unterschenkel rechts",
            "Sprunggelenk/Fuß links", "Sprunggelenk/Fuß rechts"
        ],
        default=st.session_state.anamnese_data.get("schmerz_ort", [])
    )
    if "Keine Schmerzen" not in schmerz_ort:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            schmerz_intensitaet = st.slider(
                "Schmerzintensität (0–10)",
                0, 10,
                st.session_state.anamnese_data.get("schmerz_intensitaet", 0)
            )
        with col_s2:
            schmerz_dauer = st.selectbox(
                "Dauer der Beschwerden",
                options=[
                    "Akut (< 1 Woche)",
                    "Subakut (1–6 Wochen)",
                    "Chronisch (> 6 Wochen)",
                    "Rezidiv"
                ],
                index=["Akut (< 1 Woche)", "Subakut (1–6 Wochen)", "Chronisch (> 6 Wochen)", "Rezidiv"].index(
                    st.session_state.anamnese_data.get("schmerz_dauer", "Akut (< 1 Woche)")
                ) if st.session_state.anamnese_data.get("schmerz_dauer") in ["Akut (< 1 Woche)", "Subakut (1–6 Wochen)", "Chronisch (> 6 Wochen)", "Rezidiv"] else 0
            )
    therapie_ziel = st.text_area(
        "Therapieziel",
        value=st.session_state.anamnese_data.get("therapie_ziel", ""),
        placeholder="z.B. Schmerzfreiheit beim Alltagsgehen...",
        height=60
    )
    st.markdown("---")

    st.markdown('<p class="text-lg font-medium text-slate-300 mb-4">Vorgeschichte</p>', unsafe_allow_html=True)
    unfall_op = st.multiselect(
        "Relevante Ereignisse",
        options=[
            "Keine",
            "Unfall (Sport)", "Unfall (Verkehr)", "Unfall (Arbeit)",
            "Operation (Knie)", "Operation (Hüfte)", "Operation (Rücken)",
            "Krankenhausaufenthalt"
        ],
        default=st.session_state.anamnese_data.get("unfall_op", ["Keine"])
    )
    unfall_details = ""
    if "Keine" not in unfall_op:
        unfall_details = st.text_area(
            "Details (Datum, Art, Verlauf)",
            value=st.session_state.anamnese_data.get("unfall_details", ""),
            height=60
        )
    chronisch = st.multiselect(
        "Chronische Erkrankungen",
        options=[
            "Keine",
            "Diabetes mellitus",
            "Herz-Kreislauf-Erkrankung",
            "Neurologische Erkrankung",
            "Arthritis/Gonarthrose",
            "Hüftarthrose",
            "Bandscheibenvorfall",
            "Osteoporose"
        ],
        default=st.session_state.anamnese_data.get("chronisch", ["Keine"])
    )
    st.markdown("---")

    st.markdown('<p class="text-lg font-medium text-slate-300 mb-4">Funktionsstatus</p>', unsafe_allow_html=True)
    gehfaehigkeit = st.select_slider(
        "Gehfähigkeit",
        options=[
            "Uneingeschränkt",
            "Leicht eingeschränkt",
            "Mittel eingeschränkt",
            "Stark eingeschränkt",
            "Mit Gehhilfe",
            "Nicht möglich"
        ],
        value=st.session_state.anamnese_data.get("gehfaehigkeit", "Uneingeschränkt")
    )
    hilfsmittel = st.multiselect(
        "Hilfsmittel",
        options=["Keine", "Einlage/Orthese", "Bandage", "Stock", "Krücken", "Rollator"],
        default=st.session_state.anamnese_data.get("hilfsmittel", ["Keine"])
    )
    beruf = st.text_input(
        "Beruf/Tätigkeit",
        value=st.session_state.anamnese_data.get("beruf", ""),
        placeholder="z.B. Bürojob, Pflegekraft..."
    )
    if "Keine Schmerzen" in schmerz_ort:
        schmerz_intensitaet = 0
        schmerz_dauer = ""
    st.markdown("---")

    submitted = st.form_submit_button("Speichern und weiter", type="primary", use_container_width=True)

    if submitted:
        if not patient_id:
            st.error("Bitte Patienten-ID eingeben!")
        elif not hauptbeschwerde:
            st.error("Bitte Hauptbeschwerde angeben!")
        else:
            schmerz_intensitaet = schmerz_intensitaet if "Keine Schmerzen" not in schmerz_ort else 0
            schmerz_dauer = schmerz_dauer if "Keine Schmerzen" not in schmerz_ort else ""
            unfall_details = unfall_details if "Keine" not in unfall_op else ""

            st.session_state.anamnese_data = {
                "patient_id": patient_id,
                "alter": alter,
                "geschlecht": geschlecht,
                "gewicht": gewicht,
                "groesse": groesse,
                "bmi": round(bmi, 1),
                "hauptbeschwerde": hauptbeschwerde,
                "schmerz_ort": schmerz_ort,
                "schmerz_intensitaet": schmerz_intensitaet,
                "schmerz_dauer": schmerz_dauer,
                "therapie_ziel": therapie_ziel,
                "unfall_op": unfall_op,
                "unfall_details": unfall_details,
                "chronisch": chronisch,
                "gehfaehigkeit": gehfaehigkeit,
                "hilfsmittel": hilfsmittel,
                "beruf": beruf,
                "timestamp": datetime.now().isoformat()
            }
            anamnese_dir = Path("data/processed")
            anamnese_dir.mkdir(parents=True, exist_ok=True)
            anamnese_file = anamnese_dir / f"anamnese_{patient_id}.json"
            with open(anamnese_file, "w", encoding="utf-8") as f:
                json.dump(st.session_state.anamnese_data, f, ensure_ascii=False, indent=2)
            st.success("Anamnese gespeichert!")
            st.switch_page("pages/1_Upload.py")

st.markdown("---")
st.markdown('<p class="text-slate-600 text-sm">Haile v0.1.0 | GDPR-konform — alle Daten werden lokal gespeichert</p>', unsafe_allow_html=True)
