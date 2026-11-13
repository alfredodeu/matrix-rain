# Matrix Rain

„Matrix Digital Rain“ als Bildschirmeffekt in Python + Pygame (pygame-ce) für Windows, macOS und Linux.

## Start

- **Windows:** Doppelklick auf `start_windows.bat`
- **macOS / Linux:** `./start_unix.sh` (ggf. vorher `chmod +x start_unix.sh`)

Beim ersten Start wird automatisch `.venv` angelegt und `pygame-ce` installiert.
Manuell: `pip install -r requirements.txt` und `python matrix_rain.py`.

## Bedienung

| Taste | Funktion |
|---|---|
| `ESC` / `Q` | Beenden |
| `Leertaste` | Pause / Weiter |
| `F` | Vollbild ↔ Fenster (1280×720) |
| `+` / `-` | Geschwindigkeit |
| `C` | Farbschema: Grün → Cyan → Rot → Gold |
| `H` | Hilfe-Overlay |

## Optionen

```
python matrix_rain.py [--windowed] [--fps 60] [--size 20] [--color green]
                      [--speed 1.0] [--ascii] [--screensaver] [--test-frames N]
```

- `--screensaver`: jede Taste / Mausbewegung beendet das Programm.
- `--ascii`: nur ASCII-Zeichen statt Katakana.
- `--test-frames N`: headless Smoke-Test (N Frames, kein Fenster).
- Weitere Einstellungen (Fade, Spurlänge, Flackern …) stehen oben in `matrix_rain.py` in `DEFAULTS`.

## iPad / iPhone / Browser (Web-Version)

Im Ordner `web/` liegt eine Browser-Version (HTML5-Canvas, ohne Installation).
Sie läuft auf iPad, iPhone, Mac, Windows und Linux.

**Auf das iPad bringen:** Die Seite muss über `https://` erreichbar sein, z. B. über **GitHub Pages**
(Repo → Settings → Pages → Branch wählen, Ordner `/ (root)`), dann
`https://<benutzer>.github.io/matrix-rain/web/` in Safari öffnen.
Danach **Teilen → „Zum Home-Bildschirm“**. So startet sie wie eine App im Vollbild und läuft auch offline.

Lokal testen: `cd web && python3 -m http.server 8000` und `http://localhost:8000` öffnen
(oder `index.html` einfach im Browser öffnen).

| Touch | Taste | Funktion |
|---|---|---|
| Tippen | `Leertaste` | Pause / Weiter |
| Doppelt tippen | `C` | Farbschema |
| Hoch / runter wischen | `+` / `-` | Geschwindigkeit |
| Lange drücken | `H` | Hilfe (mit Knöpfen inkl. Vollbild) |
| – | `F` | Vollbild |

URL-Parameter: `?color=cyan&speed=1.2&size=24&fps=30&ascii=1`.
Farbe und Tempo werden im Browser gespeichert.
Der Bildschirm bleibt an, solange die Seite offen ist (Wake Lock, ab iPadOS 16.4).
Falls nicht: Einstellungen → Anzeige & Helligkeit → Automatische Sperre → Nie.

## Schriften

Gesucht wird `MS Gothic` (Windows), `Hiragino Sans`/`Osaka` (macOS), `Noto Sans CJK JP` (Linux),
danach `DejaVu Sans Mono`, `Consolas`, `Menlo`. Ohne Katakana-Schrift wird ASCII verwendet.
Fedora: `sudo dnf install google-noto-sans-cjk-fonts`
