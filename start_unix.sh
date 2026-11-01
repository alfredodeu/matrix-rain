#!/usr/bin/env bash
# Matrix Rain - Start unter macOS/Linux (legt beim ersten Start .venv an)
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 nicht gefunden. Bitte installieren (Fedora: sudo dnf install python3)." >&2
    exit 1
fi

if [ ! -d .venv ]; then
    echo "Lege virtuelle Umgebung an ..."
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --disable-pip-version-check -r requirements.txt

# Hinweis für Fedora, falls keine Katakana-Schrift vorhanden ist
if command -v fc-list >/dev/null 2>&1 && ! fc-list :lang=ja | grep -q .; then
    echo "Hinweis: Keine japanische Schrift gefunden. Fedora:" >&2
    echo "  sudo dnf install google-noto-sans-cjk-fonts" >&2
fi

exec python matrix_rain.py "$@"
