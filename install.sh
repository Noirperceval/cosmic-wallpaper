#!/usr/bin/env bash
# install.sh — Instalador de Cosmic Wallpaper
# Creado por: Noir Perceval (Daniel Chable)
# GitHub: https://github.com/Noirperceval/cosmic-wallpaper
#
# Instala el acceso directo en el menú de aplicaciones
# y configura el inicio automático con la sesión de COSMIC Desktop.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Instalando Cosmic Wallpaper..."

# 1. Acceso directo en el menú de aplicaciones
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/cosmic-wallpaper.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Cosmic Wallpaper
Comment=Fondo animado interactivo para COSMIC Desktop
Exec=$SCRIPT_DIR/cosmic_wallpaper_gui.py
Icon=$SCRIPT_DIR/io.github.Noirperceval.CosmicWallpaper.svg
Terminal=false
Categories=Utility;Settings;DesktopSettings;
StartupNotify=true
EOF

# 2. Inicio automático con la sesión de COSMIC / Freedesktop
mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/cosmic-wallpaper.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Cosmic Wallpaper
Comment=Fondo animado para COSMIC Desktop — inicia con el sistema en bandeja
Exec=$SCRIPT_DIR/cosmic_wallpaper_gui.py
Icon=$SCRIPT_DIR/io.github.Noirperceval.CosmicWallpaper.svg
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
X-COSMIC-Autostart=true
EOF

chmod +x "$HOME/.local/share/applications/cosmic-wallpaper.desktop"
chmod +x "$HOME/.config/autostart/cosmic-wallpaper.desktop"
chmod +x "$SCRIPT_DIR/cosmic_wallpaper_gui.py"

# 3. Actualizar base de datos de aplicaciones
update-desktop-database "$HOME/.local/share/applications/" 2>/dev/null || true

echo ""
echo "✓ Instalación completada."
echo "  • Acceso directo en el menú de aplicaciones: listo."
echo "  • Inicio automático con el sistema: activado."
echo "  • La próxima vez que inicies sesión en COSMIC, el fondo"
echo "    arrancará automáticamente desde la bandeja del sistema."
