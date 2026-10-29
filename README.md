# 🌌 Cosmic Wallpaper

> Fondo animado interactivo, elegante y ultra-fluido diseñado para el entorno de escritorio **COSMIC Desktop**.

**Creado por:** [Noir Perceval (Daniel Chable)](https://github.com/Noirperceval)  
**Repositorio GitHub:** [https://github.com/Noirperceval](https://github.com/Noirperceval)

---

## ✨ Características Principales

- 🎬 **Galería Visual Interactiva**: Vista previa con miniaturas generadas al vuelo para tus videos.
- 🔁 **Selección Única o Múltiple**: Elige un solo video para reproducirlo en bucle infinito o varios para alternarlos.
- ⚡ **Transición Suave en Memoria (Zero-Flicker)**: Precarga los videos en buffer evitando cualquier parpadeo de pantalla negra o fondo estático entre cambios.
- 🎨 **100% Adaptable al Tema de COSMIC**: Hereda automáticamente la paleta de colores nativa (modo oscuro o claro) de tu sistema.
- 📌 **Bandeja del Sistema (System Tray)**: Minimízalo en la barra para cambiar fondos, pausar o detener con un clic.
- 🛠 **Asistente Inteligente Multi-Distro**: Detecta automáticamente tu sistema operativo (Arch, Fedora, Ubuntu, Debian, Pop!_OS, CachyOS, openSUSE) e instala los requisitos por ti en un solo clic.

---

## 🚀 Requisitos del Sistema

El programa utiliza dos herramientas estándar de Linux:
- `mpvpaper` (motor Wayland para reproducir videos en la superficie del fondo de pantalla)
- `ffmpeg` (para crear las miniaturas visuales)

### Instalación automática de requisitos:
La propia aplicación los detecta y te ofrece instalarlos al abrirla.

### Instalación manual por distribución:

- **Arch Linux / CachyOS / Manjaro**:
  ```bash
  sudo pacman -S --needed mpvpaper ffmpeg
  ```

- **Fedora / Nobara**:
  ```bash
  sudo dnf install mpvpaper ffmpeg-free
  ```

- **Ubuntu / Debian / Pop!_OS**:
  ```bash
  sudo apt update && sudo apt install mpvpaper ffmpeg
  ```

---

## 💻 Uso

1. Ejecuta la aplicación desde el menú de aplicaciones o por terminal:
   ```bash
   python3 cosmic_wallpaper_gui.py
   ```
2. Haz clic en **📁 Cambiar carpeta** para elegir donde tienes tus videos (por defecto busca en `~/Vídeos`).
3. Marca los videos que desees y pulsa **✔ Aplicar Fondo**.

### Atajo para probar el asistente de instalación:
```bash
python3 cosmic_wallpaper_gui.py --test-deps
```

---

## 📄 Licencia y Créditos

Desarrollado con dedicación para la comunidad COSMIC Desktop por **Noir Perceval (Daniel Chable)**.
