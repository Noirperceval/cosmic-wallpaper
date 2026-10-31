#!/usr/bin/env bash
# install.sh — Instalador de Cosmic Wallpaper 2.0
# Creado por: Noir Perceval (Daniel Chable)
# GitHub: https://github.com/Noirperceval/cosmic-wallpaper
#
# Instala el lanzador en el menú de aplicaciones, el acceso para detener el
# fondo y el inicio automático con la sesión de COSMIC Desktop.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$SCRIPT_DIR/cosmic_wallpaper_gui.py"
ICON_SRC="$SCRIPT_DIR/io.github.Noirperceval.CosmicWallpaper.svg"
ICON_NAME="io.github.Noirperceval.CosmicWallpaper"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
APPLICATIONS="$HOME/.local/share/applications"
AUTOSTART="$HOME/.config/autostart"

echo "==> Instalando Cosmic Wallpaper..."

# 0. Comprobaciones rápidas
if ! command -v python3 >/dev/null 2>&1; then
    echo "✗ Falta python3. Instálalo con el gestor de paquetes de tu distribución." >&2
    exit 1
fi
if ! python3 -c "import PySide6" >/dev/null 2>&1; then
    echo "✗ Falta PySide6. Instálalo, por ejemplo:  pip install --user PySide6" >&2
    echo "  (En Arch: sudo pacman -S python-pyside6)" >&2
    exit 1
fi
for bin in mpvpaper ffmpeg ffprobe; do
    if ! command -v "$bin" >/dev/null 2>&1; then
        echo "⚠ No se encontró '$bin'. La app abrirá su asistente de requisitos."
    fi
done

# 1. Icono
mkdir -p "$ICON_DIR"
if [ -f "$ICON_SRC" ]; then
    cp "$ICON_SRC" "$ICON_DIR/$ICON_NAME.svg"
fi

# 2. Lanzador del menú de aplicaciones
mkdir -p "$APPLICATIONS"
cat > "$APPLICATIONS/cosmic-wallpaper.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Cosmic Wallpaper
Comment=Fondo animado con rotación y búfer para COSMIC Desktop
Exec="$APP"
Icon=$ICON_NAME
Terminal=false
Categories=Utility;Settings;DesktopSettings;
StartupNotify=true
EOF

# 3. Lanzador para detener el fondo
cat > "$APPLICATIONS/cosmic-wallpaper-stop.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Detener Fondo Animado
Comment=Detiene el fondo animado y restaura tu wallpaper
Exec="$APP" --stop
Icon=process-stop
Terminal=false
Categories=Utility;Settings;DesktopSettings;
EOF

# 4. Inicio automático con la sesión de COSMIC / Freedesktop
mkdir -p "$AUTOSTART"
cat > "$AUTOSTART/cosmic-wallpaper.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Cosmic Wallpaper
Comment=Fondo animado para COSMIC Desktop — inicia en la bandeja
Exec="$APP"
Icon=$ICON_NAME
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
X-COSMIC-Autostart=true
EOF

chmod +x "$APPLICATIONS/cosmic-wallpaper.desktop" \
         "$APPLICATIONS/cosmic-wallpaper-stop.desktop" \
         "$AUTOSTART/cosmic-wallpaper.desktop" \
         "$APP"

# 5. Actualizar bases de datos
update-desktop-database "$APPLICATIONS/" 2>/dev/null || true
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo ""
echo "✓ Instalación completada."
echo "  • Menú de aplicaciones: Cosmic Wallpaper + Detener Fondo Animado."
echo "  • Inicio automático activado (restaura tu última rotación confirmada)."
echo "  • Para desinstalar: elimina los .desktop de ~/.local/share/applications"
echo "    y ~/.config/autostart."
