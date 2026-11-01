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

## Schriften

Gesucht wird `MS Gothic` (Windows), `Hiragino Sans`/`Osaka` (macOS), `Noto Sans CJK JP` (Linux),
danach `DejaVu Sans Mono`, `Consolas`, `Menlo`. Ohne Katakana-Schrift wird ASCII verwendet.
Fedora: `sudo dnf install google-noto-sans-cjk-fonts`
