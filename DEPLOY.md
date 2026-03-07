# Haile auf Streamlit Cloud veröffentlichen

## 1. Git-Identität setzen (falls noch nicht geschehen)

```powershell
git config --global user.email "deine@email.de"
git config --global user.name "Dein Name"
```

## 2. Änderungen pushen

Die Änderungen sind bereits gestaged. Führe aus:

```powershell
cd "C:\Users\Nutzer\.openclaw\workspace"

git commit -m "Haile UI: Bewegungsanalyse mit linear_ui, Streamlit-Sidebar, neue Seiten"
git push origin main
```

## 3. App auf Streamlit Community Cloud deployen

1. Gehe zu **[share.streamlit.io](https://share.streamlit.io)**
2. Melde dich mit GitHub an
3. Klicke auf **Create app**
4. Wähle **„Yup, I have an app.“**
5. Trage ein:
   - **Repository:** `urh-cmd/gait-analyzer`
   - **Branch:** `main`
   - **Main file path:** `Home.py`
6. Optional: **Custom subdomain** (z.B. `haile-bewegungsanalyse`)
7. Klicke auf **Deploy**

## Wichtige Hinweise

- **yolov8n-pose.pt:** Ultralytics lädt das Modell beim ersten Lauf automatisch herunter.
- **Secrets:** Wenn du API-Keys brauchst, unter „Advanced settings“ → Secrets einfügen (TOML-Format wie in `.streamlit/secrets.toml`).
- Nach dem Push aktualisiert sich die App automatisch bei neuen Commits.
