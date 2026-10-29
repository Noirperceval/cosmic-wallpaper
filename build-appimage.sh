#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "==> Compilando binario en Release..."
cargo build --release

echo "==> Preparando AppDir..."
rm -rf AppDir
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/scalable/apps

cp target/release/cosmic-wallpaper AppDir/usr/bin/
cp cosmic-wallpaper.desktop AppDir/
cp cosmic-wallpaper.desktop AppDir/usr/share/applications/

# Icono genérico SVG
cat << 'EOF' > AppDir/cosmic-wallpaper.svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect width="44" height="32" x="2" y="8" rx="4" fill="#31363b"/>
  <polygon points="18,16 32,24 18,32" fill="#3daee9"/>
</svg>
EOF
cp AppDir/cosmic-wallpaper.svg AppDir/usr/share/icons/hicolor/scalable/apps/

# AppRun
cat << 'EOF' > AppDir/AppRun
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/cosmic-wallpaper" "$@"
EOF
chmod +x AppDir/AppRun

echo "==> Generando paquete o AppImage..."
if [ ! -f linuxdeploy-x86_64.AppImage ]; then
    echo "Descarga linuxdeploy si deseas el empaquetado AppImage estándar:"
    echo "curl -LO https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
    echo "chmod +x linuxdeploy-x86_64.AppImage"
fi

echo "¡Listo! Binario disponible en: $DIR/target/release/cosmic-wallpaper"
