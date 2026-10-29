#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "==> 1. Compilando binario autónomo..."
pyinstaller --onefile --windowed --name cosmic-wallpaper cosmic_wallpaper_gui.py

echo "==> 2. Preparando AppDir..."
rm -rf AppDir
mkdir -p AppDir/usr/bin AppDir/usr/share/applications AppDir/usr/share/icons/hicolor/scalable/apps

cp dist/cosmic-wallpaper AppDir/usr/bin/
cp cosmic-wallpaper.desktop AppDir/
cp cosmic-wallpaper.desktop AppDir/usr/share/applications/
sed -i 's|^Exec=.*|Exec=cosmic-wallpaper|' AppDir/cosmic-wallpaper.desktop
sed -i 's|^Exec=.*|Exec=cosmic-wallpaper|' AppDir/usr/share/applications/cosmic-wallpaper.desktop
sed -i 's|^Icon=.*|Icon=cosmic-wallpaper|' AppDir/cosmic-wallpaper.desktop
sed -i 's|^Icon=.*|Icon=cosmic-wallpaper|' AppDir/usr/share/applications/cosmic-wallpaper.desktop

# Crear Icono SVG oficial
cat << 'EOF' > AppDir/cosmic-wallpaper.svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <defs>
    <linearGradient id="cosmicGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4a154b"/>
      <stop offset="50%" stop-color="#191938"/>
      <stop offset="100%" stop-color="#0e3854"/>
    </linearGradient>
    <linearGradient id="neonPlay" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00f2fe"/>
      <stop offset="100%" stop-color="#4facfe"/>
    </linearGradient>
  </defs>
  <rect width="116" height="116" x="6" y="6" rx="26" fill="url(#cosmicGrad)" stroke="#4facfe" stroke-width="2"/>
  <circle cx="95" cy="30" r="2.5" fill="#ffffff" opacity="0.8"/>
  <circle cx="35" cy="92" r="2" fill="#ffffff" opacity="0.6"/>
  <circle cx="102" cy="75" r="1.5" fill="#ffffff" opacity="0.7"/>
  <circle cx="28" cy="38" r="1.8" fill="#ffffff" opacity="0.6"/>
  <polygon points="50,42 90,64 50,86" fill="url(#neonPlay)"/>
</svg>
EOF

cp AppDir/cosmic-wallpaper.svg AppDir/usr/share/icons/hicolor/scalable/apps/
cp AppDir/cosmic-wallpaper.svg AppDir/.DirIcon

# AppRun
cat << 'EOF' > AppDir/AppRun
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
exec "${HERE}/usr/bin/cosmic-wallpaper" "$@"
EOF
chmod +x AppDir/AppRun

echo "==> 3. Empaquetando AppImage..."
if [ ! -f appimagetool-x86_64.AppImage ]; then
    curl -LO https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool-x86_64.AppImage
fi

ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir Cosmic-Wallpaper-x86_64.AppImage

echo "¡Completado! Archivo generado: $DIR/Cosmic-Wallpaper-x86_64.AppImage"
