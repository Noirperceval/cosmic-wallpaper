use std::env;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::time::Duration;

static PAUSED: AtomicBool = AtomicBool::new(false);

extern "C" {
    fn signal(sig: i32, handler: extern "C" fn(i32)) -> usize;
    fn kill(pid: i32, sig: i32) -> i32;
}

const SIGUSR1: i32 = 10;
const SIGSTOP: i32 = 19;
const SIGCONT: i32 = 18;

extern "C" fn handle_sigusr1(_sig: i32) {
    let prev = PAUSED.load(Ordering::SeqCst);
    PAUSED.store(!prev, Ordering::SeqCst);
    if !prev {
        println!("\n[PAUSA] Señal SIGUSR1 recibida: Video pausado.");
    } else {
        println!("\n[REANUDAR] Señal SIGUSR1 recibida: Video reanudado.");
    }
}

fn register_signals() {
    unsafe {
        signal(SIGUSR1, handle_sigusr1);
    }
}

// Cierra cualquier instancia previa de cosmic-wallpaper o mpvpaper
fn kill_all_previous_instances() {
    let current_pid = std::process::id();
    // Matar cualquier mpvpaper anterior
    let _ = Command::new("killall").arg("-9").arg("mpvpaper").output();
    
    // Matar instancias de cosmic-wallpaper anteriores a esta
    let out = Command::new("pgrep").arg("-f").arg("cosmic-wallpaper").output();
    if let Ok(o) = out {
        let text = String::from_utf8_lossy(&o.stdout);
        for line in text.lines() {
            if let Ok(pid) = line.trim().parse::<u32>() {
                if pid != current_pid {
                    unsafe {
                        kill(pid as i32, 9);
                    }
                }
            }
        }
    }
}

// Selector visual de carpetas con Zenity
fn pick_folder_zenity(initial_dir: &Path) -> Option<PathBuf> {
    let out = Command::new("zenity")
        .arg("--file-selection")
        .arg("--directory")
        .arg("--title=Cosmic Wallpaper: Selecciona la carpeta de videos")
        .arg(format!("--filename={}/", initial_dir.display()))
        .output()
        .ok()?;

    if out.status.success() {
        let path_str = String::from_utf8_lossy(&out.stdout).trim().to_string();
        if !path_str.is_empty() {
            return Some(PathBuf::from(path_str));
        }
    }
    None
}

// Selector con casillas de verificación
fn pick_videos_zenity(videos: &[PathBuf]) -> Vec<PathBuf> {
    if videos.is_empty() {
        return Vec::new();
    }

    let mut cmd = Command::new("zenity");
    cmd.arg("--list")
        .arg("--checklist")
        .arg("--title=Cosmic Wallpaper - Selecciona tus Videos")
        .arg("--text=Marca el o los videos que deseas reproducir:")
        .arg("--column=Elegir")
        .arg("--column=Archivo")
        .arg("--column=Ruta")
        .arg("--print-column=3")
        .arg("--hide-column=3")
        .arg("--width=750")
        .arg("--height=460")
        .arg("--separator=|");

    for p in videos {
        let filename = p.file_name().unwrap_or_default().to_string_lossy();
        cmd.arg("FALSE");
        cmd.arg(filename.to_string());
        cmd.arg(p.to_string_lossy().to_string());
    }

    let out = match cmd.output() {
        Ok(o) => o,
        Err(_) => return Vec::new(),
    };

    if out.status.success() {
        let res = String::from_utf8_lossy(&out.stdout).trim().to_string();
        if res.is_empty() {
            return Vec::new();
        }

        let mut selected = Vec::new();
        for item in res.split('|') {
            let path_str = item.trim();
            if !path_str.is_empty() {
                let p = PathBuf::from(path_str);
                if p.exists() {
                    selected.push(p);
                }
            }
        }
        selected
    } else {
        Vec::new()
    }
}

fn collect_videos(dir: &Path) -> Vec<PathBuf> {
    let entries = match fs::read_dir(dir) {
        Ok(e) => e,
        Err(err) => {
            eprintln!("Error al leer directorio {}: {}", dir.display(), err);
            return Vec::new();
        }
    };

    let mut videos: Vec<PathBuf> = entries
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| {
            if let Some(ext) = p.extension() {
                let ext_str = ext.to_string_lossy().to_lowercase();
                ext_str == "mp4" || ext_str == "mkv" || ext_str == "webm" || ext_str == "mov"
            } else {
                false
            }
        })
        .collect();

    videos.sort();
    videos
}

fn print_help() {
    println!(r#"Cosmic Wallpaper - Reproductor Nativo de Fondos Animados para COSMIC

Uso:
  cosmic-wallpaper [OPCIONES]

Opciones:
  -d, --dir <DIR>      Carpeta de videos (por defecto interactivo con Zenity)
  -c, --cli            Modo directo por terminal (sin ventana gráfica)
  -k, --kill           Detener completamente el fondo animado y cerrar
  -h, --help           Muestra esta ayuda

Control:
  Pausar o reanudar el fondo animado en cualquier momento con:
    pkill -SIGUSR1 -f cosmic-wallpaper
"#);
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.iter().any(|a| a == "-h" || a == "--help") {
        print_help();
        return;
    }

    if args.iter().any(|a| a == "-k" || a == "--kill") {
        kill_all_previous_instances();
        println!("Fondo animado detenido y procesos cerrados.");
        return;
    }

    register_signals();

    let default_video_dir = env::var("HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("/home/chable"))
        .join("Vídeos");

    let mut target_dir = default_video_dir;
    let mut use_gui = true;

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "-d" | "--dir" => {
                if i + 1 < args.len() {
                    target_dir = PathBuf::from(&args[i + 1]);
                    i += 1;
                }
            }
            "-c" | "--cli" => {
                use_gui = false;
            }
            _ => {}
        }
        i += 1;
    }

    if use_gui {
        if let Some(folder) = pick_folder_zenity(&target_dir) {
            target_dir = folder;
        }
    }

    println!("Buscando videos en: {}", target_dir.display());
    let all_videos = collect_videos(&target_dir);

    if all_videos.is_empty() {
        eprintln!("No se encontraron videos compatibles en {}", target_dir.display());
        return;
    }

    let playlist = if use_gui {
        let chosen = pick_videos_zenity(&all_videos);
        if chosen.is_empty() {
            println!("No seleccionaste ningún video o se canceló el diálogo.");
            return;
        }
        chosen
    } else {
        all_videos
    };

    println!("\n=== Videos seleccionados para reproducir ({} video/s) ===", playlist.len());
    for (idx, vid) in playlist.iter().enumerate() {
        println!(" [{}] {}", idx + 1, vid.file_name().unwrap_or_default().to_string_lossy());
    }
    println!("===========================================================");

    // Antes de lanzar el nuevo fondo, limpiamos radicalmente cualquier fondo anterior
    kill_all_previous_instances();

    let child_res: Result<Child, std::io::Error> = if playlist.len() == 1 {
        let single_video = &playlist[0];
        println!("Reproduciendo en bucle único: {}", single_video.display());
        Command::new("mpvpaper")
            .arg("-o")
            .arg("no-audio loop-file=inf")
            .arg("*")
            .arg(single_video)
            .spawn()
    } else {
        let playlist_path = env::temp_dir().join("cosmic_wallpaper_playlist.txt");
        {
            let mut file = match fs::File::create(&playlist_path) {
                Ok(f) => f,
                Err(e) => {
                    eprintln!("Error creando playlist temporal: {}", e);
                    return;
                }
            };
            for vid in &playlist {
                let _ = writeln!(file, "{}", vid.to_string_lossy());
            }
        }

        let mpv_opts = "no-audio prefetch-playlist=yes keep-open=yes loop-playlist=inf";
        println!("Iniciando rotación suave entre los videos seleccionados...");
        Command::new("mpvpaper")
            .arg("-o")
            .arg(mpv_opts)
            .arg("*")
            .arg(&playlist_path)
            .spawn()
    };

    let mut child = match child_res {
        Ok(c) => c,
        Err(err) => {
            eprintln!("Error al lanzar mpvpaper: {}", err);
            return;
        }
    };

    let pid = child.id() as i32;
    let mut was_paused = false;

    println!("✓ Fondo de pantalla activo.");
    println!("Control: Puedes ejecutar 'pkill -SIGUSR1 -f cosmic-wallpaper' para pausar/reanudar.");

    loop {
        let is_paused = PAUSED.load(Ordering::SeqCst);

        if is_paused && !was_paused {
            unsafe {
                kill(pid, SIGSTOP);
            }
            was_paused = true;
        } else if !is_paused && was_paused {
            unsafe {
                kill(pid, SIGCONT);
            }
            was_paused = false;
        }

        match child.try_wait() {
            Ok(Some(status)) => {
                println!("\nReproductor finalizado (código: {:?})", status.code());
                break;
            }
            Ok(None) => {
                thread::sleep(Duration::from_millis(150));
            }
            Err(e) => {
                eprintln!("Error en el reproductor: {}", e);
                break;
            }
        }
    }
}
