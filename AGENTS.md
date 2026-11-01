# AGENTS.md — Reglas para agentes

Estas reglas son obligatorias para cualquier agente (humano o IA) que trabaje en este repositorio.

## Antes de empezar

- **Lee `LEE_HISTORIAL.md` completo** antes de responder o tocar código.
- Si el usuario dice **“lee historial”**, se refiere a `LEE_HISTORIAL.md`.
- Si algo del historial contradice al `README.md`, para las decisiones técnicas manda el historial; si es un dato de uso, corrige el README y anota el cambio.
- Revisa `git status` y `git log -5` para entender el estado real antes de modificar.

## Al terminar cada tarea

- Actualiza `LEE_HISTORIAL.md`:
  - **Estado actual**: fecha, versión, rama, enlaces y hashes si cambiaron.
  - **Pendientes**: marca lo hecho con `[x]` y añade lo nuevo.
  - **Bitácora**: entrada nueva con la fecha y un resumen de 3 a 6 puntos, arriba de la anterior.
- **No borres historia anterior.** Agrega, corrige o marca como obsoleto; nunca elimines entradas.
- Si algo no se pudo verificar, dilo explícitamente y déjalo como pendiente.

## Decisiones y alcance

- Respeta las **Decisiones firmes** de `LEE_HISTORIAL.md`.
- No cambies el motor (`mpvpaper`), el formato de playlist (`.m3u`), los valores por defecto (35 s, `Rellenar`), el diseño monocromo ni la estructura de un solo archivo Python sin pedirlo antes.
- No reintroduzcas Rust ni dependencias nuevas sin justificarlo y sin actualizar el historial.

## Verificación

- Usa el análisis y las pruebas que ya tiene el proyecto:
  - `python3 -m py_compile cosmic_wallpaper_gui.py`
  - arranque en modo `offscreen` (`QT_QPA_PLATFORM=offscreen ... --no-restore`)
  - `./Cosmic-Wallpaper-x86_64.AppImage --version` tras compilar
- No hay suite automatizada todavía (está en pendientes). Si tu cambio lo permite, añade una prueba y documenta cómo ejecutarla.
- No declares algo “funcionando” sin haberlo verificado; si no puedes probarlo, dilo.

## Archivos, secretos y respaldos

- **No muevas** archivos, claves, respaldos ni artefactos fuera de la carpeta del proyecto.
- **No subas a Git** secretos, credenciales, `.env`, claves SSH, tokens ni binarios generados (`.AppImage`, `build/`, `dist/`, `AppDir/`).
- No toques `~/.config/cosmic-wallpaper/` ni `~/.cache/cosmic-wallpaper/` del usuario sin necesidad; no borres su configuración, favoritos ni selección.
- No ejecutes la versión desde el código y el AppImage al mismo tiempo: comparten configuración y socket IPC.
- Mantén versionados `LEE_HISTORIAL.md`, `AGENTS.md` y `opencode.json`.

## Estilo

- Interfaz y textos en **español**; mensajes de commit en **inglés** (como el historial).
- Conserva el diseño monocromo, los radios, los espaciados y la jerarquía actual de la UI.
- Prefiere cambios pequeños y verificables; explica el porqué en la bitácora.
