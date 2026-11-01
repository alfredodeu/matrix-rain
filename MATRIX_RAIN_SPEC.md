# Matrix Rain – Bauauftrag für Claude Code

> **Anleitung:** Diese Datei in einen leeren Projektordner legen, dort `claude` starten und eingeben:
> `Lies MATRIX_RAIN_SPEC.md und setze das Projekt vollständig um.`

---

## 1. Ziel

Ein originalgetreuer „Matrix Digital Rain“-Bildschirmeffekt in **Python + Pygame**,
lauffähig auf **Windows, macOS und Linux (Fedora)**. Er startet im Vollbild,
läuft flüssig und lässt sich sauber beenden.

## 2. Ausgangscode (Referenz)

```python
import pygame, random

pygame.init()
win = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
W, H = win.get_size()
font = pygame.font.SysFont("courier", 30, bold=True)

cols = W // 30
drops = [random.randint(-40, 0) for _ in range(cols)]
fade = pygame.Surface((W, H))
fade.set_alpha(35)

while True:
    for e in pygame.event.get():
        if e.type == pygame.KEYDOWN:
            raise SystemExit
    win.blit(fade, (0, 0))
    for i, y in enumerate(drops):
        c = random.choice("01ABCXYZ$#*")
        img = font.render(c, 1, "lime")
        win.blit(img, (i * 30, y * 30))
        bottom = y * 30 > H
        if bottom and random.random() > .97:
            drops[i] = 0
        else:
            drops[i] += 1
    pygame.display.flip()
    pygame.time.wait(50)
```

## 3. Anforderungen

### 3.1 Projektstruktur
```
matrix-rain/
├── matrix_rain.py        # Hauptprogramm (eine Datei, gut kommentiert)
├── requirements.txt      # pygame-ce>=2.4
├── start_windows.bat     # Doppelklick-Start Windows (legt venv an)
├── start_unix.sh         # Start macOS/Linux (legt venv an, chmod +x)
└── README.md             # Kurzanleitung Deutsch
```

### 3.2 Visuelle Qualität
- **Kopfzeichen weiß/hellgrün**, die Spur darunter in abgestuftem Grün (`#00FF41` → dunkel).
- **Halbbreite Katakana** (U+FF66–U+FF9D) gemischt mit Ziffern 0–9 und einigen Symbolen
  wie im Film. Falls keine Schrift mit Katakana gefunden wird, automatisch auf ASCII zurückfallen.
- Zeichen in der Spur **wechseln gelegentlich zufällig** (Flackern) statt still zu bleiben.
- **Unterschiedliche Fallgeschwindigkeit** pro Spalte (z. B. 0,5–1,5 Zellen pro Frame).
- Einige Zeichen spiegeln (`pygame.transform.flip`) wie im Original.
- Fade-Effekt über eine schwarze Fläche mit Alpha (konfigurierbar).

### 3.3 Technik
- `pygame-ce` verwenden (gleiche API, aktiver gepflegt), kompatibel zu normalem `pygame`.
- `pygame.time.Clock().tick(FPS)` statt `time.wait`.
- **Glyphen-Cache:** gerenderte Zeichen pro Farbe vorab in ein Dict cachen, kein `font.render` pro Frame.
- Schriftsuche plattformunabhängig, in dieser Reihenfolge:
  `MS Gothic` (Win), `Hiragino Sans` / `Osaka` (Mac), `Noto Sans CJK JP` / `Noto Sans Mono CJK JP` (Linux),
  dann `DejaVu Sans Mono`, `Consolas`, `Menlo`, `monospace`.
- HiDPI berücksichtigen (Windows: `ctypes.windll.shcore.SetProcessDpiAwareness(1)` in try/except).
- Mauszeiger im Vollbild ausblenden.
- Bei 4K-Monitoren stabile **60 FPS** (Zielwert, mindestens 30).

### 3.4 Bedienung
| Taste | Funktion |
|---|---|
| `ESC` / `Q` / Fenster schließen | Beenden |
| `Leertaste` | Pause / Weiter |
| `F` | Vollbild ↔ Fenster (1280×720) |
| `+` / `-` | Geschwindigkeit ändern |
| `C` | Farbschema wechseln: Grün → Cyan → Rot → Gold |
| `H` | Hilfe-Overlay ein/aus (unten links, halbtransparent) |

Andere Tasten beenden das Programm **nicht** (Unterschied zum Ausgangscode).

### 3.5 Kommandozeile (argparse)
```
python matrix_rain.py [--windowed] [--fps 60] [--size 20] [--color green]
                      [--speed 1.0] [--ascii] [--screensaver]
```
- `--screensaver`: jede Taste und jede Mausbewegung beendet das Programm (klassischer Bildschirmschoner-Modus).
- Konfigurationswerte oben in der Datei als Konstanten (`DEFAULTS`).

## 4. Startskripte

**start_windows.bat**
- Prüft, ob `py` oder `python` vorhanden ist, sonst Hinweis auf python.org.
- Legt `.venv` an, installiert `requirements.txt` und startet das Programm.

**start_unix.sh**
- `python3 -m venv .venv`, aktivieren, `pip install -r requirements.txt`, starten.
- Auf Fedora Hinweis bei fehlender Schrift: `sudo dnf install google-noto-sans-cjk-fonts`.

## 5. Abnahmekriterien

- [ ] `python matrix_rain.py --windowed` startet ohne Fehler und ohne Warnung.
- [ ] ESC beendet sauber (kein Traceback, `pygame.quit()` wird aufgerufen).
- [ ] Ohne Katakana-Schrift läuft es mit ASCII weiter (Hinweis auf der Konsole).
- [ ] CPU-Last im Leerlauf deutlich unter einem Kern (Glyphen-Cache aktiv).
- [ ] Code mit Typ-Hints, in Funktionen/Klassen gegliedert (`Column`, `MatrixRain`), deutsche Kommentare.
- [ ] Ein headless Smoke-Test (`SDL_VIDEODRIVER=dummy`) läuft 100 Frames ohne Fehler:
      `python matrix_rain.py --test-frames 100`.

## 6. Vorgehen für Claude Code

1. Struktur anlegen und `requirements.txt` schreiben.
2. `matrix_rain.py` implementieren.
3. venv anlegen, Abhängigkeiten installieren, Smoke-Test ausführen.
4. Startskripte und README schreiben.
5. Abnahmekriterien abhaken und kurz berichten, was getestet wurde.

Optional zum Schluss: `git init` und ersten Commit anlegen.
