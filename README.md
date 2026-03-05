# 🎬 Gait Analyzer

**KI-basierte Ganganalyse für Physiotherapie-Praxen**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

> **Deployment:** Siehe [DEPLOY.md](DEPLOY.md) für die Veröffentlichung auf Streamlit Community Cloud.

## 🚀 Features

- 📹 **Video-Upload** mit automatischer Pose-Estimation (YOLOv8)
- 🦴 **17 Keypoints** erkannt (COCO Format)
- 📊 **Professionelle Analyse**: Cadenz, Symmetrie, Schrittlängen
- 📄 **PDF-Reports** für Ärzte
- 🔒 **100% GDPR-konform** - alle Daten lokal verarbeitet

## 📖 Nutzung

1. Video hochladen (MP4, AVI, MOV)
2. YOLOv8-pose verarbeitet automatisch
3. Analyse-Dashboard öffnet sich
4. PDF-Report erstellen & herunterladen

## 🛠️ Tech Stack

- **Python 3.10+**
- **Streamlit** - Web Interface
- **YOLOv8** - Pose Estimation
- **OpenCV** - Video Processing
- **Plotly** - Visualisierungen
- **ReportLab** - PDF Reports

## 🏥 Für Physiotherapeuten

Dieses Tool hilft bei:
- Objektiver Gangbewertung
- Verlaufskontrolle über Zeit
- Dokumentation für Krankenkassen
- Früherkennung von Abweichungen

## ⚠️ Hinweis

Alle Videodaten werden **lokal verarbeitet** und nicht an externe Server gesendet. GDPR-konform für Praxen.

---

**Made with ❤️ for better patient care**
