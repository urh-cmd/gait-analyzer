# 🎬 Pose Video Player

**Stand-Alone HTML Player für Gait Analyzer**

## 🚀 Verwendung

### Option 1: Direkt im Browser öffnen
1. Öffne `app/pose-player.html` in deinem Browser (Doppelklick oder Drag & Drop)
2. Wähle dein **Video** (MP4, AVI, MOV)
3. Wähle die **Keypoints JSON** Datei aus `data/processed/`
4. Klicke **"▶️ Player starten"**
5. **Abspielen!** 🎉

### Option 2: Über Streamlit Dashboard
1. Streamlit App öffnen: `http://localhost:8501`
2. Zu **"🎬 Video mit Pose"** Tab gehen
3. Auf **"🎬 Pose Video Player öffnen"** klicken

## ✨ Features

- **🎥 Echtes Video-Playback** – Native Browser-Wiedergabe
- **🦴 Synchrones Pose-Overlay** – Keypoints + Skeleton direkt im Video
- **⏯️ Vollständige Controls** – Play, Pause, Seek, Speed (0.25x - 4x)
- **🎨 Anpassbar** – Confidence Filter, Skeleton/Keypoints ein/aus
- **⚡ Smooth 60 FPS** – Kein Ruckeln, kein Flackern
- **🔒 Lokal** – Alle Daten bleiben auf deinem PC

## 📁 Benötigte Dateien

- **Video:** `data/raw/*.mp4` (oder anderes Video-Format)
- **Keypoints:** `data/processed/*_keypoints.json`

## 🎮 Steuerung

| Button | Funktion |
|--------|----------|
| ⏮️ Start | Zum Anfang springen |
| ⏮️ -10s / -1s | Zurück spulen |
| ▶️ / ⏸️ | Abspielen / Pause |
| ⏭️ +1s / +10s | Vor spulen |
| 🐌 / 🚀 | Geschwindigkeit reduzieren/erhöhen |
| Progress Bar | Direktes Springen im Video |
| Confidence Slider | Filtert Keypoints nach Genauigkeit |

## 🎨 Farbcodierung

- **🔴 Rot** – Kopf (Nase, Augen, Ohren)
- **🟡 Gelb** – Schultern, Hüften
- **🟢 Grün** – Linke Körperseite (Arm, Bein)
- **🟣 Lila** – Rechte Körperseite (Arm, Bein)
- **Keypoint Farben:**
  - 🟢 Grün = Hohe Confidence (>0.8)
  - 🟡 Gelb = Mittlere Confidence (>0.5)
  - 🔴 Rot = Niedrige Confidence (<0.5)

---

**Viel Spaß beim Analysieren!** 🚶‍♂️📊
