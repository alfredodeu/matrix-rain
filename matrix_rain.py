#!/usr/bin/env python3
"""Matrix Digital Rain – Bildschirmeffekt in Python + Pygame (pygame-ce).

Läuft unter Windows, macOS und Linux. Start:
    python matrix_rain.py [--windowed] [--fps 60] [--size 20] [--color green]
                          [--speed 1.0] [--ascii] [--screensaver]

Tasten: ESC/Q beenden, Leertaste Pause, F Vollbild/Fenster, +/- Tempo,
        C Farbschema, H Hilfe.
"""
from __future__ import annotations

import argparse
import os
import random
import sys

# Pygame-Willkommensmeldung unterdrücken (muss VOR dem Import gesetzt werden).
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

# --------------------------------------------------------------------------
# Konfiguration
# --------------------------------------------------------------------------
DEFAULTS: dict = {
    "fps": 60,                 # Ziel-Bildrate
    "size": 20,                # Schriftgröße in Pixeln (= Zeilenhöhe)
    "color": "green",          # Startfarbschema
    "speed": 1.0,              # globaler Geschwindigkeitsfaktor
    "fade_alpha": 70,          # Deckkraft der schwarzen Fade-Fläche (0–255)
    "window_size": (1280, 720),
    "trail_min": 8,            # Spurlänge in Zeichen (min/max)
    "trail_max": 32,
    "col_speed_min": 0.35,     # Zellen pro Frame bei 30 FPS (Referenz)
    "col_speed_max": 1.05,
    "flicker_chance": 0.12,    # Wahrscheinlichkeit pro Spalte und Frame
    "flip_chance": 0.15,       # Anteil gespiegelter Zeichen
    "levels": 14,              # Helligkeitsstufen (0 = Kopf, Rest = Spur)
}

REFERENCE_FPS = 30.0          # Geschwindigkeiten sind auf diese Rate normiert

# Farbschemata: Grundfarbe der Spur (RGB)
SCHEMES: dict[str, tuple[int, int, int]] = {
    "green": (0, 255, 65),     # #00FF41
    "cyan": (0, 240, 255),
    "red": (255, 40, 40),
    "gold": (255, 200, 40),
}
SCHEME_ORDER = ["green", "cyan", "red", "gold"]

# Schriftsuche in der geforderten Reihenfolge (pygame normalisiert die Namen)
FONT_CANDIDATES = [
    "msgothic", "ms gothic",                                  # Windows
    "hiraginosans", "hiragino sans", "osaka",                 # macOS
    "notosanscjkjp", "noto sans cjk jp",                      # Linux
    "notosansmonocjkjp", "noto sans mono cjk jp",
    "dejavusansmono", "dejavu sans mono",
    "consolas", "menlo", "monospace",
]

KATAKANA = [chr(c) for c in range(0xFF66, 0xFF9E)]  # halbbreite Katakana
DIGITS = list("0123456789")
SYMBOLS_KANA = list(":.=*+-<>|")
CHARS_ASCII = list("0123456789ABCXYZ$#*+=<>:")


# --------------------------------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------------------------------
def enable_dpi_awareness() -> None:
    """Windows: echte Monitorauflösung nutzen (HiDPI), sonst wird skaliert."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore[attr-defined]
    except Exception:
        pass  # andere Plattformen / ältere Windows-Versionen


def supports_chars(font: pygame.font.Font, chars: list[str]) -> list[str]:
    """Gibt die Zeichen zurück, für die die Schrift tatsächlich ein Glyph hat."""
    ok = []
    for ch in chars:
        try:
            if font.metrics(ch)[0] is not None:
                ok.append(ch)
        except pygame.error:
            pass
    return ok


def pick_font(size: int, force_ascii: bool) -> tuple[pygame.font.Font, list[str]]:
    """Wählt die erste passende Schrift und den dazugehörigen Zeichensatz.

    Bevorzugt eine Schrift mit Katakana; gibt es keine, wird auf ASCII
    zurückgefallen (mit Hinweis auf der Konsole).
    """
    first_font: pygame.font.Font | None = None
    for name in FONT_CANDIDATES:
        path = pygame.font.match_font(name, bold=True) or pygame.font.match_font(name)
        if not path:
            continue
        try:
            font = pygame.font.Font(path, size)
        except (pygame.error, OSError):
            continue
        first_font = first_font or font
        if force_ascii:
            return font, CHARS_ASCII
        kana = supports_chars(font, KATAKANA)
        if len(kana) >= 40:  # praktisch der komplette Block
            return font, kana + DIGITS + supports_chars(font, SYMBOLS_KANA)
    # Keine Katakana-Schrift gefunden
    if not force_ascii:
        print("Hinweis: Keine Schrift mit Katakana gefunden – nutze ASCII-Zeichen.\n"
              "         Fedora: sudo dnf install google-noto-sans-cjk-fonts")
    return first_font or pygame.font.Font(None, size + 6), CHARS_ASCII


def mix(color: tuple[int, int, int], other: tuple[int, int, int], t: float
        ) -> tuple[int, int, int]:
    """Lineare Farbmischung (t=0 → color, t=1 → other)."""
    return (int(color[0] + (other[0] - color[0]) * t),
            int(color[1] + (other[1] - color[1]) * t),
            int(color[2] + (other[2] - color[2]) * t))


def level_colors(base: tuple[int, int, int], levels: int) -> list[tuple[int, int, int]]:
    """Farbverlauf: Stufe 0 = fast weiß (Kopf), danach Grundfarbe → dunkel."""
    colors = [mix(base, (255, 255, 255), 0.85)]
    steps = levels - 1
    for i in range(steps):
        t = i / max(1, steps - 1)
        colors.append(mix(base, (0, 0, 0), 0.92 * t ** 1.3))
    return colors


# --------------------------------------------------------------------------
# Glyphen-Cache
# --------------------------------------------------------------------------
class GlyphCache:
    """Vorgerenderte Zeichen: glyphs[stufe][gespiegelt][zeichen-index]."""

    def __init__(self, font: pygame.font.Font, chars: list[str],
                 cell_w: int, cell_h: int, levels: int) -> None:
        self.font, self.chars = font, chars
        self.cell_w, self.cell_h, self.levels = cell_w, cell_h, levels
        self.glyphs: list[list[list[pygame.Surface]]] = []

    def build(self, base: tuple[int, int, int]) -> None:
        """Rendert alle Zeichen für ein Farbschema (einmalig, nicht pro Frame)."""
        self.glyphs = []
        for color in level_colors(base, self.levels):
            normal: list[pygame.Surface] = []
            flipped: list[pygame.Surface] = []
            for ch in self.chars:
                raw = self.font.render(ch, True, color)
                cell = pygame.Surface((self.cell_w, self.cell_h), pygame.SRCALPHA)
                # Zeichen in der Zelle zentrieren (zu breite Glyphen werden beschnitten)
                cell.blit(raw, ((self.cell_w - raw.get_width()) // 2,
                                (self.cell_h - raw.get_height()) // 2))
                cell = cell.convert_alpha()
                normal.append(cell)
                flipped.append(pygame.transform.flip(cell, True, False))
            self.glyphs.append([normal, flipped])


# --------------------------------------------------------------------------
# Spalte
# --------------------------------------------------------------------------
class Column:
    """Eine fallende Zeichenspur mit eigener Geschwindigkeit und Länge."""

    def __init__(self, x: int, rows: int, n_chars: int) -> None:
        self.x, self.rows, self.n_chars = x, rows, n_chars
        # Zeichen- und Spiegel-Zustand pro Zeile
        self.idx = [random.randrange(n_chars) for _ in range(rows)]
        self.flip = [random.random() < DEFAULTS["flip_chance"] for _ in range(rows)]
        self.head = 0.0
        self.speed = 1.0
        self.length = 10
        self.reset(initial=True)

    def reset(self, initial: bool = False) -> None:
        """Neue Spur oberhalb des Bildschirms starten (versetzt, damit es nicht synchron wirkt)."""
        self.speed = random.uniform(DEFAULTS["col_speed_min"], DEFAULTS["col_speed_max"])
        self.length = random.randint(DEFAULTS["trail_min"], DEFAULTS["trail_max"])
        spread = self.rows + self.length if initial else self.rows // 3
        self.head = -random.uniform(0, spread)

    def update(self, step: float) -> None:
        """Kopf bewegen, neue Zeichen im Kopf setzen, Spur flackern lassen."""
        old = int(self.head // 1)
        self.head += self.speed * step
        new = int(self.head // 1)
        for row in range(old + 1, new + 1):  # betretene Zeilen bekommen neue Zeichen
            if 0 <= row < self.rows:
                self.idx[row] = random.randrange(self.n_chars)
                self.flip[row] = random.random() < DEFAULTS["flip_chance"]
        if random.random() < DEFAULTS["flicker_chance"]:
            row = new - random.randrange(1, self.length + 1)
            if 0 <= row < self.rows:
                self.idx[row] = random.randrange(self.n_chars)
        if new - self.length > self.rows:  # Spur komplett unten raus
            self.reset()

    def draw(self, surface: pygame.Surface, cache: GlyphCache, cell_h: int) -> None:
        """Kopf und Spur mit abgestuften Helligkeiten zeichnen."""
        head_row = int(self.head // 1)
        last_level = cache.levels - 1
        for k in range(self.length):
            row = head_row - k
            if row < 0:
                break
            if row >= self.rows:
                continue
            level = 0 if k == 0 else 1 + (k * (last_level - 1)) // self.length
            surface.blit(cache.glyphs[level][self.flip[row]][self.idx[row]],
                         (self.x, row * cell_h))


# --------------------------------------------------------------------------
# Hauptprogramm-Klasse
# --------------------------------------------------------------------------
class MatrixRain:
    """Fenster, Eingaben, Hauptschleife."""

    HELP_LINES = [
        "ESC / Q   Beenden",
        "Leertaste Pause / Weiter",
        "F         Vollbild / Fenster",
        "+ / -     Geschwindigkeit",
        "C         Farbschema",
        "H         Hilfe ein/aus",
    ]

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.fullscreen = not args.windowed
        self.fps: int = args.fps
        self.speed: float = args.speed
        self.scheme_i = SCHEME_ORDER.index(args.color)
        self.paused = False
        self.show_help = False
        self.running = True
        self.start_ticks = 0
        self.under: tuple[pygame.Rect, pygame.Surface] | None = None  # Hintergrund unter Overlay

        pygame.display.init()
        pygame.font.init()
        pygame.display.set_caption("Matrix Rain")
        self.font, self.chars = pick_font(args.size, args.ascii)
        self.cell_h = args.size
        # Zellbreite aus der Schrift ableiten (halbbreite Zeichen sind schmal)
        self.cell_w = max(6, max(self.font.size(c)[0] for c in self.chars))
        self.cache = GlyphCache(self.font, self.chars, self.cell_w, self.cell_h,
                                DEFAULTS["levels"])
        self.help_font = pygame.font.Font(
            pygame.font.match_font("consolas,dejavusansmono,menlo,couriernew") or None, 16)
        self.clock = pygame.time.Clock()
        # Fenster zuerst öffnen: convert_alpha() im Cache braucht einen Display-Modus
        self.open_window()
        self.cache.build(SCHEMES[SCHEME_ORDER[self.scheme_i]])

    # -- Fenster / Layout ---------------------------------------------------
    def open_window(self) -> None:
        """(Neu) Fenster öffnen und Spalten an die Größe anpassen."""
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(DEFAULTS["window_size"])
        pygame.mouse.set_visible(not self.fullscreen)
        w, h = self.screen.get_size()
        self.rows = h // self.cell_h + 1
        n_cols = max(1, w // self.cell_w)
        margin = (w - n_cols * self.cell_w) // 2  # Spalten mittig ausrichten
        self.columns = [Column(margin + i * self.cell_w, self.rows, len(self.chars))
                        for i in range(n_cols)]
        self.fade = pygame.Surface((w, h)).convert()
        self.fade.fill((0, 0, 0))
        self.fade.set_alpha(DEFAULTS["fade_alpha"])
        self.screen.fill((0, 0, 0))
        self.under = None

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        self.open_window()

    # -- Eingaben -----------------------------------------------------------
    def handle_events(self) -> None:
        saver = self.args.screensaver
        # Direkt nach dem Start melden manche Systeme Schein-Mausbewegungen
        armed = pygame.time.get_ticks() - self.start_ticks > 1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if saver or e.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.running = False
                elif e.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif e.key == pygame.K_f:
                    self.toggle_fullscreen()
                elif e.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS) \
                        or e.unicode == "+":
                    self.speed = min(5.0, self.speed * 1.15)
                elif e.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.speed = max(0.1, self.speed / 1.15)
                elif e.key == pygame.K_c:
                    self.scheme_i = (self.scheme_i + 1) % len(SCHEME_ORDER)
                    self.cache.build(SCHEMES[SCHEME_ORDER[self.scheme_i]])
                elif e.key == pygame.K_h:
                    self.show_help = not self.show_help
            elif e.type == pygame.MOUSEMOTION and saver and armed:
                if abs(e.rel[0]) + abs(e.rel[1]) > 3:
                    self.running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and saver and armed:
                self.running = False

    # -- Zeichnen -----------------------------------------------------------
    def draw_help(self) -> None:
        """Halbtransparentes Hilfe-Overlay unten links; sichert den Hintergrund."""
        lines = self.HELP_LINES + [f"Tempo {self.speed:.2f}x  |  {SCHEME_ORDER[self.scheme_i]}"]
        line_h = self.help_font.get_linesize()
        w = max(self.help_font.size(t)[0] for t in lines) + 24
        h = line_h * len(lines) + 20
        rect = pygame.Rect(12, self.screen.get_height() - h - 12, w, h)
        self.under = (rect, self.screen.subsurface(rect).copy())
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((0, 0, 0, 170))
        self.screen.blit(panel, rect)
        color = SCHEMES[SCHEME_ORDER[self.scheme_i]]
        for i, text in enumerate(lines):
            self.screen.blit(self.help_font.render(text, True, color),
                             (rect.x + 12, rect.y + 10 + i * line_h))

    def frame(self, dt: float) -> None:
        """Ein Frame: Overlay entfernen, faden, Spalten bewegen/zeichnen, Overlay."""
        if self.under:  # altes Overlay rückgängig machen, damit es nicht einbrennt
            self.screen.blit(self.under[1], self.under[0])
            self.under = None
        if not self.paused:
            step = dt * REFERENCE_FPS * self.speed
            self.screen.blit(self.fade, (0, 0))
            for col in self.columns:
                col.update(step)
                col.draw(self.screen, self.cache, self.cell_h)
        if self.show_help:
            self.draw_help()
        pygame.display.flip()

    def run(self, max_frames: int = 0) -> int:
        """Hauptschleife; max_frames > 0 beendet nach so vielen Frames (Smoke-Test)."""
        frames = 0
        self.start_ticks = pygame.time.get_ticks()
        while self.running:
            dt = min(self.clock.tick(self.fps) / 1000.0, 0.1)  # Aussetzer deckeln
            self.handle_events()
            self.frame(dt)
            frames += 1
            if max_frames and frames >= max_frames:
                break
        return frames


# --------------------------------------------------------------------------
# Einstieg
# --------------------------------------------------------------------------
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Matrix Digital Rain (Pygame)")
    p.add_argument("--windowed", action="store_true", help="im Fenster statt Vollbild")
    p.add_argument("--fps", type=int, default=DEFAULTS["fps"], help="Ziel-FPS")
    p.add_argument("--size", type=int, default=DEFAULTS["size"], help="Schriftgröße in px")
    p.add_argument("--color", choices=SCHEME_ORDER, default=DEFAULTS["color"],
                   help="Farbschema")
    p.add_argument("--speed", type=float, default=DEFAULTS["speed"],
                   help="Geschwindigkeitsfaktor")
    p.add_argument("--ascii", action="store_true", help="nur ASCII-Zeichen verwenden")
    p.add_argument("--screensaver", action="store_true",
                   help="jede Taste/Mausbewegung beendet das Programm")
    p.add_argument("--test-frames", type=int, default=0, metavar="N",
                   help="headless Smoke-Test: N Frames rendern und beenden")
    args = p.parse_args(argv)
    args.fps = max(1, args.fps)
    args.size = max(8, args.size)
    return args


def windows_scr_args(argv: list[str]) -> list[str] | None:
    """Übersetzt die Windows-Bildschirmschoner-Parameter (/s, /c, /p).

    Gibt die argparse-Argumente zurück oder None, wenn nichts zu starten ist.
    """
    if not argv or not argv[0].startswith("/"):
        return argv
    mode = argv[0][:2].lower()
    if mode == "/s":
        return ["--screensaver"]
    if mode == "/c":  # Einstellungen: es gibt keine, nur ein Hinweis
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
                0, "Matrix Rain hat keine Einstellungen.\n"
                   "Optionen stehen oben in matrix_rain.py (DEFAULTS).", "Matrix Rain", 0x40)
        except Exception:
            pass
        return None
    return None  # /p (Vorschau im Dialogfenster) wird nicht unterstützt


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = windows_scr_args(sys.argv[1:])
        if argv is None:
            return 0
    args = parse_args(argv)
    if args.test_frames:
        os.environ["SDL_VIDEODRIVER"] = "dummy"  # kein Fenster nötig
        args.windowed = True
    else:
        enable_dpi_awareness()
    app = None
    try:
        app = MatrixRain(args)
        frames = app.run(args.test_frames)
        if args.test_frames:
            print(f"Smoke-Test OK: {frames} Frames, {len(app.columns)} Spalten, "
                  f"{len(app.chars)} Zeichen.")
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
