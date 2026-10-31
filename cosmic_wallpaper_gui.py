#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cosmic Wallpaper 2.0 — Fondo animado para COSMIC Desktop
Creado por: Noir Perceval (Daniel Chable)
GitHub: https://github.com/Noirperceval

Novedades de la versión 2.0:
- Rediseño visual monocromo (tema claro y oscuro) con sidebar y rotación visible.
- Búfer nivel 2: caché de mpv en RAM + frame de respaldo en el escritorio
  (cosmic-bg) para que nunca se vea un fondo negro o estático entre videos.
- Selección múltiple ordenable (arrastrar en la lista de rotación).
- Pausa / reanudación real, restauración del último fondo y apagado limpio.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

from PySide6 import QtCore, QtGui, QtSvg, QtWidgets

APP_NAME = "Cosmic Wallpaper"
VERSION = "2.0.1"
AUTHOR_NAME = "Noir Perceval (Daniel Chable)"
GITHUB_URL = "https://github.com/Noirperceval"

HOME = Path.home()
CACHE_DIR = HOME / ".cache" / "cosmic-wallpaper"
THUMB_DIR = CACHE_DIR / "thumbnails"
BACKING_DIR = CACHE_DIR / "backing"
PLAYLIST_FILE = CACHE_DIR / "playlist.m3u"
PID_FILE = CACHE_DIR / "engine.pid"
IPC_PATH = CACHE_DIR / "mpv.sock"
BG_BACKUP = CACHE_DIR / "cosmic-bg-original.conf"
CONFIG_FILE = HOME / ".config" / "cosmic-wallpaper" / "config.json"
BG_CONFIG = HOME / ".config" / "cosmic" / "com.system76.CosmicBackground" / "v1" / "all"

for _d in (CACHE_DIR, THUMB_DIR, BACKING_DIR, CONFIG_FILE.parent):
    _d.mkdir(parents=True, exist_ok=True)

VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov"}
CARD_MIN_W, CARD_MAX_W = 200, 300
CARD_GAP, CARD_META_H = 14, 45
LIST_H = 68


# ---------------------------------------------------------------------------
# Tema monocromo (solo blanco y negro)
# ---------------------------------------------------------------------------

THEMES = {
    "dark": {
        "bg": "#101113",
        "surface": "#17181B",
        "elevated": "#1F2125",
        "hover": "#26282D",
        "border": "#2B2E34",
        "border_strong": "#3C4048",
        "text": "#F4F4F5",
        "muted": "#9CA0A8",
        "faint": "#6D7178",
        "accent": "#F4F4F5",
        "accent_fg": "#101113",
        "shadow": "rgba(0, 0, 0, 150)",
    },
    "light": {
        "bg": "#F5F5F6",
        "surface": "#FFFFFF",
        "elevated": "#EDEDEF",
        "hover": "#E4E5E7",
        "border": "#DCDDE0",
        "border_strong": "#C2C4C9",
        "text": "#141517",
        "muted": "#62656B",
        "faint": "#8C8F95",
        "accent": "#141517",
        "accent_fg": "#FFFFFF",
        "shadow": "rgba(0, 0, 0, 45)",
    },
}


class Theme:
    name = "dark"
    tokens = THEMES["dark"]

    @classmethod
    def set(cls, name: str):
        cls.name = name if name in THEMES else "dark"
        cls.tokens = THEMES[cls.name]
        return cls.tokens

    @classmethod
    def c(cls, key: str) -> str:
        return cls.tokens[key]


QSS_TEMPLATE = """
QWidget {
    color: {text};
    font-family: "Inter", "Cantarell", "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 12px;
}
QMainWindow, QWidget#Root, QDialog { background: {bg}; }
QToolTip {
    background: {elevated};
    color: {text};
    border: 1px solid {border_strong};
    border-radius: 6px;
    padding: 5px 8px;
}

/* ---------- header ---------- */
QWidget#Header { background: {bg}; border-bottom: 1px solid {border}; }
QLabel#AppTitle { font-size: 15px; font-weight: 650; letter-spacing: -0.2px; }
QPushButton#PathChip {
    background: {elevated};
    border: 1px solid {border};
    border-radius: 10px;
    color: {muted};
    font-size: 11px;
    padding: 3px 9px;
    text-align: left;
}
QPushButton#PathChip:hover { background: {hover}; color: {text}; }
QLineEdit#Search {
    background: {elevated};
    border: 1px solid {border};
    border-radius: 9px;
    padding: 6px 10px;
    color: {text};
    selection-background-color: {accent};
    selection-color: {accent_fg};
}
QLineEdit#Search:focus { border-color: {border_strong}; }
QPushButton#IconBtn {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 9px;
    padding: 6px;
}
QPushButton#IconBtn:hover { background: {elevated}; border-color: {border}; }

/* ---------- sidebar ---------- */
QFrame#Sidebar { background: {surface}; border-right: 1px solid {border}; }
QLabel#Section {
    color: {faint};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.4px;
    padding: 0 8px;
}
QFrame#Divider { background: {border}; border: none; max-height: 1px; min-height: 1px; }
QFrame[nav="true"] {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
}
QFrame[nav="true"]:hover { background: {hover}; }
QFrame[nav="true"][active="true"] {
    background: {elevated};
    border-color: {border_strong};
}
QFrame[nav="true"] QLabel { color: {muted}; }
QFrame[nav="true"]:hover QLabel { color: {text}; }
QFrame[nav="true"][active="true"] QLabel { color: {text}; font-weight: 600; }
QLabel#NavCount {
    color: {faint};
    font-size: 10px;
    background: {bg};
    border: 1px solid {border};
    border-radius: 9px;
    padding: 0 6px;
    max-height: 16px;
}
QFrame[nav="true"][active="true"] QLabel#NavCount {
    background: {surface};
    color: {text};
    border-color: {border_strong};
    font-weight: 600;
}
QListWidget#Rotation {
    background: transparent;
    border: none;
    outline: none;
}
QListWidget#Rotation::item { border: none; }
QPushButton#RotAdd {
    background: transparent;
    border: 1px dashed {border_strong};
    border-radius: 6px;
    color: {faint};
    font-size: 11px;
    padding: 6px 8px;
    text-align: left;
}
QPushButton#RotAdd:hover { color: {text}; border-color: {muted}; }
QPushButton#RotAdd:disabled { color: {faint}; border-color: {border}; }
QFrame#Deps {
    background: {elevated};
    border: 1px solid {border};
    border-radius: 9px;
}
QFrame#Deps QLabel { color: {muted}; font-size: 11px; }
QLabel#DepDotOk { color: {accent}; font-size: 9px; }
QLabel#DepDotBad { color: {faint}; font-size: 9px; }
QLabel#DepsFoot { color: {faint}; font-size: 10px; }

/* ---------- main ---------- */
QWidget#Main { background: {bg}; }
QLabel#ToolbarCount { color: {muted}; font-size: 12px; }
QFrame#Seg {
    background: {elevated};
    border: 1px solid {border};
    border-radius: 8px;
}
QPushButton#ViewBtn {
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
}
QPushButton#ViewBtn:hover { background: {hover}; }
QPushButton#ViewBtn[active="true"] { background: {bg}; border: 1px solid {border}; }
QScrollArea#Scroll { background: transparent; border: none; }
QWidget#ScrollBody { background: transparent; }
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: {border_strong};
    border-radius: 5px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover { background: {muted}; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

/* ---------- tarjetas ---------- */
QFrame#Card {
    background: {surface};
    border: 1px solid {border};
    border-radius: 12px;
}
QFrame#Card:hover { border-color: {border_strong}; }
QFrame#Card[state="selected"] { border-color: {border_strong}; }
QFrame#Card[state="live"] { border: 2px solid {accent}; }
QLabel#CardName { color: {text}; font-size: 11.5px; font-weight: 600; }
QLabel#CardDur, QLabel#CardSub { color: {faint}; font-size: 10.5px; }
QLabel#LiveTag {
    background: {accent};
    color: {accent_fg};
    border-radius: 8px;
    padding: 2px 7px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#Empty {
    color: {faint};
    font-size: 12.5px;
    padding: 60px;
}

/* ---------- footer ---------- */
QFrame#Footer { background: {surface}; border-top: 1px solid {border}; }
QLabel#StatusNow { font-size: 12.5px; font-weight: 600; }
QLabel#StatusMuted { color: {muted}; font-size: 12.5px; }
QLabel#StatusSub { color: {faint}; font-size: 10.5px; }
QLabel#LiveDot { font-size: 11px; }
QProgressBar#Buffer {
    background: {elevated};
    border: none;
    border-radius: 2px;
    max-height: 4px;
    min-height: 4px;
}
QProgressBar#Buffer::chunk { background: {accent}; border-radius: 2px; }
QPushButton#Primary {
    background: {accent};
    color: {accent_fg};
    border: 1px solid {accent};
    border-radius: 10px;
    font-size: 12.5px;
    font-weight: 700;
    padding: 9px 17px;
}
QPushButton#Primary:hover { background: {text}; }
QPushButton#Primary:pressed { background: {muted}; }
QPushButton#Ghost {
    background: transparent;
    color: {text};
    border: 1px solid {border_strong};
    border-radius: 10px;
    font-size: 12.5px;
    font-weight: 600;
    padding: 9px 15px;
}
QPushButton#Ghost:hover { background: {elevated}; }
QPushButton#Ghost:disabled { color: {faint}; border-color: {border}; }

/* ---------- diálogos y menús ---------- */
QDialog QLabel { color: {text}; }
QPushButton#DlgPrimary {
    background: {accent};
    color: {accent_fg};
    border: 1px solid {accent};
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 700;
}
QPushButton#DlgGhost {
    background: transparent;
    border: 1px solid {border_strong};
    border-radius: 8px;
    padding: 8px 14px;
}
QPushButton#DlgGhost:hover { background: {elevated}; }
QMenu {
    background: {surface};
    border: 1px solid {border_strong};
    border-radius: 8px;
    padding: 5px;
}
QMenu::item { padding: 6px 22px 6px 14px; border-radius: 5px; }
QMenu::item:selected { background: {elevated}; }
QMenu::separator { height: 1px; background: {border}; margin: 4px 6px; }
QMenu::indicator { width: 13px; height: 13px; }
"""


def build_qss(tokens: dict) -> str:
    qss = QSS_TEMPLATE
    for key, value in tokens.items():
        qss = qss.replace("{" + key + "}", value)
    return qss


# ---------------------------------------------------------------------------
# Iconos vectoriales monocromos
# ---------------------------------------------------------------------------

_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="1.8" '
    'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
)

ICONS = {
    "play": '<path fill="currentColor" stroke="none" d="M8 5.5v13l11-6.5z"/>',
    "folder": '<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5h3.2c.6 0 1.2.2 1.6.6L12 7.2h6.5A2.5 2.5 0 0 1 21 9.7v7.8A2.5 2.5 0 0 1 18.5 20h-13A2.5 2.5 0 0 1 3 17.5z"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
    "refresh": '<path d="M20 11a8 8 0 1 0-2.3 6.4"/><path d="M20 4.5V11h-6.2"/>',
    "gear": '<circle cx="12" cy="12" r="3.2"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H10a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V10a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    "grid": '<rect x="4" y="4" width="7" height="7" rx="1.6"/><rect x="13" y="4" width="7" height="7" rx="1.6"/><rect x="4" y="13" width="7" height="7" rx="1.6"/><rect x="13" y="13" width="7" height="7" rx="1.6"/>',
    "list": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "check": '<path stroke-width="3.1" d="m5 12.5 4.5 4.5L19 7"/>',
    "stop": '<rect x="6.5" y="6.5" width="11" height="11" rx="2" fill="currentColor" stroke="none"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "video": '<rect x="3" y="6" width="12.5" height="12" rx="2.5"/><path d="m15.5 11 5-3v8l-5-3z"/>',
    "star": '<path d="m12 4 2.4 5 5.6.8-4 3.9 1 5.5-5-2.7-5 2.7 1-5.5-4-3.9 5.6-.8z"/>',
    "clock": '<circle cx="12" cy="12" r="8.2"/><path d="M12 7.5V12l3.2 2"/>',
    "layers": '<path d="m12 3 8.5 4.5L12 12 3.5 7.5z"/><path d="m3.5 12.2 8.5 4.5 8.5-4.5"/><path d="m3.5 16.7 8.5 4.5 8.5-4.5"/>',
    "pause": '<path d="M9 5v14M15 5v14" stroke-width="2.6"/>',
    "quit": '<path d="M15 4h3.5A1.5 1.5 0 0 1 20 5.5v13A1.5 1.5 0 0 1 18.5 20H15"/><path d="M10 8l-4 4 4 4M6 12h9"/>',
    "info": '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 8h.01" stroke-width="2"/>',
    "trash": '<path d="M4 7h16M9.5 7V5h5v2M6.5 7l1 12.5h9L17.5 7"/>',
}


def make_icon(name: str, color: str, size: int = 16) -> QtGui.QIcon:
    body = ICONS.get(name, "")
    svg = _SVG.format(body=body).replace("currentColor", color)
    renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(svg.encode("utf-8")))
    pm = QtGui.QPixmap(size * 2, size * 2)
    pm.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pm)
    painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
    renderer.render(painter)
    painter.end()
    pm.setDevicePixelRatio(2.0)
    return QtGui.QIcon(pm)


def make_pixmap(name: str, color: str, size: int = 16) -> QtGui.QPixmap:
    return make_icon(name, color, size).pixmap(QtCore.QSize(size, size))


def app_pixmap(size: int = 64) -> QtGui.QPixmap:
    t = Theme.tokens
    pm = QtGui.QPixmap(size, size)
    pm.fill(QtCore.Qt.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.Antialiasing, True)
    p.setPen(QtCore.Qt.NoPen)
    p.setBrush(QtGui.QColor(t["accent"]))
    p.drawRoundedRect(QtCore.QRectF(0, 0, size, size), size * 0.27, size * 0.27)
    p.setBrush(QtGui.QColor(t["accent_fg"]))
    triangle = QtGui.QPolygonF([
        QtCore.QPointF(size * 0.40, size * 0.29),
        QtCore.QPointF(size * 0.75, size * 0.50),
        QtCore.QPointF(size * 0.40, size * 0.71),
    ])
    p.drawPolygon(triangle)
    p.end()
    return pm


def repolish(widget: QtWidgets.QWidget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


# ---------------------------------------------------------------------------
# Utilidades del sistema
# ---------------------------------------------------------------------------

def detect_distro() -> dict:
    """Detecta la distribución y el comando de instalación adecuado."""
    info = {"name": "Linux", "id": "", "id_like": "", "pkg_manager": "desconocido",
            "install_cmd": "", "mpvpaper_pkg": "mpvpaper", "ffmpeg_pkg": "ffmpeg"}

    os_release = Path("/etc/os-release")
    if os_release.exists():
        try:
            for line in os_release.read_text(encoding="utf-8").splitlines():
                if line.startswith("NAME="):
                    info["name"] = line.split("=", 1)[1].strip().strip('"')
                elif line.startswith("ID="):
                    info["id"] = line.split("=", 1)[1].strip().strip('"').lower()
                elif line.startswith("ID_LIKE="):
                    info["id_like"] = line.split("=", 1)[1].strip().strip('"').lower()
        except OSError:
            pass

    family = info["id"] + " " + info["id_like"]
    if any(k in family for k in ["arch", "cachyos", "manjaro", "endeavouros"]):
        info.update(pkg_manager="pacman", install_cmd="sudo pacman -S --needed --noconfirm")
    elif any(k in family for k in ["fedora", "rhel", "nobara"]):
        info.update(pkg_manager="dnf", install_cmd="sudo dnf install -y", ffmpeg_pkg="ffmpeg-free")
    elif any(k in family for k in ["ubuntu", "debian", "pop", "mint"]):
        info.update(pkg_manager="apt", install_cmd="sudo apt update && sudo apt install -y")
    elif "opensuse" in family:
        info.update(pkg_manager="zypper", install_cmd="sudo zypper install -y")
    return info


def launch_in_terminal(command: str) -> bool:
    """Ejecuta un comando en la primera terminal disponible."""
    terminals = [
        ("cosmic-term", ["-e", "bash", "-c"]),
        ("alacritty", ["-e", "bash", "-c"]),
        ("foot", ["bash", "-c"]),
        ("konsole", ["-e", "bash", "-c"]),
        ("gnome-terminal", ["--", "bash", "-c"]),
        ("xterm", ["-e", "bash", "-c"]),
    ]
    tail = f"{command}; echo; read -p 'Presiona Enter para cerrar...'"
    for term, args in terminals:
        if shutil.which(term):
            try:
                subprocess.Popen([term, *args, tail])
                return True
            except OSError:
                continue
    return False


def human_mb(num_bytes: int) -> str:
    mb = num_bytes / (1024 * 1024)
    if mb >= 1024:
        return f"{mb / 1024:.1f} GB"
    return f"{mb:.0f} MB"


def format_duration(seconds: float) -> str:
    try:
        total = int(round(seconds))
    except (TypeError, ValueError):
        return "--:--"
    if total <= 0:
        return "--:--"
    return f"{total // 60:02d}:{total % 60:02d}"


def set_elided_label(label: QtWidgets.QLabel, text: str, max_width: int):
    fm = label.fontMetrics()
    label.setText(fm.elidedText(text, QtCore.Qt.ElideRight, max_width - 8))
    label.setToolTip(text)


# ---------------------------------------------------------------------------
# Miniaturas, duraciones y frame de respaldo
# ---------------------------------------------------------------------------

_thumb_cache: dict[Path, Path | None] = {}
_duration_cache: dict[Path, float] = {}


def get_thumbnail(video: Path) -> Path | None:
    if video in _thumb_cache:
        return _thumb_cache[video]
    try:
        mtime = int(video.stat().st_mtime)
    except OSError:
        _thumb_cache[video] = None
        return None

    out = THUMB_DIR / f"{video.stem}_{mtime}.jpg"
    if not out.exists():
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            _thumb_cache[video] = None
            return None
        cmd = [
            ffmpeg, "-y", "-ss", "00:00:01", "-i", str(video),
            "-frames:v", "1", "-q:v", "3",
            "-vf", "scale=320:180:force_original_aspect_ratio=increase,crop=320:180",
            str(out),
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        except (OSError, subprocess.SubprocessError):
            pass
    result = out if out.exists() else None
    _thumb_cache[video] = result
    return result


def probe_duration(video: Path) -> float:
    if video in _duration_cache:
        return _duration_cache[video]
    ffprobe = shutil.which("ffprobe")
    duration = 0.0
    if ffprobe:
        try:
            out = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(video)],
                capture_output=True, text=True, timeout=6,
            )
            duration = float(out.stdout.strip())
        except (OSError, subprocess.SubprocessError, ValueError):
            duration = 0.0
    _duration_cache[video] = duration
    return duration


def backing_frame(video: Path) -> Path | None:
    """Extrae un frame del video para usarlo como fondo estático de respaldo."""
    try:
        mtime = int(video.stat().st_mtime)
    except OSError:
        return None
    out = BACKING_DIR / f"{video.stem}_{mtime}.jpg"
    if out.exists():
        return out
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    cmd = [ffmpeg, "-y", "-ss", "00:00:01", "-i", str(video),
           "-frames:v", "1", "-q:v", "3", str(out)]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return out if out.exists() else None


def apply_cosmic_background(image: Path) -> bool:
    """Pinta `image` como fondo estático de COSMIC respaldando la config original."""
    if not shutil.which("cosmic-bg") or not image.exists():
        return False
    if not BG_CONFIG.parent.exists():
        return False
    try:
        original = BG_CONFIG.read_text(encoding="utf-8")
    except OSError:
        return False

    if not BG_BACKUP.exists():
        try:
            BG_BACKUP.write_text(original, encoding="utf-8")
        except OSError:
            pass

    source = 'source: Path("{}")'.format(str(image).replace('\\', '\\\\').replace('"', '\\"'))
    if re.search(r'source:\s*Path\("[^"]*"\)', original):
        updated = re.sub(r'source:\s*Path\("[^"]*"\)', source, original, count=1)
    else:
        updated = (
            '(\n'
            '    output: "all",\n'
            f'    {source},\n'
            '    filter_by_theme: false,\n'
            '    rotation_frequency: 300,\n'
            '    filter_method: Lanczos,\n'
            '    scaling_mode: Zoom,\n'
            '    sampling_method: Alphanumeric,\n'
            ')\n'
        )
    # Evita que el tema del sistema sustituya nuestro frame
    updated = re.sub(r'filter_by_theme:\s*#?\w+', 'filter_by_theme: false', updated, count=1)

    try:
        BG_CONFIG.write_text(updated, encoding="utf-8")
        return True
    except OSError:
        return False


def restore_cosmic_background() -> bool:
    """Devuelve el fondo estático que el usuario tenía antes de usar la app."""
    if not BG_BACKUP.exists():
        return False
    try:
        shutil.copyfile(BG_BACKUP, BG_CONFIG)
        BG_BACKUP.unlink()
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Motor de fondo animado (búfer nivel 2)
# ---------------------------------------------------------------------------

class WallpaperEngine(QtCore.QObject):
    """Controla mpvpaper con caché en RAM y frame de respaldo del escritorio."""

    changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.proc: subprocess.Popen | None = None
        self.playlist: list[Path] = []
        self.index = 0
        self.paused = False
        self.mpvpaper = shutil.which("mpvpaper")
        self._watch = QtCore.QTimer(self)
        self._watch.setInterval(2000)
        self._watch.timeout.connect(self._check_alive)

    # -- estado ---------------------------------------------------------
    def running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    # -- reproducción ---------------------------------------------------
    def start(self, videos, start_index: int = 0) -> bool:
        videos = [Path(v) for v in videos if Path(v).exists()]
        self._kill()
        if not videos or not self.mpvpaper:
            self.playlist = []
            self.changed.emit()
            return False

        self.playlist = videos
        self.index = max(0, min(start_index, len(videos) - 1))
        self.paused = False

        # Nivel 2: frame de respaldo ANTES de lanzar el video, para que el
        # escritorio nunca muestre un fondo negro ni un salto estático.
        frame = backing_frame(videos[self.index])
        if frame:
            apply_cosmic_background(frame)

        try:
            IPC_PATH.unlink()
        except OSError:
            pass

        # Nivel 1: caché en RAM + prefetch del siguiente video de la lista.
        # El socket IPC permite pedir "siguiente video" sin reiniciar mpv.
        options = (
            "no-audio loop-file=inf keep-open=yes cache=yes cache-secs=300 "
            "demuxer-max-bytes=768MiB demuxer-readahead-secs=60 prefetch-playlist=yes "
            f"input-ipc-server={IPC_PATH}"
        )
        if len(videos) == 1:
            cmd = [self.mpvpaper, "-o", options, "*", str(videos[0])]
        else:
            try:
                PLAYLIST_FILE.write_text(
                    "#EXTM3U\n" + "\n".join(str(v) for v in videos), encoding="utf-8"
                )
            except OSError:
                self.playlist = []
                return False
            cmd = [
                self.mpvpaper, "-o",
                options + f" loop-playlist=inf playlist-start={self.index}",
                "*", str(PLAYLIST_FILE),
            ]

        try:
            self.proc = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            PID_FILE.write_text(str(self.proc.pid), encoding="utf-8")
        except OSError:
            self.proc = None
            self.playlist = []
            return False

        self._watch.start()
        self.changed.emit()
        return True

    # -- control por IPC -------------------------------------------------
    def _ipc(self, command: list, timeout: float = 0.5) -> dict | None:
        """Envía un comando a mpv y devuelve su respuesta (ignora eventos)."""
        if not self.running() or not IPC_PATH.exists():
            return None
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect(str(IPC_PATH))
                request_id = 7
                payload = json.dumps(
                    {"command": command, "request_id": request_id}) + "\n"
                sock.sendall(payload.encode("utf-8"))
                buffer = b""
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    chunk = sock.recv(65536)
                    if not chunk:
                        break
                    buffer += chunk
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        try:
                            message = json.loads(line.decode("utf-8"))
                        except ValueError:
                            continue
                        if message.get("request_id") == request_id:
                            return message
        except (OSError, ValueError):
            return None
        return None

    def next_video(self) -> bool:
        response = self._ipc(["playlist-next", "weak"], timeout=0.8)
        return bool(response and response.get("error") == "success")

    def current_index(self) -> int | None:
        response = self._ipc(["get_property", "playlist-pos"], timeout=0.25)
        if not response or response.get("error") != "success":
            return None
        position = response.get("data")
        if isinstance(position, int) and position >= 0:
            return position
        return None

    def stop(self, restore_background: bool = True):
        self._kill()
        self.playlist = []
        if restore_background:
            restore_cosmic_background()
        self.changed.emit()

    def set_paused(self, paused: bool):
        if not self.running():
            return
        try:
            sig = signal.SIGSTOP if paused else signal.SIGCONT
            os.killpg(os.getpgid(self.proc.pid), sig)
        except (ProcessLookupError, PermissionError, OSError):
            return
        self.paused = paused
        self.changed.emit()

    def toggle_paused(self):
        if self.running():
            self.set_paused(not self.paused)

    # -- internos -------------------------------------------------------
    def _kill(self):
        if self.proc is not None:
            pid = self.proc.pid
            try:
                if self.proc.poll() is None:
                    pgid = os.getpgid(pid)
                    # Un proceso detenido (SIGSTOP) no atiende SIGTERM hasta
                    # que se reanuda, así que lo despertamos primero.
                    try:
                        os.killpg(pgid, signal.SIGCONT)
                    except OSError:
                        pass
                    os.killpg(pgid, signal.SIGTERM)
                    try:
                        self.proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                pass
            self.proc = None
        self.paused = False
        try:
            PID_FILE.unlink()
        except OSError:
            pass
        try:
            IPC_PATH.unlink()
        except OSError:
            pass
        self._watch.stop()

    def _check_alive(self):
        if self.proc is not None and self.proc.poll() is not None:
            self.proc = None
            self.paused = False
            self._watch.stop()
            try:
                PID_FILE.unlink()
            except OSError:
                pass
            try:
                IPC_PATH.unlink()
            except OSError:
                pass
            self.changed.emit()


def _pid_is_mpvpaper(pid: int) -> bool:
    """Evita matar un proceso ajeno si el PID fue reutilizado."""
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False
    return b"mpvpaper" in raw


def stop_from_cli() -> int:
    """Detiene un motor que quedó vivo de una sesión anterior."""
    stopped = False
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        pid = 0

    if pid > 0 and _pid_is_mpvpaper(pid):
        try:
            pgid = os.getpgid(pid)
            try:
                os.killpg(pgid, signal.SIGCONT)
            except OSError:
                pass
            os.killpg(pgid, signal.SIGTERM)
            stopped = True
        except (ProcessLookupError, PermissionError, OSError):
            pass
        try:
            PID_FILE.unlink()
        except OSError:
            pass

    if restore_cosmic_background():
        stopped = True
    print("Fondo animado detenido." if stopped else "No había un fondo animado activo.")
    return 0


# ---------------------------------------------------------------------------
# Widgets personalizados
# ---------------------------------------------------------------------------

def rounded_top_path(rect: QtCore.QRectF, radius: float) -> QtGui.QPainterPath:
    path = QtGui.QPainterPath()
    path.moveTo(rect.left(), rect.bottom())
    path.lineTo(rect.left(), rect.top() + radius)
    path.quadTo(rect.left(), rect.top(), rect.left() + radius, rect.top())
    path.lineTo(rect.right() - radius, rect.top())
    path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + radius)
    path.lineTo(rect.right(), rect.bottom())
    path.closeSubpath()
    return path


def draw_cover(painter: QtGui.QPainter, rect: QtCore.QRectF, pixmap: QtGui.QPixmap):
    if pixmap.isNull():
        return
    scaled = pixmap.scaled(
        rect.size().toSize(), QtCore.Qt.KeepAspectRatioByExpanding,
        QtCore.Qt.SmoothTransformation,
    )
    src = QtCore.QRect(
        max(0, (scaled.width() - int(rect.width())) // 2),
        max(0, (scaled.height() - int(rect.height())) // 2),
        int(rect.width()), int(rect.height()),
    )
    painter.drawPixmap(rect.toRect(), scaled, src)


class ThumbWidget(QtWidgets.QWidget):
    """Miniatura dibujada a mano: imagen, degradado, casilla y badges."""

    clicked = QtCore.Signal()
    toggled = QtCore.Signal()

    def __init__(self, thumb: Path | None, compact: bool = False, parent=None):
        super().__init__(parent)
        self.compact = compact
        self.selected = False
        self.live = False
        self.buffered = False
        self._pm = QtGui.QPixmap(str(thumb)) if thumb and thumb.exists() else QtGui.QPixmap()
        self._check_rect = QtCore.QRectF()
        self._pulse_on = True
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(750)
        self._timer.timeout.connect(self._pulse)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setAttribute(QtCore.Qt.WA_Hover, True)

    def set_states(self, selected: bool, live: bool, buffered: bool):
        self.selected = selected
        self.live = live
        self.buffered = buffered
        if live and not self.compact and not self._timer.isActive():
            self._timer.start()
        elif not live and self._timer.isActive():
            self._timer.stop()
            self._pulse_on = True
        self.update()

    def _pulse(self):
        self._pulse_on = not self._pulse_on
        self.update()

    # -- pintura --------------------------------------------------------
    def paintEvent(self, event):
        t = Theme.tokens
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        r = QtCore.QRectF(self.rect())
        radius = 8.0 if self.compact else 11.0
        path = QtGui.QPainterPath()
        if self.compact:
            path.addRoundedRect(r, radius, radius)
        else:
            path = rounded_top_path(r, radius)
        p.setClipPath(path)

        if not self._pm.isNull():
            draw_cover(p, r, self._pm)
        else:
            p.fillRect(r, QtGui.QColor(t["elevated"]))
            icon = make_pixmap("video", t["faint"], 24)
            p.drawPixmap(
                int(r.center().x() - 12), int(r.center().y() - 12), icon,
            )

        if not self.compact:
            grad = QtGui.QLinearGradient(0, r.height() * 0.45, 0, r.height())
            grad.setColorAt(0.0, QtGui.QColor(0, 0, 0, 0))
            grad.setColorAt(1.0, QtGui.QColor(0, 0, 0, 120))
            p.fillRect(r, grad)
            self._paint_check(p, t)
            self._paint_badges(p, t)
        p.end()

    def _paint_check(self, p: QtGui.QPainter, t: dict):
        size, margin = 20.0, 8.0
        rect = QtCore.QRectF(margin, margin, size, size)
        self._check_rect = rect
        p.setPen(QtGui.QPen(
            QtGui.QColor(t["accent"] if self.selected else "#FFFFFF"), 1.6))
        p.setBrush(QtGui.QColor(t["accent"]) if self.selected
                   else QtGui.QColor(12, 13, 15, 145))
        p.drawRoundedRect(rect, 6, 6)
        if self.selected:
            pen = QtGui.QPen(QtGui.QColor(t["accent_fg"]), 2.2)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            pen.setJoinStyle(QtCore.Qt.RoundJoin)
            p.setPen(pen)
            p.drawPolyline(QtGui.QPolygonF([
                QtCore.QPointF(rect.left() + 5, rect.top() + 10.5),
                QtCore.QPointF(rect.left() + 8.6, rect.top() + 14),
                QtCore.QPointF(rect.left() + 15, rect.top() + 6.5),
            ]))

    def _paint_badges(self, p: QtGui.QPainter, t: dict):
        right = self.width() - 8.0
        top = 8.0
        if self.live:
            right = self._pill(
                p, right, top, "EN VIVO", QtGui.QColor(t["accent"]),
                QtGui.QColor(t["accent_fg"]), dot=True, pulse=self._pulse_on,
            )
        elif self.buffered:
            self._pill(
                p, right, top, "PRECARGADO", QtGui.QColor(10, 11, 13, 160),
                QtGui.QColor("#F4F4F5"), dot=False,
                border=QtGui.QColor(255, 255, 255, 70),
            )

    def _pill(self, p, right, top, text, bg, fg, dot=False, border=None,
              pulse=True) -> float:
        font = QtGui.QFont(self.font())
        font.setPixelSize(9)
        font.setWeight(QtGui.QFont.Weight.DemiBold)
        font.setLetterSpacing(QtGui.QFont.SpacingType.AbsoluteSpacing, 0.7)
        p.setFont(font)
        fm = QtGui.QFontMetrics(font)
        text_w = fm.horizontalAdvance(text)
        height = 18.0
        pad = 7.0
        dot_w = 10.0 if dot else 0.0
        width = text_w + pad * 2 + dot_w
        rect = QtCore.QRectF(right - width, top, width, height)

        p.setPen(QtGui.QPen(border, 1) if border else QtCore.Qt.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(rect, height / 2, height / 2)

        x = rect.left() + pad
        if dot:
            p.setPen(QtCore.Qt.NoPen)
            color = QtGui.QColor(fg)
            color.setAlpha(255 if pulse else 90)
            p.setBrush(color)
            p.drawEllipse(QtCore.QRectF(x, rect.center().y() - 2.5, 5, 5))
            x += dot_w
        p.setPen(QtGui.QPen(fg))
        p.drawText(
            QtCore.QRectF(x, rect.top(), text_w + 1, height),
            int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter), text,
        )
        return rect.left() - 6

    # -- interacción ----------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if not self.compact and self._check_rect.contains(event.position()):
                self.toggled.emit()
            else:
                self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class CheckButton(QtWidgets.QWidget):
    toggled = QtCore.Signal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.checked = checked
        self.setFixedSize(20, 20)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def set_checked(self, value: bool):
        if self.checked != value:
            self.checked = value
            self.update()

    def paintEvent(self, event):
        t = Theme.tokens
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        rect = QtCore.QRectF(1, 1, 18, 18)
        p.setPen(QtGui.QPen(QtGui.QColor(t["accent"] if self.checked else t["border_strong"]), 1.5))
        p.setBrush(QtGui.QColor(t["accent"]) if self.checked else QtCore.Qt.NoBrush)
        p.drawRoundedRect(rect, 5, 5)
        if self.checked:
            pen = QtGui.QPen(QtGui.QColor(t["accent_fg"]), 2.1)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            pen.setJoinStyle(QtCore.Qt.RoundJoin)
            p.setPen(pen)
            p.drawPolyline(QtGui.QPolygonF([
                QtCore.QPointF(5.5, 10.5), QtCore.QPointF(8.6, 13.5),
                QtCore.QPointF(14.5, 6.5),
            ]))
        p.end()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.checked = not self.checked
            self.update()
            self.toggled.emit(self.checked)
            event.accept()
            return
        super().mousePressEvent(event)


class ElidedLabel(QtWidgets.QLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._full = text
        super().setText(text)
        self.setToolTip(text)
        self.setMinimumWidth(0)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                           QtWidgets.QSizePolicy.Preferred)

    def setText(self, text: str):
        self._full = text
        super().setText(text)
        self.setToolTip(text)
        self.update()

    def set_full_text(self, text: str):
        self.setText(text)

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        fm = self.fontMetrics()
        color = QtGui.QColor(Theme.c("muted") if self.objectName() == "StatusMuted"
                             else Theme.c("text"))
        p.setPen(color)
        text = fm.elidedText(self._full, QtCore.Qt.ElideRight, self.width())
        p.drawText(self.rect(), int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter), text)
        p.end()


class ClickableFrame(QtWidgets.QFrame):
    clicked = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class ScrollArea(QtWidgets.QScrollArea):
    resized = QtCore.Signal()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()


class NavItem(QtWidgets.QFrame):
    clicked = QtCore.Signal(str)

    def __init__(self, key: str, icon_name: str, text: str, count: int = 0, parent=None):
        super().__init__(parent)
        self.key = key
        self.setProperty("nav", True)
        self.setProperty("active", False)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(9, 5, 9, 5)
        lay.setSpacing(9)

        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedSize(15, 15)
        self.icon_label.setProperty("iconName", icon_name)
        lay.addWidget(self.icon_label)

        self.text_label = QtWidgets.QLabel(text)
        lay.addWidget(self.text_label, 1)

        self.count_label = QtWidgets.QLabel(str(count))
        self.count_label.setObjectName("NavCount")
        self.count_label.setAlignment(QtCore.Qt.AlignCenter)
        lay.addWidget(self.count_label)

    def set_active(self, active: bool):
        self.setProperty("active", active)
        repolish(self)

    def set_count(self, count: int):
        self.count_label.setText(str(count))

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.key)
        super().mousePressEvent(event)


class VideoCard(QtWidgets.QFrame):
    clicked = QtCore.Signal(Path)
    toggled = QtCore.Signal(Path, bool)
    favorite_requested = QtCore.Signal(Path)
    add_requested = QtCore.Signal(Path)
    remove_requested = QtCore.Signal(Path)

    def __init__(self, path: Path, mode: str = "grid", selected: bool = False,
                 live: bool = False, buffered: bool = False, favorite: bool = False,
                 duration: float = 0.0, parent=None):
        super().__init__(parent)
        self.path = path
        self.mode = mode
        self.selected = selected
        self.setObjectName("Card")
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.setCursor(QtCore.Qt.PointingHandCursor)

        thumb_path = get_thumbnail(path)
        self.duration = duration

        if mode == "grid":
            self.setFixedSize(CARD_MIN_W, CARD_MIN_W * 9 // 16 + CARD_META_H + 4)
            lay = QtWidgets.QVBoxLayout(self)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(0)

            self.thumb = ThumbWidget(thumb_path, compact=False)
            self.thumb.setFixedHeight(CARD_MIN_W * 9 // 16)
            lay.addWidget(self.thumb)

            meta = QtWidgets.QWidget()
            meta.setMinimumHeight(CARD_META_H)
            row = QtWidgets.QHBoxLayout(meta)
            row.setContentsMargins(10, 0, 10, 0)
            row.setSpacing(8)

            self.name_label = ElidedLabel(path.stem)
            self.name_label.setObjectName("CardName")
            row.addWidget(self.name_label, 1)

            self.dur_label = QtWidgets.QLabel(format_duration(duration))
            self.dur_label.setObjectName("CardDur")
            row.addWidget(self.dur_label)
            lay.addWidget(meta, 1)

            self.thumb.clicked.connect(lambda: self.clicked.emit(self.path))
            self.thumb.toggled.connect(lambda: self.toggled.emit(self.path, not self.selected))
            self.check = None
            self.live_badge = None
        else:
            self.setFixedHeight(LIST_H)
            self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                               QtWidgets.QSizePolicy.Fixed)
            lay = QtWidgets.QHBoxLayout(self)
            lay.setContentsMargins(8, 8, 12, 8)
            lay.setSpacing(12)

            self.thumb = ThumbWidget(thumb_path, compact=True)
            self.thumb.setFixedSize(92, LIST_H - 16)
            lay.addWidget(self.thumb)

            texts = QtWidgets.QVBoxLayout()
            texts.setContentsMargins(0, 0, 0, 0)
            texts.setSpacing(2)
            self.name_label = ElidedLabel(path.stem)
            self.name_label.setObjectName("CardName")
            texts.addWidget(self.name_label)
            self.sub_label = QtWidgets.QLabel(
                f"{format_duration(duration)} · {path.suffix.lstrip('.').upper()}"
            )
            self.sub_label.setObjectName("CardSub")
            texts.addWidget(self.sub_label)
            lay.addLayout(texts, 1)

            self.live_badge = QtWidgets.QLabel("EN VIVO")
            self.live_badge.setObjectName("LiveTag")
            self.live_badge.setFixedHeight(18)
            self.live_badge.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                          QtWidgets.QSizePolicy.Fixed)
            self.live_badge.setVisible(live)
            lay.addWidget(self.live_badge)

            self.check = CheckButton(selected)
            self.check.toggled.connect(
                lambda value: self.toggled.emit(self.path, value))
            lay.addWidget(self.check)
            self.thumb.clicked.connect(lambda: self.clicked.emit(self.path))

        if favorite:
            self.setToolTip(f"{path.name} · ★ favorito")
        self.setProperty("state", "live" if live else ("selected" if selected else ""))
        self.thumb.set_states(selected, live, buffered)
        repolish(self)

    def set_states(self, selected: bool, live: bool, buffered: bool):
        self.selected = selected
        self.setProperty("state", "live" if live else ("selected" if selected else ""))
        self.thumb.set_states(selected, live, buffered)
        if self.check is not None:
            self.check.set_checked(selected)
        if self.live_badge is not None:
            self.live_badge.setVisible(live)
        repolish(self)

    def set_grid_width(self, width: int):
        if self.mode != "grid":
            return
        width = max(CARD_MIN_W, min(CARD_MAX_W, width))
        thumb_h = round(width * 9 / 16)
        self.thumb.setFixedHeight(thumb_h)
        self.setFixedSize(width, thumb_h + CARD_META_H + 4)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.path)
        super().mousePressEvent(event)

    def _context_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        act_preview = menu.addAction("Ver como vista previa")
        act_add = menu.addAction("Añadir a la rotación")
        act_remove = menu.addAction("Quitar de la rotación")
        menu.addSeparator()
        act_fav = menu.addAction(
            "Quitar de favoritos" if self.path in self.favorites else "Marcar como favorito")
        menu.addSeparator()
        act_open = menu.addAction("Abrir carpeta contenedora")

        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen is act_preview:
            self.clicked.emit(self.path)
        elif chosen is act_add:
            self.add_requested.emit(self.path)
        elif chosen is act_remove:
            self.remove_requested.emit(self.path)
        elif chosen is act_fav:
            self.favorite_requested.emit(self.path)
        elif chosen is act_open:
            subprocess.Popen(["xdg-open", str(self.path.parent)])


class RotationDelegate(QtWidgets.QStyledItemDelegate):
    """Fila de la lista de rotación: miniatura, nombre, turno y asa."""

    def sizeHint(self, option, index):
        return QtCore.QSize(option.rect.width(), 44)

    def paint(self, painter, option, index):
        t = Theme.tokens
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        rect = option.rect.adjusted(2, 2, -2, -2)
        hovered = bool(option.state & QtWidgets.QStyle.StateFlag.State_MouseOver)
        selected = bool(option.state & QtWidgets.QStyle.StateFlag.State_Selected)
        if hovered or selected:
            painter.setPen(QtGui.QPen(QtGui.QColor(t["border_strong"]) if selected else QtCore.Qt.NoPen, 1))
            painter.setBrush(QtGui.QColor(t["hover"]))
            painter.drawRoundedRect(QtCore.QRectF(rect), 6, 6)

        thumb_rect = QtCore.QRectF(rect.left() + 6, rect.top() + 8, 40, 24)
        pixmap = index.data(QtCore.Qt.UserRole + 2)
        clip = QtGui.QPainterPath()
        clip.addRoundedRect(thumb_rect, 4, 4)
        painter.setClipPath(clip)
        if isinstance(pixmap, QtGui.QPixmap) and not pixmap.isNull():
            draw_cover(painter, thumb_rect, pixmap)
        else:
            painter.fillRect(thumb_rect, QtGui.QColor(t["elevated"]))
        painter.setClipping(False)

        text_x = thumb_rect.right() + 8
        text_w = rect.right() - text_x - 22

        name_font = QtGui.QFont(option.font)
        name_font.setPixelSize(11)
        name_font.setWeight(QtGui.QFont.Weight.DemiBold)
        painter.setFont(name_font)
        painter.setPen(QtGui.QColor(t["text"]))
        fm = QtGui.QFontMetrics(name_font)
        name = fm.elidedText(str(index.data(QtCore.Qt.DisplayRole)), QtCore.Qt.ElideRight, int(text_w))
        painter.drawText(
            QtCore.QRectF(text_x, rect.top() + 5, text_w, 16),
            int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter), name,
        )

        sub_font = QtGui.QFont(option.font)
        sub_font.setPixelSize(9)
        painter.setFont(sub_font)
        painter.setPen(QtGui.QColor(t["faint"]))
        painter.drawText(
            QtCore.QRectF(text_x, rect.top() + 21, text_w, 14),
            int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter),
            str(index.data(QtCore.Qt.UserRole + 1)),
        )

        # asa de arrastre
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(t["faint"]))
        cx = rect.right() - 11
        for row in range(3):
            for col in range(2):
                painter.drawEllipse(
                    QtCore.QRectF(cx + col * 4, rect.top() + 14 + row * 5, 2.2, 2.2))
        painter.restore()


# ---------------------------------------------------------------------------
# Diálogo de dependencias
# ---------------------------------------------------------------------------

class DependenciesDialog(QtWidgets.QDialog):
    DEPS = [
        ("mpvpaper", "Motor de reproducción del fondo", True),
        ("ffmpeg", "Miniaturas y frames de respaldo", True),
        ("ffprobe", "Duración de los videos", True),
        ("cosmic-bg", "Fondo estático de respaldo", False),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Requisitos del sistema")
        self.setMinimumWidth(520)
        self.distro = detect_distro()

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 18)
        lay.setSpacing(14)

        title = QtWidgets.QLabel(f"Requisitos · {self.distro['name']}")
        title.setStyleSheet("font-size: 15px; font-weight: 700;")
        lay.addWidget(title)

        intro = QtWidgets.QLabel(
            "Cosmic Wallpaper usa estas herramientas del sistema. "
            "El frame de respaldo evita que se vea un fondo negro entre videos."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: palette(mid);")
        lay.addWidget(intro)

        self.rows = {}
        for binary, description, needed in self.DEPS:
            row = QtWidgets.QHBoxLayout()
            dot = QtWidgets.QLabel()
            dot.setFixedWidth(14)
            row.addWidget(dot)
            name = QtWidgets.QLabel(f"<b>{binary}</b> — {description}")
            name.setWordWrap(True)
            row.addWidget(name, 1)
            state = QtWidgets.QLabel()
            row.addWidget(state)
            lay.addLayout(row)
            self.rows[binary] = (dot, state, needed)

        self.command_label = QtWidgets.QLabel()
        self.command_label.setWordWrap(True)
        self.command_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.command_label.setStyleSheet(
            "background: rgba(127,127,127,0.12); border-radius: 6px; padding: 8px;")
        lay.addWidget(self.command_label)

        buttons = QtWidgets.QHBoxLayout()
        self.btn_recheck = QtWidgets.QPushButton("Comprobar de nuevo")
        self.btn_recheck.setObjectName("DlgGhost")
        self.btn_recheck.clicked.connect(self.refresh)
        buttons.addWidget(self.btn_recheck)

        self.btn_copy = QtWidgets.QPushButton("Copiar comando")
        self.btn_copy.setObjectName("DlgGhost")
        self.btn_copy.clicked.connect(self.copy_command)
        buttons.addWidget(self.btn_copy)

        buttons.addStretch()

        self.btn_install = QtWidgets.QPushButton("Instalar faltantes")
        self.btn_install.setObjectName("DlgPrimary")
        self.btn_install.clicked.connect(self.install)
        buttons.addWidget(self.btn_install)

        btn_close = QtWidgets.QPushButton("Cerrar")
        btn_close.setObjectName("DlgGhost")
        btn_close.clicked.connect(self.accept)
        buttons.addWidget(btn_close)
        lay.addLayout(buttons)

        self.refresh()

    def missing(self) -> list[str]:
        return [binary for binary, _, _ in self.DEPS if not shutil.which(binary)]

    def install_packages(self) -> list[str]:
        packages = []
        for binary, _, _ in self.DEPS:
            if shutil.which(binary):
                continue
            if binary in ("ffmpeg", "ffprobe"):
                packages.append(self.distro["ffmpeg_pkg"])
            elif binary == "mpvpaper":
                packages.append(self.distro["mpvpaper_pkg"])
        return sorted(set(packages))

    def command(self) -> str:
        packages = self.install_packages()
        if not packages or not self.distro["install_cmd"]:
            return ""
        return f"{self.distro['install_cmd']} {' '.join(packages)}"

    def refresh(self):
        for binary, (dot, state, needed) in self.rows.items():
            found = bool(shutil.which(binary))
            dot.setText("●")
            dot.setObjectName("DepDotOk" if found else "DepDotBad")
            state.setText("disponible" if found else ("falta" if needed else "opcional"))
            state.setStyleSheet("color: palette(mid);")
            repolish(dot)

        command = self.command()
        if command:
            self.command_label.setText(command)
            self.command_label.show()
            self.btn_copy.setEnabled(True)
            self.btn_install.setEnabled(True)
        else:
            self.command_label.hide()
            self.btn_copy.setEnabled(False)
            self.btn_install.setEnabled(False)

    def copy_command(self):
        QtWidgets.QApplication.clipboard().setText(self.command())

    def install(self):
        command = self.command()
        if not command:
            return
        if launch_in_terminal(command):
            self.accept()
        else:
            QtWidgets.QMessageBox.information(
                self, "Comando para tu terminal",
                f"Abre tu terminal y ejecuta:\n\n{command}")


# ---------------------------------------------------------------------------
# Aplicación
# ---------------------------------------------------------------------------

class CosmicWallpaperApp(QtWidgets.QMainWindow):
    def __init__(self, restore: bool = True, test_deps: bool = False):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {VERSION}")
        self.resize(1200, 780)
        self.setMinimumSize(940, 600)
        self.setWindowIcon(QtGui.QIcon(app_pixmap(64)))

        self.config = self.load_config()
        Theme.set(self.config.get("theme", "dark"))

        self.folder = self.resolve_folder(self.config.get("folder"))
        self.favorites = {
            Path(p) for p in self.config.get("favorites", []) if Path(p).exists()
        }
        self.confirmed = [
            Path(p) for p in self.config.get("selected", []) if Path(p).exists()
        ]
        self.selection: list[Path] = list(self.confirmed)
        self.live: Path | None = None
        self.videos: list[Path] = []
        self.cards: list[VideoCard] = []
        self.filter = "all"
        self.query = ""
        self.mode = self.config.get("view", "grid")
        if self.mode not in ("grid", "list"):
            self.mode = "grid"
        self.rotation_mode = self.config.get("rotation_mode", "timer")
        if self.rotation_mode not in ("end", "timer"):
            self.rotation_mode = "timer"
        try:
            self.rotation_seconds = int(self.config.get("rotation_seconds", 35))
        except (TypeError, ValueError):
            self.rotation_seconds = 35
        self.rotation_seconds = max(5, min(3600, self.rotation_seconds))
        self._rotate_due = 0.0
        self._restore = restore and self.config.get("restore", True)
        self._cols = 0
        self._card_w = 0

        self.engine = WallpaperEngine(self)
        self.engine.changed.connect(self.on_engine_changed)

        self._apply_timer = QtCore.QTimer(self)
        self._apply_timer.setSingleShot(True)
        self._apply_timer.setInterval(320)
        self._apply_timer.timeout.connect(self.apply_selection)

        self.rotate_timer = QtCore.QTimer(self)
        self.rotate_timer.setSingleShot(True)
        self.rotate_timer.timeout.connect(self.advance_rotation)

        self.clock_timer = QtCore.QTimer(self)
        self.clock_timer.setInterval(1000)
        self.clock_timer.timeout.connect(self.update_countdown_ui)

        self.sync_timer = QtCore.QTimer(self)
        self.sync_timer.setInterval(2000)
        self.sync_timer.timeout.connect(self.sync_position)

        self._build_ui()
        self.apply_theme(Theme.name)
        self._build_tray()
        self.scan_folder()
        self.refresh_rotation()
        self.update_footer()

        QtCore.QTimer.singleShot(700, self.restore_last)
        missing = [b for b, _, needed in DependenciesDialog.DEPS
                   if needed and not shutil.which(b)]
        if missing:
            QtCore.QTimer.singleShot(350, lambda: DependenciesDialog(self).exec())
        if test_deps:
            QtCore.QTimer.singleShot(250, lambda: DependenciesDialog(self).exec())

    # -- configuración ---------------------------------------------------
    def load_config(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
        return {}

    def save_config(self):
        self.config.update({
            "folder": str(self.folder),
            "selected": [str(p) for p in self.confirmed],
            "favorites": [str(p) for p in sorted(self.favorites)],
            "theme": Theme.name,
            "view": self.mode,
            "rotation_mode": self.rotation_mode,
            "rotation_seconds": self.rotation_seconds,
            "restore": self.config.get("restore", True),
        })
        try:
            CONFIG_FILE.write_text(
                json.dumps(self.config, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def resolve_folder(self, value) -> Path:
        candidates = []
        if value:
            candidates.append(Path(value))
        candidates.append(HOME / "Vídeos")
        candidates.append(HOME / "Videos")
        for candidate in candidates:
            try:
                if candidate.is_dir():
                    return candidate
            except OSError:
                continue
        fallback = HOME / "Vídeos"
        try:
            fallback.mkdir(parents=True, exist_ok=True)
        except OSError:
            fallback = HOME
        return fallback

    # -- interfaz --------------------------------------------------------
    def _build_ui(self):
        root = QtWidgets.QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QtWidgets.QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_header())
        body = QtWidgets.QWidget()
        body_lay = QtWidgets.QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)
        body_lay.addWidget(self._build_sidebar())
        body_lay.addWidget(self._build_main(), 1)
        outer.addWidget(body, 1)
        outer.addWidget(self._build_footer())

    # ... header
    def _build_header(self) -> QtWidgets.QWidget:
        header = QtWidgets.QWidget()
        header.setObjectName("Header")
        header.setFixedHeight(68)
        lay = QtWidgets.QHBoxLayout(header)
        lay.setContentsMargins(20, 10, 20, 10)
        lay.setSpacing(12)

        icon = QtWidgets.QLabel()
        icon.setObjectName("AppIconLabel")
        icon.setFixedSize(38, 38)
        icon.setPixmap(app_pixmap(38))
        lay.addWidget(icon)

        titles = QtWidgets.QVBoxLayout()
        titles.setContentsMargins(0, 0, 0, 0)
        titles.setSpacing(3)

        title = QtWidgets.QLabel(APP_NAME)
        title.setObjectName("AppTitle")
        titles.addWidget(title)

        self.path_button = QtWidgets.QPushButton()
        self.path_button.setObjectName("PathChip")
        self.path_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.path_button.setIcon(make_icon("folder", Theme.c("muted"), 12))
        self.path_button.setIconSize(QtCore.QSize(12, 12))
        self.path_button.clicked.connect(self.select_folder)
        self.path_button.setToolTip("Cambiar carpeta de videos")
        titles.addWidget(self.path_button, 0, QtCore.Qt.AlignLeft)
        lay.addLayout(titles)

        lay.addStretch()

        self.search = QtWidgets.QLineEdit()
        self.search.setObjectName("Search")
        self.search.setPlaceholderText("Buscar videos…")
        self.search.setFixedWidth(230)
        self.search.setClearButtonEnabled(True)
        self.search.addAction(make_icon("search", Theme.c("muted"), 14),
                              QtWidgets.QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(self.on_search)
        lay.addWidget(self.search)

        self.btn_refresh = self._icon_button("refresh", "Recargar carpeta")
        self.btn_refresh.clicked.connect(self.scan_folder)
        lay.addWidget(self.btn_refresh)

        self.btn_settings = self._icon_button("gear", "Ajustes")
        self.btn_settings.clicked.connect(self.open_settings_menu)
        lay.addWidget(self.btn_settings)

        self.update_path_label()
        return header

    def _icon_button(self, icon_name: str, tooltip: str) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton()
        btn.setObjectName("IconBtn")
        btn.setFixedSize(32, 32)
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setProperty("iconName", icon_name)
        btn.setIcon(make_icon(icon_name, Theme.c("muted"), 16))
        btn.setIconSize(QtCore.QSize(16, 16))
        return btn

    # ... sidebar
    def _build_sidebar(self) -> QtWidgets.QWidget:
        side = QtWidgets.QFrame()
        side.setObjectName("Sidebar")
        side.setFixedWidth(250)
        lay = QtWidgets.QVBoxLayout(side)
        lay.setContentsMargins(12, 12, 12, 10)
        lay.setSpacing(8)

        lay.addWidget(self._section_label("Biblioteca"))

        self.nav_items: dict[str, NavItem] = {}
        for key, icon_name, text in (
            ("all", "video", "Todos los videos"),
            ("favorites", "star", "Favoritos"),
            ("recent", "clock", "Recientes"),
        ):
            item = NavItem(key, icon_name, text)
            item.clicked.connect(self.set_filter)
            lay.addWidget(item)
            self.nav_items[key] = item
        self.nav_items["all"].set_active(True)

        divider = QtWidgets.QFrame()
        divider.setObjectName("Divider")
        lay.addWidget(divider)

        rot_head = QtWidgets.QHBoxLayout()
        rot_head.setContentsMargins(0, 0, 0, 0)
        self.rot_title = self._section_label("En rotación · 0")
        rot_head.addWidget(self.rot_title)
        rot_head.addStretch()
        lay.addLayout(rot_head)

        self.rot_list = QtWidgets.QListWidget()
        self.rot_list.setObjectName("Rotation")
        self.rot_list.setItemDelegate(RotationDelegate(self.rot_list))
        self.rot_list.setMouseTracking(True)
        self.rot_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.rot_list.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.rot_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.rot_list.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.rot_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.rot_list.setMinimumHeight(44)
        self.rot_list.setMaximumHeight(220)
        self.rot_list.itemDoubleClicked.connect(self._rotation_preview)
        self.rot_list.model().rowsMoved.connect(
            lambda *_: QtCore.QTimer.singleShot(0, self._rotation_reordered))
        self.rot_empty = QtWidgets.QLabel(
            "Aún no hay videos en la rotación. Marca una casilla o usa el botón de abajo.")
        self.rot_empty.setObjectName("StatusSub")
        self.rot_empty.setWordWrap(True)
        lay.addWidget(self.rot_empty)
        lay.addWidget(self.rot_list)

        self.btn_rot_add = QtWidgets.QPushButton("  Añadir a la rotación")
        self.btn_rot_add.setObjectName("RotAdd")
        self.btn_rot_add.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_rot_add.setProperty("iconName", "plus")
        self.btn_rot_add.setIcon(make_icon("plus", Theme.c("faint"), 12))
        self.btn_rot_add.clicked.connect(self.add_live_to_rotation)
        lay.addWidget(self.btn_rot_add)
        lay.addStretch(1)

        self.deps_card = self._build_deps_card()
        lay.addWidget(self.deps_card)
        return side

    def _section_label(self, text: str) -> QtWidgets.QLabel:
        label = QtWidgets.QLabel(text.upper())
        label.setObjectName("Section")
        return label

    def _build_deps_card(self) -> QtWidgets.QFrame:
        card = ClickableFrame()
        card.setObjectName("Deps")
        card.setToolTip("Comprobar requisitos del sistema")
        lay = QtWidgets.QVBoxLayout(card)
        lay.setContentsMargins(10, 9, 10, 9)
        lay.setSpacing(5)

        self.dep_rows = {}
        for binary, label, needed in DependenciesDialog.DEPS:
            row = QtWidgets.QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(7)
            dot = QtWidgets.QLabel("●")
            dot.setObjectName("DepDotOk" if shutil.which(binary) else "DepDotBad")
            row.addWidget(dot)
            name = QtWidgets.QLabel(f"<b>{binary}</b>")
            row.addWidget(name)
            state = QtWidgets.QLabel(
                "disponible" if shutil.which(binary) else ("falta" if needed else "opcional"))
            row.addStretch()
            row.addWidget(state)
            lay.addLayout(row)
            self.dep_rows[binary] = dot

        foot = QtWidgets.QHBoxLayout()
        self.buffer_label = QtWidgets.QLabel("Búfer en RAM")
        self.buffer_label.setObjectName("DepsFoot")
        foot.addWidget(self.buffer_label)
        foot.addStretch()
        self.buffer_value = QtWidgets.QLabel("0 MB")
        self.buffer_value.setObjectName("DepsFoot")
        foot.addWidget(self.buffer_value)
        lay.addLayout(foot)

        card.clicked.connect(lambda: DependenciesDialog(self).exec())
        return card

    # ... main
    def _build_main(self) -> QtWidgets.QWidget:
        main = QtWidgets.QWidget()
        main.setObjectName("Main")
        lay = QtWidgets.QVBoxLayout(main)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        toolbar = QtWidgets.QWidget()
        toolbar.setFixedHeight(52)
        row = QtWidgets.QHBoxLayout(toolbar)
        row.setContentsMargins(22, 0, 22, 0)
        row.setSpacing(10)

        self.count_label = QtWidgets.QLabel("0 videos")
        self.count_label.setObjectName("ToolbarCount")
        row.addWidget(self.count_label)
        row.addStretch()

        seg = QtWidgets.QFrame()
        seg.setObjectName("Seg")
        seg_lay = QtWidgets.QHBoxLayout(seg)
        seg_lay.setContentsMargins(3, 3, 3, 3)
        seg_lay.setSpacing(2)

        self.btn_grid = self._view_button("grid", "Cuadrícula")
        self.btn_grid.clicked.connect(lambda: self.set_view("grid"))
        seg_lay.addWidget(self.btn_grid)
        self.btn_list = self._view_button("list", "Lista")
        self.btn_list.clicked.connect(lambda: self.set_view("list"))
        seg_lay.addWidget(self.btn_list)
        row.addWidget(seg)
        lay.addWidget(toolbar)

        self.scroll = ScrollArea()
        self.scroll.setObjectName("Scroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.resized.connect(self._relayout)
        lay.addWidget(self.scroll, 1)

        self.set_view(self.mode, render=False)
        return main

    def _view_button(self, icon_name: str, tooltip: str) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton()
        btn.setObjectName("ViewBtn")
        btn.setFixedSize(32, 26)
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setIcon(make_icon(icon_name, Theme.c("muted"), 14))
        btn.setIconSize(QtCore.QSize(14, 14))
        btn.setProperty("iconName", icon_name)
        return btn

    # ... footer
    def _build_footer(self) -> QtWidgets.QWidget:
        footer = QtWidgets.QFrame()
        footer.setObjectName("Footer")
        footer.setFixedHeight(78)
        lay = QtWidgets.QHBoxLayout(footer)
        lay.setContentsMargins(22, 10, 20, 10)
        lay.setSpacing(18)

        status = QtWidgets.QVBoxLayout()
        status.setContentsMargins(0, 0, 0, 0)
        status.setSpacing(3)
        status.addStretch(1)

        line = QtWidgets.QHBoxLayout()
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(7)
        self.live_dot = QtWidgets.QLabel("●")
        self.live_dot.setObjectName("LiveDot")
        line.addWidget(self.live_dot)

        self.status_now = QtWidgets.QLabel("Sin fondo activo")
        self.status_now.setObjectName("StatusNow")
        self.status_now.setMaximumWidth(300)
        line.addWidget(self.status_now)

        self.status_next = QtWidgets.QLabel("")
        self.status_next.setObjectName("StatusMuted")
        self.status_next.setMaximumWidth(470)
        line.addWidget(self.status_next)
        line.addStretch()
        status.addLayout(line)

        self.buffer_bar = QtWidgets.QProgressBar()
        self.buffer_bar.setObjectName("Buffer")
        self.buffer_bar.setRange(0, 100)
        self.buffer_bar.setValue(0)
        self.buffer_bar.setTextVisible(False)
        self.buffer_bar.setFixedWidth(420)
        self.buffer_bar.setFixedHeight(3)
        status.addWidget(self.buffer_bar)

        self.status_sub = QtWidgets.QLabel("Selecciona un video para verlo en vivo.")
        self.status_sub.setObjectName("StatusSub")
        status.addWidget(self.status_sub)
        status.addStretch(1)
        lay.addLayout(status, 1)

        self.btn_stop = QtWidgets.QPushButton("Detener")
        self.btn_stop.setObjectName("Ghost")
        self.btn_stop.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_stop.setProperty("iconName", "stop")
        self.btn_stop.setIcon(make_icon("stop", Theme.c("text"), 14))
        self.btn_stop.clicked.connect(self.stop_wallpaper)
        lay.addWidget(self.btn_stop)

        self.btn_confirm = QtWidgets.QPushButton("Confirmar selección")
        self.btn_confirm.setObjectName("Primary")
        self.btn_confirm.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_confirm.setProperty("iconName", "check")
        self.btn_confirm.setIcon(make_icon("check", Theme.c("accent_fg"), 14))
        self.btn_confirm.clicked.connect(self.confirm_selection)
        lay.addWidget(self.btn_confirm)
        return footer

    # -- tema ------------------------------------------------------------
    def apply_theme(self, name: str):
        Theme.set(name)
        app = QtWidgets.QApplication.instance()
        if app:
            app.setStyleSheet(build_qss(Theme.tokens))
        self.setWindowIcon(QtGui.QIcon(app_pixmap(64)))
        self.refresh_icons()
        for card in self.cards:
            card.update()
            card.thumb.update()
        self.rot_list.viewport().update()
        self.update_footer()

    def refresh_icons(self):
        t = Theme.tokens
        for widget in self.findChildren(QtWidgets.QPushButton):
            icon_name = widget.property("iconName")
            if not icon_name:
                continue
            name = widget.objectName()
            if name == "Primary":
                color = t["accent_fg"]
            elif name == "Ghost":
                color = t["text"]
            elif name == "PathChip":
                color = t["muted"]
            elif name == "RotAdd":
                color = t["faint"]
            else:
                color = t["muted"]
            size = 12 if name == "PathChip" else (14 if name == "ViewBtn" else 16)
            widget.setIcon(make_icon(icon_name, color, size))
        for item in self.nav_items.values():
            icon_name = item.icon_label.property("iconName")
            item.icon_label.setPixmap(make_pixmap(icon_name, t["muted"], 15))
        header_icon = self.findChild(QtWidgets.QLabel, "AppIconLabel")
        if header_icon:
            header_icon.setPixmap(app_pixmap(38))

    def open_settings_menu(self):
        menu = QtWidgets.QMenu(self)
        theme_menu = menu.addMenu("Tema")
        act_dark = theme_menu.addAction("Oscuro")
        act_dark.setCheckable(True)
        act_dark.setChecked(Theme.name == "dark")
        act_light = theme_menu.addAction("Claro")
        act_light.setCheckable(True)
        act_light.setChecked(Theme.name == "light")
        act_dark.triggered.connect(lambda: self.change_theme("dark"))
        act_light.triggered.connect(lambda: self.change_theme("light"))

        rotation_menu = menu.addMenu("Rotación")
        act_end = rotation_menu.addAction("Al terminar cada video")
        act_end.setCheckable(True)
        act_end.setChecked(self.rotation_mode == "end")
        act_end.triggered.connect(lambda: self.set_rotation(None))

        act_timer = rotation_menu.addAction(
            f"Cada {self.rotation_seconds} segundos…")
        act_timer.setCheckable(True)
        act_timer.setChecked(self.rotation_mode == "timer")
        act_timer.triggered.connect(lambda: self.edit_rotation_interval())

        rotation_menu.addSeparator()
        for seconds in (10, 15, 20, 30, 35, 60):
            action = rotation_menu.addAction(f"{seconds} segundos")
            action.setCheckable(True)
            action.setChecked(
                self.rotation_mode == "timer" and self.rotation_seconds == seconds)
            action.triggered.connect(
                lambda checked=False, value=seconds: self.set_rotation(value))

        menu.addSeparator()
        act_restore = menu.addAction("Restaurar último fondo al iniciar")
        act_restore.setCheckable(True)
        act_restore.setChecked(self.config.get("restore", True))
        act_restore.toggled.connect(self.set_restore_enabled)

        act_deps = menu.addAction("Comprobar requisitos")
        act_deps.triggered.connect(lambda: DependenciesDialog(self).exec())

        act_folder = menu.addAction("Cambiar carpeta de videos")
        act_folder.triggered.connect(self.select_folder)

        menu.addSeparator()
        act_about = menu.addAction(f"Acerca de {APP_NAME}")
        act_about.triggered.connect(self.show_about)

        menu.exec(self.btn_settings.mapToGlobal(
            QtCore.QPoint(0, self.btn_settings.height() + 4)))

    def change_theme(self, name: str):
        self.apply_theme(name)
        self.save_config()

    def set_restore_enabled(self, enabled: bool):
        self.config["restore"] = enabled
        self.save_config()

    # -- datos -----------------------------------------------------------
    def scan_folder(self):
        try:
            entries = list(self.folder.iterdir())
        except OSError:
            self.videos = []
            self.status_sub.setText(f"No se pudo leer la carpeta: {self.folder}")
            self.render_cards()
            return

        self.videos = sorted(
            (p for p in entries if p.is_file() and p.suffix.lower() in VIDEO_EXT),
            key=lambda p: p.name.lower(),
        )
        for video in self.videos:
            probe_duration(video)

        self.render_cards()
        self.refresh_counts()
        if self.videos:
            self.status_sub.setText(
                "Haz clic en un video para verlo en vivo · usa las casillas para la rotación.")
        else:
            self.status_sub.setText("No se encontraron videos en esta carpeta.")

    def refresh_counts(self):
        self.nav_items["all"].set_count(len(self.videos))
        self.nav_items["favorites"].set_count(
            sum(1 for v in self.videos if v in self.favorites))
        self.nav_items["recent"].set_count(
            min(12, len(self.videos)))
        self.count_label.setText(f"{len(self.visible_videos())} videos")

    def visible_videos(self) -> list[Path]:
        videos = list(self.videos)
        if self.filter == "favorites":
            videos = [v for v in videos if v in self.favorites]
        elif self.filter == "recent":
            def mtime(path: Path) -> float:
                try:
                    return path.stat().st_mtime
                except OSError:
                    return 0.0
            videos = sorted(videos, key=mtime, reverse=True)[:12]
        if self.query:
            needle = self.query.lower()
            videos = [v for v in videos if needle in v.name.lower()]
        return videos

    def render_cards(self):
        old = self.scroll.takeWidget()
        cards: list[VideoCard] = []
        videos = self.visible_videos()

        if not videos:
            body = QtWidgets.QWidget()
            body.setObjectName("ScrollBody")
            lay = QtWidgets.QVBoxLayout(body)
            message = ("Sin resultados para tu búsqueda." if self.query else
                       "No hay videos en esta vista." if self.videos else
                       "No se encontraron videos en esta carpeta.\n"
                       "Usa la ruta de arriba para elegir otra carpeta.")
            label = QtWidgets.QLabel(message)
            label.setObjectName("Empty")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setWordWrap(True)
            lay.addWidget(label)
            self.scroll.setWidget(body)
            if old is not None:
                old.deleteLater()
            self.cards = []
            self.count_label.setText("0 videos")
            return

        if self.mode == "grid":
            body = QtWidgets.QWidget()
            body.setObjectName("ScrollBody")
            self._grid = QtWidgets.QGridLayout(body)
            self._grid.setContentsMargins(22, 4, 22, 20)
            self._grid.setSpacing(CARD_GAP)
            self._grid.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        else:
            body = QtWidgets.QWidget()
            body.setObjectName("ScrollBody")
            self._grid = QtWidgets.QVBoxLayout(body)
            self._grid.setContentsMargins(22, 4, 22, 20)
            self._grid.setSpacing(6)
            self._grid.setAlignment(QtCore.Qt.AlignTop)

        for video in videos:
            card = VideoCard(
                video,
                mode=self.mode,
                selected=video in self.selection,
                live=video == self.live,
                buffered=video in self.selection,
                favorite=video in self.favorites,
                duration=_duration_cache.get(video, 0.0),
            )
            card.clicked.connect(self.on_card_clicked)
            card.toggled.connect(self.on_card_toggled)
            card.favorite_requested.connect(self.toggle_favorite)
            card.add_requested.connect(self.add_to_rotation)
            card.remove_requested.connect(self.remove_from_rotation)
            cards.append(card)

        if self.mode == "grid":
            self._cols = 0
            self._card_w = 0
            self._layout_grid(cards, self.scroll.viewport().width())
            QtCore.QTimer.singleShot(0, self._relayout)
        else:
            for card in cards:
                self._grid.addWidget(card)
            self._grid.addStretch(1)

        self.cards = cards
        self.scroll.setWidget(body)
        if old is not None:
            old.deleteLater()
        self.count_label.setText(f"{len(videos)} videos")

    def _layout_grid(self, cards: list[VideoCard], width: int):
        spacing = CARD_GAP
        available = max(width - 44, CARD_MIN_W)
        cols = max(1, (available + spacing) // (CARD_MIN_W + spacing))
        card_w = (available - (cols - 1) * spacing) // cols
        card_w = max(CARD_MIN_W, min(CARD_MAX_W, card_w))
        if cols == self._cols and card_w == self._card_w:
            return
        self._cols = cols
        self._card_w = card_w

        while self._grid.count():
            self._grid.takeAt(0)

        card_h = round(card_w * 9 / 16) + CARD_META_H + 4
        rows = max(1, (len(cards) + cols - 1) // cols)
        body = self._grid.parentWidget()
        if body is not None:
            body.setMinimumHeight(rows * card_h + (rows - 1) * spacing + 24)

        for index, card in enumerate(cards):
            card.set_grid_width(card_w)
            self._grid.addWidget(card, index // cols, index % cols)

    def _relayout(self):
        if self.mode != "grid" or not self.cards:
            return
        if not hasattr(self, "_grid"):
            return
        self._layout_grid(self.cards, self.scroll.viewport().width())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout()

    def set_view(self, mode: str, render: bool = True):
        self.mode = mode if mode in ("grid", "list") else "grid"
        for btn, key in ((self.btn_grid, "grid"), (self.btn_list, "list")):
            btn.setProperty("active", key == self.mode)
            repolish(btn)
        if render:
            self.render_cards()
        self.save_config()

    def set_filter(self, key: str):
        self.filter = key
        for name, item in self.nav_items.items():
            item.set_active(name == key)
        self.render_cards()
        self.refresh_counts()

    def on_search(self, text: str):
        self.query = text.strip()
        self.render_cards()
        self.refresh_counts()

    # -- selección y reproducción ---------------------------------------
    def launch(self, videos, start_index: int = 0) -> bool:
        videos = [Path(v) for v in videos]
        ok = self.engine.start(videos, start_index)
        if ok:
            self.engine.index = max(0, min(start_index, len(videos) - 1))
            self.live = videos[self.engine.index]
        self.restart_rotation_clock()
        return ok

    def on_card_clicked(self, path: Path):
        if not self.engine.mpvpaper:
            DependenciesDialog(self).exec()
            return
        self.live = path
        if self.launch([path]):
            self.status_sub.setText(
                f"Vista previa en vivo: {path.stem} · confirma para fijarlo.")
        else:
            self.status_sub.setText("No se pudo iniciar mpvpaper.")
        self.refresh_card_states()
        self.update_footer()

    def on_card_toggled(self, path: Path, checked: bool):
        if checked:
            if path not in self.selection:
                self.selection.append(path)
        else:
            if path in self.selection:
                self.selection.remove(path)
        self.refresh_rotation()
        self.refresh_card_states()
        self.refresh_counts()
        self._apply_timer.start()

    def apply_selection(self):
        if not self.selection:
            if self.engine.running():
                self.engine.stop(restore_background=True)
            self.live = None
            self.status_sub.setText("Ningún video seleccionado.")
            self.refresh_card_states()
            self.update_footer()
            return

        if self.engine.playlist == self.selection and self.engine.running():
            return

        if self.launch(self.selection):
            count = len(self.selection)
            self.status_sub.setText(
                f"{count} video{'s' if count != 1 else ''} en rotación con búfer activo.")
        else:
            self.status_sub.setText("No se pudo iniciar mpvpaper.")
        self.refresh_card_states()
        self.update_footer()

    # -- temporizador de rotación ----------------------------------------
    def timer_rotation_active(self) -> bool:
        return (self.rotation_mode == "timer" and self.engine.running()
                and len(self.engine.playlist) > 1)

    def restart_rotation_clock(self):
        self.rotate_timer.stop()
        self.clock_timer.stop()
        self.sync_timer.stop()
        if not self.engine.running():
            self.update_footer()
            return
        self.sync_timer.start()
        if self.engine.paused:
            return
        if self.timer_rotation_active():
            self._rotate_due = time.monotonic() + self.rotation_seconds
            self.rotate_timer.start(self.rotation_seconds * 1000)
            self.clock_timer.start()
        self.update_countdown_ui()

    def advance_rotation(self, force: bool = False):
        if not force and not self.timer_rotation_active():
            return
        if not self.engine.running() or len(self.engine.playlist) < 2:
            return
        playlist = self.engine.playlist

        # Si mpv avanzó solo (video más corto que el intervalo), partimos de
        # la posición real antes de pedir el siguiente.
        current = self.engine.current_index()
        if current is not None and 0 <= current < len(playlist):
            self.engine.index = current
            self.live = playlist[current]

        if not self.engine.next_video():
            # Respaldo: si el socket IPC no responde, relanzamos empezando
            # por el siguiente video.
            nxt = (self.engine.index + 1) % len(playlist)
            if not self.launch(playlist, nxt):
                return
            playlist = self.engine.playlist
        else:
            self.engine.index = (self.engine.index + 1) % len(playlist)

        if 0 <= self.engine.index < len(playlist):
            self.live = playlist[self.engine.index]
        self.refresh_card_states()
        self.update_footer()
        self.restart_rotation_clock()

    def sync_position(self):
        """Sincroniza el badge EN VIVO con el video que mpv está mostrando."""
        if not self.engine.running():
            self.sync_timer.stop()
            return
        position = self.engine.current_index()
        if (position is None or position == self.engine.index
                or position >= len(self.engine.playlist)):
            return
        self.engine.index = position
        self.live = self.engine.playlist[position]
        self.refresh_card_states()
        self.update_footer()

    def update_countdown_ui(self):
        if not self.engine.running():
            return
        playlist = self.engine.playlist
        if len(playlist) < 2 or self.rotation_mode != "timer":
            return
        index = self.engine.index % len(playlist)
        nxt = playlist[(index + 1) % len(playlist)]
        remaining = max(0, int(round(self._rotate_due - time.monotonic())))
        set_elided_label(
            self.status_next,
            f"· siguiente {nxt.stem} · cambia en {format_duration(remaining)}",
            460,
        )
        total = max(1, self.rotation_seconds)
        progress = int(max(0, min(100, (1 - remaining / total) * 100)))
        self.buffer_bar.setValue(progress)

    def set_rotation(self, seconds: int | None):
        if seconds is None:
            self.rotation_mode = "end"
        else:
            self.rotation_mode = "timer"
            self.rotation_seconds = max(5, min(3600, int(seconds)))
        self.save_config()
        self.restart_rotation_clock()
        self.update_footer()
        mode_text = ("al terminar cada video" if self.rotation_mode == "end"
                     else f"cada {self.rotation_seconds} segundos")
        self.status_sub.setText(f"Rotación {mode_text}.")

    def edit_rotation_interval(self):
        value, accepted = QtWidgets.QInputDialog.getInt(
            self, "Intervalo de rotación",
            "Cambiar de video cada (segundos):",
            self.rotation_seconds, 5, 3600, 5,
        )
        if accepted:
            self.set_rotation(value)

    def confirm_selection(self):
        if not self.selection and self.live is not None:
            self.selection = [self.live]
            self.refresh_rotation()
        if not self.selection:
            QtWidgets.QMessageBox.warning(
                self, "Sin selección",
                "Marca al menos un video con la casilla antes de confirmar.")
            return
        self.confirmed = list(self.selection)
        self.save_config()
        if not (self.engine.running() and self.engine.playlist == self.confirmed):
            self.launch(self.confirmed)
        else:
            self.restart_rotation_clock()
        self.refresh_card_states()
        self.update_footer()

        count = len(self.confirmed)
        message = (f"Fondo fijado: {self.confirmed[0].stem}" if count == 1
                   else f"Rotación de {count} videos fijada")
        self.status_sub.setText(f"{message} · se restaurará al iniciar.")
        QtWidgets.QToolTip.showText(
            self.btn_confirm.mapToGlobal(QtCore.QPoint(0, -34)), message, self.btn_confirm)
        self.tray_message(message)

    def stop_wallpaper(self):
        self.engine.stop(restore_background=True)
        self.rotate_timer.stop()
        self.clock_timer.stop()
        self.sync_timer.stop()
        self.live = None
        self.refresh_card_states()
        self.update_footer()
        self.status_sub.setText(
            "Fondo detenido · tu selección sigue guardada para reanudarla.")

    def add_live_to_rotation(self):
        target = self.live or (self.selection[0] if self.selection else None)
        if target is None:
            self.status_sub.setText(
                "Primero haz clic en un video para añadirlo a la rotación.")
            return
        self.add_to_rotation(target)

    def add_to_rotation(self, path: Path):
        if path in self.selection:
            self.status_sub.setText(f"{path.stem} ya está en la rotación.")
            return
        self.selection.append(path)
        self.refresh_rotation()
        self.refresh_card_states()
        self.refresh_counts()
        self._apply_timer.start()

    def remove_from_rotation(self, path: Path):
        if path in self.selection:
            self.selection.remove(path)
            self.refresh_rotation()
            self.refresh_card_states()
            self.refresh_counts()
            self._apply_timer.start()

    def toggle_favorite(self, path: Path):
        if path in self.favorites:
            self.favorites.discard(path)
        else:
            self.favorites.add(path)
        self.save_config()
        self.render_cards()
        self.refresh_counts()

    # -- lista de rotación -----------------------------------------------
    def refresh_rotation(self):
        self.rot_list.blockSignals(True)
        self.rot_list.clear()
        for index, path in enumerate(self.selection):
            item = QtWidgets.QListWidgetItem(path.stem)
            thumb = get_thumbnail(path)
            if thumb:
                pm = QtGui.QPixmap(str(thumb))
                if not pm.isNull():
                    item.setData(QtCore.Qt.UserRole + 2, pm)
            item.setData(QtCore.Qt.UserRole, str(path))
            item.setData(QtCore.Qt.UserRole + 1,
                         f"{format_duration(_duration_cache.get(path, 0.0))} · "
                         f"{index + 1}º turno")
            item.setToolTip(f"{path.name}\nArrastra para cambiar el orden")
            self.rot_list.addItem(item)
        self.rot_list.blockSignals(False)
        self.rot_title.setText(f"EN ROTACIÓN · {len(self.selection)}")
        count = len(self.selection)
        self.rot_empty.setVisible(count == 0)
        self.rot_list.setVisible(count > 0)
        self.rot_list.setFixedHeight(max(44, min(220, count * 44 + 4)))
        self.btn_rot_add.setEnabled(bool(self.videos))
        self.update_buffer_label()

    def _rotation_items(self) -> list[Path]:
        result = []
        for index in range(self.rot_list.count()):
            item = self.rot_list.item(index)
            path = Path(item.data(QtCore.Qt.UserRole))
            if path in self.selection:
                result.append(path)
        return result

    def _rotation_reordered(self):
        new_order = self._rotation_items()
        if not new_order or new_order == self.selection:
            return
        self.selection = new_order
        for index, path in enumerate(self.selection):
            for row in range(self.rot_list.count()):
                item = self.rot_list.item(row)
                if Path(item.data(QtCore.Qt.UserRole)) == path:
                    item.setData(QtCore.Qt.UserRole + 1,
                                 f"{format_duration(_duration_cache.get(path, 0.0))} · "
                                 f"{index + 1}º turno")
        if self.engine.running() and not self.engine.paused:
            self.launch(self.selection)
            self.refresh_card_states()
            self.update_footer()

    def _rotation_preview(self, item: QtWidgets.QListWidgetItem):
        path = Path(item.data(QtCore.Qt.UserRole))
        if path.exists():
            self.on_card_clicked(path)

    # -- estado visual ----------------------------------------------------
    def refresh_card_states(self):
        for card in self.cards:
            selected = card.path in self.selection
            live = card.path == self.live
            buffered = card.path in self.selection
            card.set_states(selected, live, buffered)

    def update_buffer_label(self):
        total = 0
        for path in self.selection:
            try:
                total += path.stat().st_size
            except OSError:
                continue
        count = len(self.selection)
        self.buffer_value.setText(human_mb(total) if count else "0 MB")
        self.buffer_label.setText(f"Búfer · {count} video{'s' if count != 1 else ''}")

    def update_footer(self):
        running = self.engine.running()
        paused = self.engine.paused
        t = Theme.tokens

        if running:
            playlist = self.engine.playlist
            index = self.engine.index if 0 <= self.engine.index < len(playlist) else 0
            now = self.live or (playlist[index] if playlist else None)
            set_elided_label(self.status_now, now.stem if now else "Reproduciendo", 300)
            if len(playlist) > 1:
                nxt = playlist[(index + 1) % len(playlist)]
                set_elided_label(
                    self.status_next, f"· siguiente {nxt.stem} · precargado", 460)
            else:
                set_elided_label(self.status_next, "· en bucle", 460)
            self.live_dot.setStyleSheet(f"color: {t['accent']};")
            self.buffer_bar.setValue(100)
            self.update_countdown_ui()
        else:
            set_elided_label(self.status_now, "Sin fondo activo", 300)
            set_elided_label(self.status_next, "", 460)
            self.live_dot.setStyleSheet(f"color: {t['faint']};")
            self.buffer_bar.setValue(0)

        if paused:
            self.status_sub.setText("Pausado · el video se reanuda desde el mismo punto.")
        self.update_buffer_label()

    def on_engine_changed(self):
        if not self.engine.running():
            self.rotate_timer.stop()
            self.clock_timer.stop()
            self.sync_timer.stop()
            if self.live is not None:
                self.live = None
                self.refresh_card_states()
            self.update_footer()
            return
        if self.engine.paused:
            self.rotate_timer.stop()
            self.clock_timer.stop()
        else:
            self.restart_rotation_clock()
        self.update_footer()

    def restore_last(self):
        if not self._restore or not self.confirmed:
            return
        if self.engine.running():
            return
        if self.launch(self.confirmed):
            self.selection = list(self.confirmed)
            self.refresh_card_states()
            self.refresh_rotation()
            self.update_footer()
            self.status_sub.setText(
                f"Restaurado: {self.confirmed[0].stem}"
                + (f" y {len(self.confirmed) - 1} más en rotación"
                   if len(self.confirmed) > 1 else ""))

    # -- ventana y bandeja ------------------------------------------------
    def update_path_label(self):
        try:
            shown = "~/" + str(self.folder.relative_to(HOME))
        except ValueError:
            shown = str(self.folder)
        self.path_button.setText("  " + shown)
        self.path_button.setToolTip(str(self.folder))

    def select_folder(self):
        chosen = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de videos", str(self.folder))
        if chosen:
            self.folder = Path(chosen)
            self.update_path_label()
            self.save_config()
            self.scan_folder()

    def _build_tray(self):
        self.tray = None
        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QtWidgets.QSystemTrayIcon(
            QtGui.QIcon(app_pixmap(64)), self)
        self.tray.setToolTip(f"{APP_NAME} {VERSION}")
        menu = QtWidgets.QMenu(self)

        act_show = menu.addAction("Abrir selector de videos")
        act_show.triggered.connect(self.show_normal_window)

        self.act_pause = menu.addAction("Pausar fondo")
        self.act_pause.triggered.connect(self.toggle_pause)

        act_stop = menu.addAction("Detener fondo")
        act_stop.triggered.connect(self.stop_wallpaper)

        act_next = menu.addAction("Siguiente video")
        act_next.triggered.connect(lambda: self.advance_rotation(force=True))

        menu.addSeparator()
        act_about = menu.addAction(f"Acerca de {APP_NAME}")
        act_about.triggered.connect(self.show_about)
        menu.addSeparator()
        act_quit = menu.addAction("Salir")
        act_quit.triggered.connect(self.quit_app)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def toggle_pause(self):
        if not self.engine.running():
            self.status_sub.setText("No hay ningún fondo reproduciéndose.")
            return
        self.engine.toggle_paused()
        if self.tray is not None and hasattr(self, "act_pause"):
            self.act_pause.setText(
                "Reanudar fondo" if self.engine.paused else "Pausar fondo")
        self.status_sub.setText(
            "Fondo pausado." if self.engine.paused else "Fondo reanudado.")
        self.update_footer()

    def on_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.show_normal_window()

    def show_normal_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def tray_message(self, text: str):
        if self.tray is not None:
            self.tray.showMessage(APP_NAME, text,
                                  QtWidgets.QSystemTrayIcon.Information, 2500)

    def show_about(self):
        QtWidgets.QMessageBox.about(
            self, f"Acerca de {APP_NAME}",
            f"<h3>{APP_NAME} {VERSION}</h3>"
            "<p>Fondo animado para COSMIC Desktop con búfer de doble capa: "
            "caché en RAM y frame estático de respaldo.</p>"
            f"<p><b>Autor:</b> {AUTHOR_NAME}<br>"
            f"<a href='{GITHUB_URL}'>{GITHUB_URL}</a></p>")

    def closeEvent(self, event):
        if self.tray is not None:
            event.ignore()
            self.hide()
            self.tray_message("La aplicación sigue activa en la bandeja del sistema.")
        else:
            self.quit_app()

    def quit_app(self):
        self.engine.stop(restore_background=True)
        if self.tray is not None:
            self.tray.hide()
        QtWidgets.QApplication.quit()


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]
    if "--version" in args:
        print(f"{APP_NAME} {VERSION}")
        return 0
    if "-k" in args or "--stop" in args:
        return stop_from_cli()

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("cosmic-wallpaper")
    app.setApplicationDisplayName(APP_NAME)
    app.setDesktopFileName("cosmic-wallpaper")
    app.setQuitOnLastWindowClosed(False)

    window = CosmicWallpaperApp(
        restore="--no-restore" not in args,
        test_deps="--test-deps" in args,
    )
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
