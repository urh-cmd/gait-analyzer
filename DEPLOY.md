# 🚀 Gait Analyzer – Deployment-Anleitung

## ⚠️ Wichtiger Hinweis (GDPR)

Der Entwicklungsplan empfiehlt **lokale Verarbeitung** für Patientendaten. Eine Cloud-Veröffentlichung bedeutet:

- **Patientenvideos** werden auf Servern von Drittanbietern verarbeitet
- **Datenschutz** – prüfe, ob deine Nutzung mit DSGVO konform ist
- Für **Demos oder Schulungen** ohne echte Patientendaten ist Cloud-Deployment unkritisch

---

## Option 1: Streamlit Community Cloud (empfohlen, kostenlos)

### Voraussetzungen
- GitHub-Account
- Repository mit dem Code

### Schritt 1: GitHub-Repository erstellen

```powershell
cd c:\Users\Nutzer\.clawdbot\workspace

# Falls noch nicht initialisiert:
# git init

# Alle Änderungen committen
git add .
git commit -m "Gait Analyzer – Deployment-Version"

# Neues Repo auf github.com erstellen, dann:
git remote add origin https://github.com/DEIN_USERNAME/gait-analyzer.git
git branch -M main
git push -u origin main
```

### Schritt 2: Auf Streamlit Community Cloud deployen

1. Gehe zu **https://share.streamlit.io**
2. Melde dich mit GitHub an
3. Klicke **"Create app"** / **"Neue App erstellen"**
4. Einstellungen:
   - **Repository:** `DEIN_USERNAME/gait-analyzer`
   - **Branch:** `main`
   - **Main file path:** `Home.py`
5. **Advanced settings** (optional):
   - **Python version:** 3.10 oder 3.11
6. **Deploy** klicken

### Schritt 3: Warten

Der erste Build kann **5–15 Minuten** dauern (ultralytics, opencv). YOLOv8 wird beim ersten Lauf automatisch heruntergeladen.

---

## Option 2: Hugging Face Spaces

1. Gehe zu **https://huggingface.co/spaces**
2. **Create new Space**
3. **SDK:** Streamlit
4. Repo clonen und Code einfügen
5. `requirements.txt` im Root hinzufügen

---

## Dateien im Repo

| Datei | Zweck |
|-------|-------|
| `Home.py` | Einstiegspunkt der App |
| `requirements.txt` | Python-Abhängigkeiten |
| `packages.txt` | Linux-Systempakete (OpenCV) |
| `pages/` | Multipage-Seiten |
| `app/`, `src/` | App-Logik |

---

## Bekannte Einschränkungen (Community Cloud)

- **Speicher:** Hochgeladene Videos sind ephemeral (verloren beim App-Sleep)
- **CPU:** Limitierter Rechenzeit pro Request
- **Cold Start:** App kann nach Inaktivität 1–2 Minuten brauchen
- **Video-Länge:** Sehr lange Videos (>2 Min) können Timeouts verursachen

---

## Fehlerbehebung

### Build schlägt fehl
- `packages.txt` prüfen (libgl1-mesa-glx für OpenCV)
- `requirements.txt` – Versionen evtl. locken

### "ModuleNotFoundError"
- Fehlende Abhängigkeit in `requirements.txt` ergänzen

### Video spielt nicht ab
- Kurze Testvideos verwenden
- Codec H.264 (bereits implementiert)

---

**Viel Erfolg! 🚶**
