# 🌌 Cosmic Wallpaper

> Fondo animado interactivo, elegante y ultra-fluido diseñado para el entorno de escritorio **COSMIC Desktop**.

**Creado por:** [Noir Perceval (Daniel Chable)](https://github.com/Noirperceval)  
**Repositorio GitHub:** [https://github.com/Noirperceval/cosmic-wallpaper](https://github.com/Noirperceval/cosmic-wallpaper)

---

## 📸 Vista Previa

![Cosmic Wallpaper en acción](docs/preview.png)

---

## 📦 Métodos de Instalación

Tienes dos opciones para disfrutar de Cosmic Wallpaper:

### Opción 1: AppImage Portátil (Recomendada - Sin instalación)
La forma más directa y rápida. Funciona en cualquier distribución Linux con COSMIC (Arch, Fedora, Ubuntu, Debian, Pop!_OS):
1. Descarga el archivo `Cosmic-Wallpaper-x86_64.AppImage` desde nuestro [Releases en GitHub](https://github.com/Noirperceval/cosmic-wallpaper/releases).
2. Dale permisos de ejecución:
   ```bash
   chmod +x Cosmic-Wallpaper-x86_64.AppImage
   ```
3. Haz doble clic en el archivo y ¡listo!

---

### Opción 2: Paquete Flatpak (Flathub)
Si utilizas el ecosistema Flatpak, el proyecto incluye el manifiesto oficial con ID:
`io.github.Noirperceval.CosmicWallpaper`

> ⚠️ **Nota importante sobre Flatpak y Wayland:**  
> Flatpak funciona dentro de un contenedor aislado (sandbox). Para que la aplicación pueda proyectar el video sobre el fondo de pantalla en COSMIC Desktop sin restricciones, se requiere tener instalado **`mpvpaper`** en tu sistema base:
> - **Arch / CachyOS / Manjaro:** `sudo pacman -S mpvpaper`
> - **Fedora / Nobara:** `sudo dnf install mpvpaper`
> - **Ubuntu / Debian / Pop!_OS:** `sudo apt install mpvpaper`
>
> *(Si prefieres no instalar nada en tu sistema base, utiliza el AppImage de la Opción 1).*

---

## ✨ Características Principales

- 🎬 **Galería Visual Interactiva**: Vista previa con miniaturas generadas al vuelo para tus videos.
- ⚡ **Vista Previa en Tiempo Real**: Haz un solo clic sobre cualquier tarjeta de video para verlo en vivo en tu fondo de pantalla al instante.
- 💾 **Confirmar Selección**: Botón para fijar tu video favorito o rotación múltiple de forma permanente.
- 🔁 **Rotación Fluida (Zero-Flicker)**: Precarga los videos en buffer de memoria evitando cualquier parpadeo de pantalla negra o fondo estático entre cambios.
- 🎨 **100% Adaptable al Tema de COSMIC**: Hereda automáticamente la paleta de colores nativa (modo oscuro o claro) de tu sistema.
- 📌 **Bandeja del Sistema (System Tray)**: Minimízalo en la barra para cambiar fondos, pausar o detener con un clic.
- 🛠 **Asistente Inteligente Multi-Distro**: Detecta automáticamente tu sistema operativo e instala los requisitos por ti en un solo clic.

---

## 💻 Construir el AppImage desde el código

Si deseas generar el ejecutable AppImage por tu cuenta:
```bash
git clone https://github.com/Noirperceval/cosmic-wallpaper.git
cd cosmic-wallpaper
./build-appimage.sh
```

---

## 📄 Licencia y Créditos

Desarrollado con dedicación para la comunidad COSMIC Desktop por **Noir Perceval (Daniel Chable)**.
