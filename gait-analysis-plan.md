# Ganganalyse-Tool für Physiotherapie-Praxis
## Technischer Entwicklungsplan

**Zielgruppe:** Physiotherapie-Praxis mit 100 Patienten/Woche  
**Entwicklungszeit:** 3-4 Monate (3 Phasen)  
**Compliance:** GDPR-konform (lokale Verarbeitung)

---

## Übersicht: Verbesserter 3-Phasen-Plan

### Phase 1: MVP (Woche 1-6)
**Ziel:** Funktionierender Prototyp mit Kernmetriken

| Woche | Meilenstein | Deliverable |
|-------|-------------|-------------|
| 1 | Setup & Research | Projektstruktur, YOLOv8-pose Evaluation |
| 2 | Grundlegende Pose-Estimation | Video → Keypoints Pipeline + **Physio-Feedback #1** |
| 3 | Metrik-Berechnung | Knie-Winkel, Schrittlänge, Becken-Rotation |
| 4 | One Euro Filter Integration | Zeitlich geglättete Daten |
| 5 | Streamlit UI | Upload, Visualisierung, einfacher Report |
| 6 | MVP Polish & Review | **Physio-Feedback #2**, Bugfixes |

**Key Changes vom Originalplan:**
- ✅ YOLOv8-pose statt MediaPipe (bessere Fuß-Keypoints)
- ✅ One Euro Filter statt Kalman (einfacher, besser für Biomechanik)
- ✅ Frühes Physio-Feedback (Woche 2 & 6)

---

### Phase 2: Präzision (Woche 7-14)
**Ziel:** Klinisch nutzbare Genauigkeit

| Woche | Meilenstein | Deliverable |
|-------|-------------|-------------|
| 7-8 | Structure-from-Motion | 3D-Rekonstruktion aus 2 sequentiellen Videos |
| 9-10 | Multi-Video Support | Kalibration via Boden-Marker (1m Tape) |
| 11-12 | Erweiterte Metriken | Doppelstandphase, Schwungphase-Symmetrie |
| 13-14 | Validierung & Training | Custom Training auf GaitRec/OU-ISIR Datensätzen |

**Key Changes:**
- ✅ Structure-from-Motion statt synchroner Dual-Kamera (weniger Hardware-Frickelei)
- ✅ Temporal smoothing bereits in Phase 1 (One Euro Filter)

---

### Phase 3: Arzt-Level Features (Woche 15-20)
**Ziel:** Clinical Decision Support Tool

| Woche | Meilenstein | Deliverable |
|-------|-------------|-------------|
| 15-16 | Zeit-Parameter | Schrittzyklus, Phasen-Prozent, Cadence |
| 17-18 | Raum-Parameter | Schrittweite, Base of Support, Schrittlänge-Vergleich |
| 19 | Dynamik & Vergleich | Becken-Beschleunigungsprofile, Links/Rechts-Symmetrie |
| 20 | Final Polish | PDF-Reports, Export-Funktionen, **Arzt-Validierung** |

---

## Systemarchitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Handy-Video  │  │ Handy-Video  │  │  Referenz    │           │
│  │   (sagittal) │  │  (frontal)   │  │  (optional)  │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
└─────────┼─────────────────┼─────────────────┼───────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    POSE ESTIMATION LAYER                         │
│                                                                  │
│   ┌──────────────────────────────────────────────────────┐      │
│   │              YOLOv8-pose / AlphaPose                  │      │
│   │         (33+ Keypoints, 30+ FPS)                      │      │
│   └────────────────────┬─────────────────────────────────┘      │
│                        │                                         │
│                        ▼                                         │
│   ┌──────────────────────────────────────────────────────┐      │
│   │            One Euro Filter (Temporal Smoothing)       │      │
│   │     fcmin=1.0, beta=0.007 (tuned for gait)            │      │
│   └────────────────────┬─────────────────────────────────┘      │
└────────────────────────┼────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   3D RECONSTRUCTION (Optional)                   │
│                                                                  │
│   ┌──────────────────────────────────────────────────────┐      │
│   │        Structure-from-Motion (SfM)                    │      │
│   │   OR Stereo-Approximation (2 Kameras)                 │      │
│   └────────────────────┬─────────────────────────────────┘      │
└────────────────────────┼────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     METRICS CALCULATION                          │
│                                                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│   │   Kinematic  │  │   Temporal   │  │   Spatial    │          │
│   │   Metrics    │  │   Metrics    │  │   Metrics    │          │
│   │              │  │              │  │              │          │
│   │ • Knee Angle │  │ • Step Cycle │  │ • Step Width │          │
│   │ • Hip Rot.   │  │ • Double Sup.│  │ • Stride Len │          │
│   │ • Ankle Flex │  │ • Swing %    │  │ • Base of Sup│          │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└──────────┼─────────────────┼─────────────────┼──────────────────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ANALYSIS & OUTPUT                             │
│                                                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│   │  Symmetry    │  │   Red Flag   │  │   Reports    │          │
│   │  Analysis    │  │   Detection  │  │              │          │
│   │              │  │              │  │ • JSON Export│          │
│   │ Left vs Right│  │ • Asymmetry  │  │ • PDF Report │          │
│   │ Deviation %  │  │ • Range Lim. │  │ • Heatmaps   │          │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└──────────┼─────────────────┼─────────────────┼──────────────────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                           │
│                                                                  │
│   ┌──────────────────────────────────────────────────────┐      │
│   │              Streamlit Web Interface                  │      │
│   │                                                      │      │
│   │  [Video Upload] → [Processing] → [Dashboard]         │      │
│   │                                                      │      │
│   │  Tabs: Overview | Timeline | Comparison | Export     │      │
│   └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack Empfehlungen

### Core Stack
| Komponente | Library | Begründung |
|------------|---------|------------|
| **Pose Estimation** | `ultralytics` (YOLOv8-pose) | Schnell, genau, gute Fuß-Keypoints, aktiv maintained |
| **Alternative** | `AlphaPose` | Noch präziser, aber komplexer Setup |
| **Video Processing** | `opencv-python` | Industriestandard, gut dokumentiert |
| **Numerik** | `numpy` + `scipy` | Für Winkelberechnungen, Filter |
| **Temporal Filter** | Custom One Euro | Einfacher als Kalman, besser tunable |
| **3D Reconstruction** | `pycolmap` oder `open3d` | SfM-Implementierungen |
| **UI Framework** | `streamlit` | Rapid prototyping, ideal für MVPs |
| **Visualization** | `plotly` + `matplotlib` | Interaktive Graphen, Heatmaps |
| **PDF Reports** | `reportlab` oder `weasyprint` | Professionelle Exporte |
| **Data Storage** | `sqlite` (local) | GDPR-konform, kein Server nötig |

### Optional/Fortgeschritten
| Komponente | Library | Nutzung |
|------------|---------|---------|
| **Custom Training** | `pytorch` + `ultralytics` | Fine-tuning auf Gait-Daten |
| **Biomechanik** | `biomech` (falls verfügbar) | Oder eigene Implementierung |
| **Tests** | `pytest` | Unit tests für Metrik-Berechnungen |

---

## MVP Spezifikation (Woche 1-6 Detailplan)

### Woche 1: Setup & Research
**Tasks:**
- [ ] Projektstruktur anlegen (`src/`, `tests/`, `data/`, `models/`)
- [ ] Python Environment (Python 3.10+, virtualenv/poetry)
- [ ] YOLOv8-pose installieren & testen (`pip install ultralytics`)
- [ ] Test-Videos aufnehmen (mindestens 5 verschiedene Gänge)
- [ ] Vergleich: YOLOv8 vs. MediaPipe vs. AlphaPose (Speed/Accuracy)

**Deliverable:**
- Repository-Setup
- Benchmark-Ergebnisse im `docs/benchmark.md`

### Woche 2: Grundlegende Pose-Estimation
**Tasks:**
- [ ] Video-Loader mit OpenCV (Frame-by-frame)
- [ ] YOLOv8-pose Integration (Inference pro Frame)
- [ ] Keypoint-Extraktion (33 Punkte → relevante Gelenke filtern)
- [ ] JSON-Export der Rohdaten (Frame-Nummer → Keypoints)
- [ ] **PHYSIO-FEEDBACK #1:** Zeige Rohdaten, frage nach Relevanz

**Deliverable:**
- `python -m gait_analyzer.process_video input.mp4 --output raw_keypoints.json`

### Woche 3: Metrik-Berechnung
**Tasks:**
- [ ] Winkelberechnung (Knie, Hüfte, Knöchel)
- [ ] Schrittdetektion (Heel-Strike, Toe-Off via Keypoint-Geschwindigkeit)
- [ ] Schrittlängen-Berechnung (Pixel → cm via Referenz)
- [ ] Becken-Rotation (Yaw-Winkel aus Hüft-Keypoints)

**Formeln:**
```python
# Knie-Winkel (3-Punkt-Winkel)
knee_angle = angle(hip, knee, ankle)

# Schrittdetektion
heel_strike = detect_local_minima(heel_y_velocity)
toe_off = detect_local_maxima(toe_y_velocity)

# Becken-Rotation (approximiert aus 2D)
pelvis_rotation = atan2(right_hip.y - left_hip.y, right_hip.x - left_hip.x)
```

**Deliverable:**
- `metrics_calculator.py` mit allen Kernfunktionen
- Unit tests für Winkelberechnungen

### Woche 4: One Euro Filter Integration
**Tasks:**
- [ ] One Euro Filter implementieren (oder `filterpy` verwenden)
- [ ] Parameter-Tuning für Ganganalyse:
  - `freq = 30` (FPS)
  - `mincutoff = 1.0` (minimaler Rauschfilter)
  - `beta = 0.007` (Geschwindigkeitsabhängige Anpassung)
- [ ] Vorher/Nachher-Vergleich visualisieren

**One Euro Filter Pseudocode:**
```python
class OneEuroFilter:
    def __init__(self, freq, mincutoff=1.0, beta=0.007, dcutoff=1.0):
        self.freq = freq
        self.mincutoff = mincutoff
        self.beta = beta
        self.dcutoff = dcutoff
        self.x_prev = None
        self.dx_prev = None
    
    def filter(self, x, t=None):
        # Low-pass filter on signal
        # Adaptive cutoff based on rate of change
        ...
```

**Deliverable:**
- Geglättete Metriken in JSON
- Visualisierung: Rohe vs. gefilterte Daten

### Woche 5: Streamlit UI
**Tasks:**
- [ ] Multi-page Streamlit App strukturieren
- [ ] Upload-Seite (Video + Patient-ID)
- [ ] Verarbeitungs-Seite (Progress bar, Status)
- [ ] Dashboard-Seite:
  - Zeitlicher Verlauf der Winkel
  - Schritt-Detection Visualisierung
  - Einfache Statistiken (Min/Max/Avg pro Winkel)

**Streamlit Pages:**
```
gait_analyzer/
├── app/
│   ├── 01_Upload.py
│   ├── 02_Processing.py
│   └── 03_Dashboard.py
```

**Deliverable:**
- `streamlit run app/01_Upload.py`
- Demo-fähige UI

### Woche 6: MVP Polish & Review
**Tasks:**
- [ ] Fehlerbehandlung (korrupte Videos, zu dunkel, etc.)
- [ ] Performance-Optimierung (Batch-Verarbeitung?)
- [ ] Dokumentation (README, Installation)
- [ ] **PHYSIO-FEEDBACK #2:** Usability-Test mit echten Daten
- [ ] Bugfixes aus Feedback

**Deliverable:**
- MVP Release v0.1.0
- Physio-Validierungsbericht

---

## Deployment-Strategie

### Option A: Lokale Installation (Empfohlen für MVP)
**Setup:**
```bash
# Auf Physio-Praxis Laptop/PC
python -m venv gait_env
source gait_env/bin/activate  # Windows: gait_env\Scripts\activate
pip install -r requirements.txt
streamlit run app/01_Upload.py
```

**Vorteile:**
- ✅ 100% GDPR-konform (keine Daten verlassen den PC)
- ✅ Keine Internetverbindung nötig
- ✅ Keine laufenden Kosten

**Nachteile:**
- ❌ Manuelles Update nötig
- ❌ Nur auf einem Gerät nutzbar

### Option B: On-Premise Server (Ab Phase 2)
**Setup:**
- Kleiner PC/Raspberry Pi 5 im Praxis-Netzwerk
- Docker-Container mit der App
- Zugriff via Browser im lokalen Netz

**Vorteile:**
- ✅ Zentralisiertes System
- ✅ Mehrere Therapeuten können gleichzeitig arbeiten
- ✅ Einfacheres Backup

**Nachteile:**
- ❌ Initialer Hardware-Kauf (~300-500€)
- ❌ Netzwerk-Setup nötig

### Option C: Hybrid (Langfristig)
- Verarbeitung: Lokal (GDPR)
- Berichte: Sync zu verschlüsseltem Cloud-Storage (optional)

---

## GDPR Compliance Checklist

### ✅ Muss (Kritisch)
- [ ] **Lokale Verarbeitung:** Keine Videodaten an externe APIs
- [ ] **Patienteneinwilligung:** Digitale Unterschrift vor erster Analyse
- [ ] **Datenminimierung:** Nur notwendige Metadaten speichern
- [ ] **Zugriffskontrolle:** Login-System (ab Phase 2)
- [ ] **Löschfristen:** Automatisches Löschen nach X Jahren

### ✅ Sollte (Empfohlen)
- [ ] **Verschlüsselung:** Ruhende Daten verschlüsseln (SQLite encryption)
- [ ] **Audit-Log:** Wer hat wann auf welche Daten zugegriffen?
- [ ] **Pseudonymisierung:** Patienten-ID statt Name in Datenbank
- [ ] **Backup-Strategie:** Verschlüsselte Backups, getrennt vom Hauptsystem

### ✅ Dokumentation (Für Behörden)
- [ ] **Verzeichnis von Verarbeitungstätigkeiten:** Was wird warum gespeichert?
- [ ] **Technische und organisatorische Maßnahmen (TOM):** Sicherheitskonzept
- [ ] **Datenschutz-Folgenabschätzung:** Falls hochriskant (wahrscheinlich nicht nötig)

---

## Empfohlene Dateistruktur

```
gait-analyzer/
├── README.md                    # Projektübersicht, Installation
├── LICENSE                      # MIT oder proprietär
├── requirements.txt             # Python Dependencies
├── pyproject.toml              # Moderne Alternative zu requirements.txt
├── .gitignore                  # Nicht committen: Videos, Modelle, DBs
├── docs/
│   ├── architecture.md         # Dieser Plan
│   ├── gdpr_compliance.md      # DSGVO-Dokumentation
│   ├── user_manual.md          # Für Physios
│   └── benchmark.md            # Performance-Vergleiche
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── video_loader.py     # OpenCV Video I/O
│   │   ├── pose_estimator.py   # YOLOv8-pose Wrapper
│   │   ├── filtering.py        # One Euro Filter
│   │   └── metrics.py          # Alle Berechnungen
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── symmetry.py         # Links/Rechts-Vergleich
│   │   ├── red_flags.py        # Abnormalitäts-Detektion
│   │   └── report_generator.py # PDF/JSON Export
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── geometry.py         # Winkel-, Distanzberechnungen
│   │   ├── visualization.py    # Plotting-Helper
│   │   └── calibration.py      # Pixel-zu-cm Konvertierung
│   └── database/
│       ├── __init__.py
│       ├── models.py           # SQLite Schema
│       └── patient_repo.py     # CRUD Operationen
├── app/
│   ├── __init__.py
│   ├── 01_Upload.py            # Streamlit: Video Upload
│   ├── 02_Processing.py        # Streamlit: Verarbeitung
│   ├── 03_Dashboard.py         # Streamlit: Ergebnisse
│   └── components/
│       ├── __init__.py
│       ├── video_player.py     # Custom Streamlit-Komponente
│       └── metric_cards.py     # UI-Elemente
├── tests/
│   ├── __init__.py
│   ├── test_metrics.py         # Unit tests für Berechnungen
│   ├── test_filtering.py       # One Euro Filter tests
│   └── fixtures/
│       └── sample_keypoints.json  # Testdaten
├── data/
│   ├── raw/                    # Rohvideos (nicht im Git!)
│   ├── processed/              # JSON-Keypoints
│   └── reference/              # Kalibrationsdaten
├── models/
│   └── yolov8n-pose.pt         # Heruntergeladenes Modell
└── scripts/
    ├── setup.sh                # Einmaliges Setup
    ├── download_models.py      # YOLOv8 Modelle laden
    └── benchmark.py            # Performance-Tests
```

---

## Nächste Schritte

1. **Jetzt:** Repository initialisieren, Week 1 Tasks starten
2. **Woche 2:** Erstes Physio-Feedback einholen
3. **Woche 6:** MVP validieren, entscheiden ob Phase 2 & 3
4. **Kontinuierlich:** GDPR-Dokumentation pflegen

---

**Status:** Plan v1.0 fertig  
**Autor:** Neil 🤖  
**Letzte Aktualisierung:** 2026-03-04
