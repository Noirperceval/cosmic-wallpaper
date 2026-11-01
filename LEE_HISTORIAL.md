# LEE_HISTORIAL — Memoria del proyecto Cosmic Wallpaper

Este archivo es la memoria viva del proyecto: qué hace, qué está hecho, qué falta y por qué se decidió cada cosa.

## Cómo usar este archivo

- **Al empezar** cualquier sesión de trabajo: léelo completo antes de tocar código.
- **Al terminar**: actualiza "Estado actual", marca los pendientes y añade una entrada nueva en "Bitácora".
- **Nunca borres historia**: agrega, corrige o marca como obsoleto; no elimines entradas anteriores. La bitácora va con la más reciente arriba.

## Qué es este proyecto

Cosmic Wallpaper es una aplicación de escritorio para Linux que pone **videos locales como fondo animado** en COSMIC Desktop, con rotación automática, búfer sin cortes y una interfaz monocroma en español. Está pensada para usuarios de COSMIC que quieren personalizar su escritorio sin tocar la terminal ni editar archivos de configuración.

**Público:** usuarios de COSMIC Desktop (Arch/CachyOS, Fedora, Ubuntu/Debian, Pop!_OS, openSUSE) con videos propios; también quien quiera empaquetarlo o modificarlo.

**Límites:** no reproduce video por sí misma (delega en `mpvpaper`), no incluye `mpvpaper`/`ffmpeg`/`cosmic-bg` (los pide al sistema), está probada solo en COSMIC/Wayland, el manifiesto Flatpak es solo de referencia y no hay suite de pruebas automatizada todavía.

## Estado actual

- **Fecha:** 2026-11-01
- **Versión de la app:** 2.0.2 (`VERSION` en `cosmic_wallpaper_gui.py`)
- **Rama:** `main` (sincronizada con `origin/main`)
- **Último commit de la app:** `f9bb7dd` — *Release 2.0.2: configurable video scaling*
- **Commit de esta memoria:** el que añade `LEE_HISTORIAL.md`, `AGENTS.md` y `opencode.json` (ver `git log -1`).
- **Entorno probado:** CachyOS, COSMIC/Wayland, pantalla 1920×1080, Python 3.14.8, PySide6 6.12.0, mpvpaper 1.9, mpv 0.41.0, ffmpeg 9.0.2.
- **Pruebas:** no hay suite automatizada versionada (pendiente). Verificación usada: `python3 -m py_compile`, render offscreen del GUI, build del AppImage, `Cosmic-Wallpaper-x86_64.AppImage --version` y pruebas funcionales manuales ejecutadas fuera del repo (no versionadas). La descarga de la release se verificó con HTTP 200 y 121.240.056 bytes.
- **Enlaces:**
  - Repositorio: https://github.com/Noirperceval/cosmic-wallpaper
  - Release 2.0.2: https://github.com/Noirperceval/cosmic-wallpaper/releases/tag/v2.0.2
  - Descarga directa (última): https://github.com/Noirperceval/cosmic-wallpaper/releases/latest/download/Cosmic-Wallpaper-x86_64.AppImage

## Mapa del proyecto

| Ruta | Qué es |
|---|---|
| `cosmic_wallpaper_gui.py` | **La aplicación completa** (~2.800 líneas): UI Qt, motor de video, búfer, rotación, bandeja y asistente de dependencias. |
| `README.md` | Documentación para usuarios: instalación, uso, rotación, ajuste de video y compilación. |
| `install.sh` | Instala lanzador en el menú, lanzador "Detener Fondo" y autostart; comprueba Python/PySide6/mpvpaper. |
| `build-appimage.sh` | Compila con PyInstaller y empaqueta con `appimagetool` (descarga la herramienta si falta). |
| `cosmic-wallpaper.desktop` | Plantilla del lanzador principal (usada por AppImage). |
| `cosmic-wallpaper-stop.desktop` | Plantilla del lanzador para `--stop`. |
| `cosmic-wallpaper-autostart.desktop` | Plantilla de inicio automático. |
| `io.github.Noirperceval.CosmicWallpaper.desktop` | Lanzador Flatpak. |
| `io.github.Noirperceval.CosmicWallpaper.metainfo.xml` | Metadatos para Flathub (versión y notas). |
| `io.github.Noirperceval.CosmicWallpaper.svg` | Icono de la aplicación. |
| `io.github.Noirperceval.CosmicWallpaper.yml` | Manifiesto Flatpak (referencia; no funcional todavía). |
| `docs/preview.png`, `docs/preview-light.png` | Capturas reales de la interfaz (oscuro y claro). |
| `LEE_HISTORIAL.md` | Este archivo. |
| `AGENTS.md` | Reglas obligatorias para agentes que trabajen en el proyecto. |
| `opencode.json` | Configuración de OpenCode: instrucciones y comando `/historial`. |
| `.gitignore` | Excluye cachés, artefactos, binarios, secretos y respaldos. |
| `build/`, `dist/`, `AppDir/`, `*.AppImage`, `appimagetool-*.AppImage`, `*.spec`, `__pycache__/` | Generados localmente; **no se versionan**. |
| `docs/mockup-assets/`, `docs/redesign-mockup.html` | Artefactos locales de diseño; **no se versionan**. |

**Rutas de ejecución (fuera del repo):**

- Configuración: `~/.config/cosmic-wallpaper/config.json`
- Caché: `~/.cache/cosmic-wallpaper/` (`thumbnails/`, `backing/`, `playlist.m3u`, `engine.pid`, `mpv.sock`, `cosmic-bg-original.conf`)

## Qué está hecho

- **Interfaz 2.0** monocroma (tema claro y oscuro), con sidebar de biblioteca (Todos / Favoritos / Recientes), buscador, vista de cuadrícula o lista y tarjetas con badges `EN VIVO` y `PRECARGADO`.
- **Lista de rotación** en el sidebar, ordenable arrastrando, con turnos numerados y miniatura.
- **Selección múltiple** con casillas, vista previa individual al hacer clic, confirmación persistente y restauración del último fondo al iniciar.
- **Motor de fondo** sobre `mpvpaper`: playlist `.m3u`, caché en RAM, `prefetch-playlist`, `keep-open`, pausa/reanudación real, watchdog y apagado limpio (solo su propio grupo de procesos).
- **Búfer nivel 2:** caché de mpv + frame de respaldo extraído con `ffmpeg` y pintado con `cosmic-bg` antes de lanzar el video; se restaura el wallpaper original al detener.
- **Rotación temporizada** cada 35 s por defecto (presets 10/15/20/30/35/60 y personalizado 5–3600 s), con cuenta atrás en el pie; modo alternativo "al terminar cada video"; acción "Siguiente video" en la bandeja.
- **Ajuste de video** (`Rellenar` / `Ajustar` / `Estirar`) aplicado en vivo por IPC; `Rellenar` es el predeterminado.
- **Bandeja del sistema** con abrir, pausar/reanudar, detener, siguiente, acerca de y salir.
- **Asistente de requisitos** multi-distro con detección de gestor de paquetes y comando de instalación.
- **Empaquetado y distribución:** `install.sh`, `build-appimage.sh`, AppImage de ~116 MB y releases publicadas `v2.0.0`, `v2.0.1`, `v2.0.2` con descarga directa desde el README.

## Decisiones firmes

1. **Python + PySide6**, no Rust. El prototipo Rust (`src/main.rs`, `Cargo.toml`, `Cargo.lock`) se eliminó en `9613f07`; COSMIC esté en Rust no obliga a que las apps lo estén.
2. **El motor es `mpvpaper`.** La app no dibuja video por su cuenta.
3. **La playlist debe ser `.m3u`.** Un `.txt` hace que mpv falle (`Failed to recognize file format`); fue la causa de que la rotación no funcionara.
4. **Rotación y ajuste se hacen por IPC** (`playlist-next`, `panscan`, `keepaspect`), sin reiniciar `mpvpaper` ni perder el búfer.
5. **Búfer nivel 2:** caché de mpv + frame de respaldo con `cosmic-bg` aplicado *antes* de lanzar el video. Al detener o salir se restaura el wallpaper original.
6. **Nunca matar `mpvpaper` ajenos.** Solo se termina el grupo de procesos propio; no se usa `killall`.
7. **Diseño monocromo** en blanco y negro (oscuro/claro), sin colores de acento. UI y textos en español; commits en inglés.
8. **Valores por defecto:** rotación cada 35 s, ajuste "Rellenar", restaurar fondo al iniciar activado.
9. **Un solo archivo de aplicación** (`cosmic_wallpaper_gui.py`) para no romper PyInstaller ni el flujo actual de empaquetado.
10. **Nada de secretos ni binarios en Git.** El AppImage y los artefactos van en Releases, no en el repositorio.
11. **No ejecutar la versión desde el código y el AppImage a la vez:** comparten configuración y socket IPC.
12. **La memoria no se borra.** `LEE_HISTORIAL.md`, `AGENTS.md` y `opencode.json` se mantienen versionados y actualizados.

## Pendientes

- [ ] Añadir una suite de pruebas automatizada en el repo (pytest + Qt en modo `offscreen`).
- [ ] Declarar dependencias de Python (`pyproject.toml` o `requirements.txt`, PySide6 ≥ 6.x).
- [ ] Añadir un archivo `LICENSE` (el metainfo declara MIT, pero no existe el archivo).
- [ ] Hacer funcional el Flatpak (incluir PySide6 y acceso al `mpvpaper` del host) o retirar el manifiesto.
- [ ] Probar el AppImage en una instalación limpia de COSMIC en otra distribución.
- [ ] Configurar CI (GitHub Actions) con `py_compile` y las pruebas.
- [ ] Verificar el frame de respaldo con versiones de `cosmic-bg` que no recarguen la configuración al instante.
- [ ] Probar sesiones largas para confirmar que el índice de rotación por IPC no se desincroniza.
- [ ] Traer las etiquetas de las releases al repo local (`git fetch --tags`).
- [ ] Revisar README y notas de release cuando cambie la versión.

## Comandos útiles

```bash
# Dependencias del sistema (Arch / CachyOS)
sudo pacman -S mpvpaper ffmpeg python-pyside6

# Si la distribución no empaqueta PySide6
pip install --user PySide6

# Ejecutar
./cosmic_wallpaper_gui.py
./cosmic_wallpaper_gui.py --no-restore   # sin restaurar el último fondo
./cosmic_wallpaper_gui.py --stop         # detener y restaurar el wallpaper
./cosmic_wallpaper_gui.py --version

# Verificación básica
python3 -m py_compile cosmic_wallpaper_gui.py
QT_QPA_PLATFORM=offscreen timeout 5 ./cosmic_wallpaper_gui.py --no-restore
# (el código de salida 124 es lo esperado: la app sigue viva)

# Instalar lanzadores en el menú y autostart
./install.sh

# Compilar y verificar el AppImage
./build-appimage.sh
./Cosmic-Wallpaper-x86_64.AppImage --version

# Validar la configuración de OpenCode
python3 -m json.tool opencode.json > /dev/null

# Publicar cambios
git add -A
git commit -m "Descripción en inglés"
git push origin main
# Release: GitHub → Releases → adjuntar Cosmic-Wallpaper-x86_64.AppImage
```

## Bitácora

### 2026-11-01 — Memoria del proyecto

- Se creó `LEE_HISTORIAL.md` con el estado real del proyecto, mapa, decisiones, pendientes y comandos.
- Se creó `AGENTS.md` con las reglas de lectura, actualización y verificación.
- Se creó `opencode.json` con la instrucción `LEE_HISTORIAL.md` y el comando `/historial`.
- Se amplió `.gitignore` con secretos, claves y respaldos; se mantienen versionados los tres archivos de memoria.
- Se documentó que no hay pruebas automatizadas todavía y que el Flatpak no es funcional.

### 2026-10-30 — v2.0.2: ajuste de video

- Nuevo ajuste `Rellenar` / `Ajustar` / `Estirar`, aplicado en vivo por IPC y persistido.
- `Rellenar` queda por defecto: llena la pantalla recortando bordes (caso 3440×1440 en 1920×1080).
- Se detectó y corrigió el caso de videos 21:9 con márgenes de 240 px.
- Release `v2.0.2` publicada con el AppImage recompilado.

### 2026-10-30 — v2.0.1: botón de descarga

- Botón "Descargar AppImage" y enlace a Releases al principio del README.
- Insignia de versión dinámica (`releases/latest`).
- Release `v2.0.1` publicada; sin cambios funcionales.

### 2026-10-30 — v2.0.0: rediseño, búfer y rotación

- Rediseño monocromo con sidebar, grid/lista, buscador y favoritos.
- Búfer nivel 2: caché de mpv + frame de respaldo con `cosmic-bg`.
- Rotación cada 35 s por IPC y modo "al terminar cada video".
- Corrección clave: playlist `.m3u` en vez de `.txt`; la rotación múltiple no funcionaba.
- Pausa/reanudación real; "Detener" ya no borra la selección; restauración al iniciar.
- Se eliminó el prototipo Rust y se actualizaron `install.sh`, el build y los metadatos.
- Release `v2.0.0` publicada.

### 2026-10-29 — Primera versión distribuible

- AppImage inicial, manifiesto Flatpak, `install.sh` con autostart y captura en `docs/`.
- Versión 1.1: selección múltiple, vista previa en vivo y bandeja del sistema.
