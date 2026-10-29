#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cosmic Wallpaper GUI & System Tray
Creado por: Noir Perceval (Daniel Chable)
GitHub: https://github.com/Noirperceval

Fondo animado interactivo y elegante para COSMIC Desktop.
- Respeta los colores y tema nativo del sistema.
- Asistente inteligente de dependencias para Arch, Fedora, Ubuntu, Debian, Pop!_OS, CachyOS, etc.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets

APP_NAME = "Cosmic Wallpaper"
AUTHOR_NAME = "Noir Perceval (Daniel Chable)"
GITHUB_URL = "https://github.com/Noirperceval"
VERSION = "1.0.0"

CACHE_DIR = Path.home() / ".cache" / "cosmic-wallpaper" / "thumbnails"
CONFIG_FILE = Path.home() / ".config" / "cosmic-wallpaper" / "config.json"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)


def detect_distro():
    """Detecta la distribución de Linux y el comando adecuado para instalar paquetes."""
    info = {"name": "Linux", "id": "", "id_like": "", "install_cmd": "", "missing_pkgs": []}
    
    os_release = Path("/etc/os-release")
    if os_release.exists():
        with open(os_release, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("NAME="):
                    info["name"] = line.split("=", 1)[1].strip().strip('"')
                elif line.startswith("ID="):
                    info["id"] = line.split("=", 1)[1].strip().strip('"').lower()
                elif line.startswith("ID_LIKE="):
                    info["id_like"] = line.split("=", 1)[1].strip().strip('"').lower()

    distro_family = info["id"] + " " + info["id_like"]

    # Determinar gestor de paquetes
    if any(k in distro_family for k in ["arch", "cachyos", "manjaro", "endeavouros"]):
        info["pkg_manager"] = "pacman"
        info["install_cmd"] = "sudo pacman -S --needed --noconfirm"
        info["mpvpaper_pkg"] = "mpvpaper"
        info["ffmpeg_pkg"] = "ffmpeg"
    elif any(k in distro_family for k in ["fedora", "rhel", "nobara"]):
        info["pkg_manager"] = "dnf"
        info["install_cmd"] = "sudo dnf install -y"
        info["mpvpaper_pkg"] = "mpvpaper"
        info["ffmpeg_pkg"] = "ffmpeg-free"
    elif any(k in distro_family for k in ["ubuntu", "debian", "pop", "mint"]):
        info["pkg_manager"] = "apt"
        info["install_cmd"] = "sudo apt update && sudo apt install -y"
        info["mpvpaper_pkg"] = "mpvpaper"
        info["ffmpeg_pkg"] = "ffmpeg"
    elif "opensuse" in distro_family:
        info["pkg_manager"] = "zypper"
        info["install_cmd"] = "sudo zypper install -y"
        info["mpvpaper_pkg"] = "mpvpaper"
        info["ffmpeg_pkg"] = "ffmpeg"
    else:
        info["pkg_manager"] = "desconocido"
        info["install_cmd"] = ""
        info["mpvpaper_pkg"] = "mpvpaper"
        info["ffmpeg_pkg"] = "ffmpeg"

    return info


def check_and_prompt_dependencies(parent_widget=None, force_test=False):
    """
    Verifica si faltan dependencias y le ofrece al usuario instalarlas.
    Si force_test=True, simula que faltan paquetes para comprobar la ventana y el asistente.
    """
    distro = detect_distro()
    missing_bins = []
    needed_pkgs = []

    if force_test or not shutil.which("mpvpaper"):
        missing_bins.append("mpvpaper (motor de reproducción de fondo)")
        needed_pkgs.append(distro["mpvpaper_pkg"])

    if force_test or not shutil.which("ffmpeg"):
        missing_bins.append("ffmpeg (generador de miniaturas)")
        needed_pkgs.append(distro["ffmpeg_pkg"])

    if not missing_bins:
        return True  # Todo perfecto

    msg = (
        f"<h3>¡Hola! Detectamos que estás usando {distro['name']}</h3>"
        "<p>Para que los fondos animados funcionen con fluidez y miniaturas, "
        "se requieren los siguientes paquetes del sistema:</p>"
        + "".join([f"• <b>{m}</b><br>" for m in missing_bins]) +
        f"<br><p>¿Deseas que preparemos la instalación automática usando <code>{distro['pkg_manager']}</code>?</p>"
    )

    box = QtWidgets.QMessageBox(parent_widget)
    box.setWindowTitle("Asistente de Requisitos - Cosmic Wallpaper")
    box.setIcon(QtWidgets.QMessageBox.Information)
    box.setText(msg)
    btn_install = box.addButton("Instalar requisitos", QtWidgets.QMessageBox.AcceptRole)
    btn_cancel = box.addButton("Continuar sin instalar", QtWidgets.QMessageBox.RejectRole)
    box.exec()

    if box.clickedButton() == btn_install:
        if distro["install_cmd"]:
            pkgs_str = " ".join(needed_pkgs)
            full_command = f"{distro['install_cmd']} {pkgs_str}"
            
            terms = ["cosmic-term", "alacritty", "konsole", "gnome-terminal", "foot", "xterm"]
            launched = False
            for term in terms:
                if shutil.which(term):
                    try:
                        if term in ["cosmic-term", "alacritty", "foot"]:
                            subprocess.Popen([term, "-e", "bash", "-c", f"{full_command}; echo; read -p 'Presiona Enter para cerrar...'"])
                        elif term == "gnome-terminal":
                            subprocess.Popen([term, "--", "bash", "-c", f"{full_command}; echo; read -p 'Presiona Enter para cerrar...'"])
                        elif term == "konsole":
                            subprocess.Popen([term, "-e", "bash", "-c", f"{full_command}; echo; read -p 'Presiona Enter para cerrar...'"])
                        launched = True
                        break
                    except Exception:
                        pass

            if not launched:
                QtWidgets.QMessageBox.information(
                    parent_widget,
                    "Comando para tu terminal",
                    f"Abre tu terminal y ejecuta este comando:\n\n{full_command}"
                )
        else:
            QtWidgets.QMessageBox.warning(
                parent_widget,
                "Instalación manual",
                f"Por favor instala manualmente los paquetes: {', '.join(needed_pkgs)} usando tu gestor de paquetes."
            )

    return True


def get_thumbnail(video_path: Path) -> Path:
    """Genera miniatura usando ffmpeg de forma ultrarrápida."""
    thumb_name = f"{video_path.stem}_{int(os.path.getmtime(video_path))}.jpg"
    thumb_path = CACHE_DIR / thumb_name
    if not thumb_path.exists() and shutil.which("ffmpeg"):
        cmd = [
            "ffmpeg",
            "-ss", "00:00:01",
            "-i", str(video_path),
            "-vframes", "1",
            "-vf", "scale=320:180:force_original_aspect_ratio=increase,crop=320:180",
            "-y",
            str(thumb_path),
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
        except Exception:
            pass
    return thumb_path


def kill_all_instances():
    """Detiene cualquier mpvpaper activo."""
    subprocess.run(["killall", "-9", "mpvpaper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class VideoCard(QtWidgets.QFrame):
    """Tarjeta visual con miniatura que se adapta al tema del sistema."""
    clicked = QtCore.Signal(Path)
    toggled = QtCore.Signal(Path, bool)

    def __init__(self, video_path: Path, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.setFixedSize(220, 165)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setCursor(QtCore.Qt.PointingHandCursor)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Imagen miniatura
        self.img_label = QtWidgets.QLabel()
        self.img_label.setFixedSize(204, 115)
        self.img_label.setScaledContents(True)
        self.img_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.img_label)

        # Controles inferiores (Checkbox + Nombre)
        bot_layout = QtWidgets.QHBoxLayout()
        bot_layout.setContentsMargins(0, 0, 0, 0)
        bot_layout.setSpacing(6)

        self.check = QtWidgets.QCheckBox()
        self.check.stateChanged.connect(self._on_check_changed)
        bot_layout.addWidget(self.check)

        self.title_label = QtWidgets.QLabel(video_path.stem)
        self.title_label.setWordWrap(False)
        self.title_label.setToolTip(video_path.name)
        bot_layout.addWidget(self.title_label, 1)

        layout.addLayout(bot_layout)
        self.load_thumbnail()

    def load_thumbnail(self):
        thumb = get_thumbnail(self.video_path)
        if thumb.exists():
            pix = QtGui.QPixmap(str(thumb))
            self.img_label.setPixmap(pix)
        else:
            self.img_label.setText("🎬 Video")

    def _on_check_changed(self, state):
        is_checked = (state == QtCore.Qt.Checked.value or state == 2)
        self.toggled.emit(self.video_path, is_checked)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.check.setChecked(not self.check.isChecked())
            self.clicked.emit(self.video_path)
        super().mousePressEvent(event)


class CosmicWallpaperApp(QtWidgets.QMainWindow):
    def __init__(self, test_deps=False):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{VERSION} — por {AUTHOR_NAME}")
        self.resize(960, 640)
        self.setMinimumSize(720, 480)

        # Configuración persistente
        self.config = self.load_config()
        self.current_folder = Path(self.config.get("folder", str(Path.home() / "Vídeos")))
        if not self.current_folder.exists():
            self.current_folder = Path.home() / "Vídeos"
            self.current_folder.mkdir(parents=True, exist_ok=True)

        self.selected_videos = set()
        self.cards = []

        self.init_ui()
        self.init_tray()
        
        # Verificar dependencias (normal o modo prueba)
        check_and_prompt_dependencies(self, force_test=test_deps)
        
        self.scan_folder()

    def load_config(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_config(self):
        self.config["folder"] = str(self.current_folder)
        self.config["selected"] = [str(p) for p in self.selected_videos]
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def init_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # Barra superior con título y botones de carpeta
        top_bar = QtWidgets.QHBoxLayout()
        title_box = QtWidgets.QVBoxLayout()

        self.title = QtWidgets.QLabel("Videos Locales")
        font = self.title.font()
        font.setPointSize(font.pointSize() + 4)
        font.setBold(True)
        self.title.setFont(font)
        title_box.addWidget(self.title)

        self.folder_subtitle = QtWidgets.QLabel(f"Carpeta: {self.current_folder}")
        title_box.addWidget(self.folder_subtitle)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        # Botón Probar Dependencias
        self.btn_test_deps = QtWidgets.QPushButton("🔍 Probar Asistente")
        self.btn_test_deps.setToolTip("Verifica y muestra el asistente de dependencias para nuevos usuarios")
        self.btn_test_deps.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_test_deps.clicked.connect(lambda: check_and_prompt_dependencies(self, force_test=True))
        top_bar.addWidget(self.btn_test_deps)

        # Botón Seleccionar Carpeta
        self.btn_folder = QtWidgets.QPushButton("📁 Cambiar carpeta")
        self.btn_folder.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_folder.clicked.connect(self.select_folder)
        top_bar.addWidget(self.btn_folder)

        # Botón Refrescar
        self.btn_refresh = QtWidgets.QPushButton("🔄 Recargar")
        self.btn_refresh.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.scan_folder)
        top_bar.addWidget(self.btn_refresh)

        main_layout.addLayout(top_bar)

        # Separador visual nativo
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(sep)

        # Área de Scroll con Cuadrícula
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll_content = QtWidgets.QWidget()
        self.grid = QtWidgets.QGridLayout(self.scroll_content)
        self.grid.setContentsMargins(8, 8, 8, 8)
        self.grid.setSpacing(14)
        self.grid.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll, 1)

        # Créditos y autor
        credits_bar = QtWidgets.QHBoxLayout()
        credits_lbl = QtWidgets.QLabel(
            f"Creado por <b>{AUTHOR_NAME}</b> — "
            f"<a href='{GITHUB_URL}' style='color: inherit;'>{GITHUB_URL}</a>"
        )
        credits_lbl.setOpenExternalLinks(True)
        credits_lbl.setStyleSheet("opacity: 0.8; font-size: 11px;")
        credits_bar.addWidget(credits_lbl)
        credits_bar.addStretch()
        main_layout.addLayout(credits_bar)

        # Barra Inferior de Acción
        bottom_bar = QtWidgets.QHBoxLayout()
        self.status_lbl = QtWidgets.QLabel("Selecciona los videos que desees poner de fondo")
        bottom_bar.addWidget(self.status_lbl)

        bottom_bar.addStretch()

        self.btn_stop = QtWidgets.QPushButton("⏹ Detener Fondo")
        self.btn_stop.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_stop.clicked.connect(self.stop_wallpaper)
        bottom_bar.addWidget(self.btn_stop)

        self.btn_apply = QtWidgets.QPushButton("✔ Aplicar Fondo")
        self.btn_apply.setDefault(True)
        self.btn_apply.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_apply.clicked.connect(self.apply_wallpaper)
        bottom_bar.addWidget(self.btn_apply)

        main_layout.addLayout(bottom_bar)

    def init_tray(self):
        """Bandeja del sistema (System Tray) para acceso rápido."""
        self.tray = QtWidgets.QSystemTrayIcon(self)
        icon = self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        self.tray.setIcon(icon)
        self.tray.setToolTip(f"{APP_NAME}\nPor {AUTHOR_NAME}")

        tray_menu = QtWidgets.QMenu(self)

        act_show = tray_menu.addAction("🖥 Abrir Selector de Videos")
        act_show.triggered.connect(self.show_normal_window)

        act_pause = tray_menu.addAction("⏯ Pausar / Reanudar")
        act_pause.triggered.connect(self.toggle_pause)

        tray_menu.addSeparator()

        act_stop = tray_menu.addAction("⏹ Detener Fondo")
        act_stop.triggered.connect(self.stop_wallpaper)

        tray_menu.addSeparator()

        act_about = tray_menu.addAction(f"ℹ Acerca de {APP_NAME}")
        act_about.triggered.connect(self.show_about)

        tray_menu.addSeparator()

        act_exit = tray_menu.addAction("✖ Salir por Completo")
        act_exit.triggered.connect(self.quit_app)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def show_about(self):
        QtWidgets.QMessageBox.about(
            self,
            f"Acerca de {APP_NAME}",
            f"<h2>{APP_NAME} v{VERSION}</h2>"
            f"<p>Fondo animado interactivo y de alto rendimiento para el escritorio COSMIC.</p>"
            f"<p><b>Autor:</b> {AUTHOR_NAME}</p>"
            f"<p><b>GitHub:</b> <a href='{GITHUB_URL}'>{GITHUB_URL}</a></p>"
        )

    def on_tray_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.show_normal_window()

    def show_normal_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def toggle_pause(self):
        subprocess.run(["pkill", "-STOP", "mpvpaper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def select_folder(self):
        dir_chosen = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de videos", str(self.current_folder)
        )
        if dir_chosen:
            self.current_folder = Path(dir_chosen)
            self.folder_subtitle.setText(f"Carpeta: {self.current_folder}")
            self.save_config()
            self.scan_folder()

    def scan_folder(self):
        for c in self.cards:
            self.grid.removeWidget(c)
            c.deleteLater()
        self.cards.clear()

        extensions = {".mp4", ".mkv", ".webm", ".mov"}
        videos = [p for p in self.current_folder.iterdir() if p.suffix.lower() in extensions]
        videos.sort()

        if not videos:
            self.status_lbl.setText("No se encontraron videos en la carpeta seleccionada.")
            return

        cols = 4
        prev_selected = set(self.config.get("selected", []))

        for idx, vid in enumerate(videos):
            row = idx // cols
            col = idx % cols
            card = VideoCard(vid, self.scroll_content)
            card.toggled.connect(self.on_card_toggled)

            if str(vid) in prev_selected:
                card.check.setChecked(True)

            self.grid.addWidget(card, row, col)
            self.cards.append(card)

        self.status_lbl.setText(f"{len(videos)} videos encontrados en la carpeta.")

    def on_card_toggled(self, video_path: Path, is_checked: bool):
        if is_checked:
            self.selected_videos.add(video_path)
        else:
            self.selected_videos.discard(video_path)

        count = len(self.selected_videos)
        if count == 0:
            self.status_lbl.setText("Ningún video seleccionado.")
        elif count == 1:
            self.status_lbl.setText("1 video seleccionado (reproducción en bucle único).")
        else:
            self.status_lbl.setText(f"{count} videos seleccionados (rotación continua y suave).")

    def stop_wallpaper(self):
        kill_all_instances()
        self.status_lbl.setText("Fondo animado detenido.")

    def apply_wallpaper(self):
        if not self.selected_videos:
            self.status_lbl.setText("⚠ Por favor selecciona al menos 1 video antes de aplicar.")
            return

        self.save_config()
        kill_all_instances()

        selected_list = list(self.selected_videos)
        selected_list.sort()

        if len(selected_list) == 1:
            vid = selected_list[0]
            cmd = [
                "mpvpaper",
                "-o", "no-audio loop-file=inf",
                "*",
                str(vid),
            ]
            subprocess.Popen(cmd)
            self.status_lbl.setText(f"✓ Aplicado: {vid.name}")
        else:
            playlist_path = Path("/tmp/cosmic_wallpaper_playlist.txt")
            with open(playlist_path, "w", encoding="utf-8") as f:
                for v in selected_list:
                    f.write(f"{v}\n")

            mpv_opts = "no-audio prefetch-playlist=yes keep-open=yes loop-playlist=inf"
            cmd = [
                "mpvpaper",
                "-o", mpv_opts,
                "*",
                str(playlist_path),
            ]
            subprocess.Popen(cmd)
            self.status_lbl.setText(f"✓ {len(selected_list)} videos aplicados en rotación suave.")

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray.showMessage(
            APP_NAME,
            "La aplicación sigue activa en tu bandeja del sistema.",
            QtWidgets.QSystemTrayIcon.Information,
            2000,
        )

    def quit_app(self):
        self.tray.hide()
        QtWidgets.QApplication.quit()


def main():
    test_mode = "--test-deps" in sys.argv
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = CosmicWallpaperApp(test_deps=test_mode)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
