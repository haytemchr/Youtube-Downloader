import sys
import tkinter as tk
from tkinter import messagebox, filedialog
import re
import os
import threading
import time
import queue
import glob
import json
import subprocess
import traceback

# a faire: rajouter un bouton pour annuler le téléchargement

try:
    import customtkinter as ctk
    import requests
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError as e:
    root = tk.Tk()
    root.withdraw()
    missing_module = e.name if hasattr(e, 'name') else 'inconnu'
    if missing_module == 'inconnu':
        match = re.search(r"No module named '(\w+)'", str(e))
        if match:
            missing_module = match.group(1)
    messagebox.showerror(
        "Dépendance Manquante",
        f"Le module requis '{missing_module}' est introuvable.\n\n"
        "Pour que l'application fonctionne, veuillez installer les dépendances en exécutant la commande suivante dans le terminal :\n\n"
        "pip install -r requirements.txt"
    )
    sys.exit(f"Arrêt : Dépendance '{missing_module}' non trouvée.")

CONFIG_FILE = "config.json"

class YTDLLogger:
    def __init__(self, log_func):
        self.log_func = log_func
    
    def debug(self, msg):
        if "ERROR" in msg or "WARNING" in msg:
            self.log_func(f"⚠️ yt-dlp: {msg}")
    
    def warning(self, msg):
        if "JavaScript runtime" in msg or "js-runtimes" in msg or "EJS" in msg:
            return
        self.log_func(f"⚠️ yt-dlp: {msg}")
    
    def error(self, msg):
        self.log_func(f"❌ yt-dlp: {msg}")

class ConfigScreen:
    def __init__(self, parent):
        self.parent_window = parent[0]
        self.app_instance = parent[1]
        self.api_key = tk.StringVar()
        self.ffmpeg_path = tk.StringVar()
        self.load_config()
        self.window = ctk.CTkToplevel(self.parent_window)
        self.window.title("Configuration - YouTube Downloader")
        self.window.resizable(True, True)
        self.window.transient(self.parent_window)
        self.window.grab_set()
        self.window.update_idletasks()
        win_width = 711
        win_height = 613 
        x = (self.window.winfo_screenwidth() // 2) - (win_width // 2)
        y = (self.window.winfo_screenheight() // 2) - (win_height // 2)
        self.window.geometry(f"{win_width}x{win_height}+{x}+{y}")
        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        title = ctk.CTkLabel(main_frame, text="Configuration", font=("Helvetica", 20, "bold"))
        title.pack(pady=20)
        desc = ctk.CTkLabel(main_frame, text="Une clé API YouTube est recommandée pour une meilleure gestion des métadonnées des PLAYLISTS, mais n'est pas obligatoire pour le téléchargement.", font=("Helvetica", 12), wraplength=400, text_color="orange")
        desc.pack(pady=10)
        desc2 = ctk.CTkLabel(main_frame, text="En revanche, pour les VIDÉOS UNIQUES, vous n'en avez pas besoin.", font=("Helvetica", 12), wraplength=400, text_color="green")
        desc2.pack(pady=5)
        api_frame = ctk.CTkFrame(main_frame)
        api_frame.pack(fill=tk.X, padx=20, pady=20)
        api_label = ctk.CTkLabel(api_frame, text="Clé API YouTube :")
        api_label.pack(side=tk.LEFT, padx=5)
        self.api_entry = ctk.CTkEntry(api_frame, textvariable=self.api_key, width=300, show="*")
        self.api_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.show_key_var = tk.BooleanVar(value=False)
        show_key_btn = ctk.CTkCheckBox(api_frame, text="Afficher", variable=self.show_key_var, command=self.toggle_key_visibility)
        show_key_btn.pack(side=tk.RIGHT, padx=5)

        ffmpeg_frame = ctk.CTkFrame(main_frame)
        ffmpeg_frame.pack(fill=tk.X, padx=20, pady=10)
        ffmpeg_label = ctk.CTkLabel(ffmpeg_frame, text="Chemin FFmpeg (dossier 'bin') :")
        ffmpeg_label.pack(side=tk.LEFT, padx=5)
        if not self.ffmpeg_path.get() and hasattr(self.app_instance, 'ffmpeg_path'):
            self.ffmpeg_path.set(self.app_instance.ffmpeg_path.get())
        self.ffmpeg_entry = ctk.CTkEntry(ffmpeg_frame, textvariable=self.ffmpeg_path, width=300)
        self.ffmpeg_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ffmpeg_browse_btn = ctk.CTkButton(ffmpeg_frame, text="Parcourir", command=self.browse_ffmpeg_folder)
        ffmpeg_browse_btn.pack(side=tk.RIGHT, padx=5)
        ffmpeg_desc = ctk.CTkLabel(main_frame, text="Indiquez le chemin du dossier 'bin' de FFmpeg (ex: C:\\ffmpeg\\bin). Nécessaire pour fusionner vidéo/audio et convertir en MP3.", font=("Helvetica", 10), wraplength=400, text_color="gray")
        ffmpeg_desc.pack(pady=5)

        instructions = ctk.CTkLabel(main_frame, text="Instructions pour obtenir une clé API :\n1. Allez sur https://console.cloud.google.com/\n2. Créez un projet ou sélectionnez-en un existant\n3. Activez l'API YouTube Data v3\n4. Créez des identifiants (clé API)\n5. Copiez la clé et collez-la ci-dessus", font=("Helvetica", 17), justify=tk.LEFT, wraplength=500)
        instructions.pack(pady=10)
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        save_btn = ctk.CTkButton(button_frame, text="Sauvegarder", command=self.save_config, height=35, font=("Helvetica", 12, "bold"))
        save_btn.pack(side=tk.RIGHT, padx=5)
        skip_btn = ctk.CTkButton(button_frame, text="Passer", command=self.skip_config, height=35, font=("Helvetica", 12))
        skip_btn.pack(side=tk.RIGHT, padx=5)

    def toggle_key_visibility(self):
        if self.show_key_var.get():
            self.api_entry.configure(show="")
        else:
            self.api_entry.configure(show="*")

    def browse_ffmpeg_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.ffmpeg_path.set(folder)

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.api_key.set(config.get('api_key', ''))
                    self.ffmpeg_path.set(config.get('ffmpeg_path', ''))
        except Exception as e:
            print("Erreur lors du chargement de la configuration: " + str(e))

    def save_config(self):
        try:
            config = {
                'api_key': self.api_key.get().strip(),
                'ffmpeg_path': self.ffmpeg_path.get().strip()
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Succès", "Configuration sauvegardée avec succès!")
            self.app_instance.load_settings()
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")

    def skip_config(self):
        self.window.destroy()

class FFmpegInfoScreen:
    def __init__(self, parent):
        self.parent_window = parent[0]
        self.app_instance = parent[1]
        self.window = ctk.CTkToplevel(self.parent_window)
        self.window.title("Alerte FFmpeg - YouTube Downloader")
        
        win_width = 600
        win_height = 550
        
        self.window.resizable(False, False)
        self.window.transient(self.parent_window)
        self.window.grab_set()
        self.window.update_idletasks()
        
        x = (self.window.winfo_screenwidth() // 2) - (win_width // 2)
        y = (self.window.winfo_screenheight() // 2) - (win_height // 2)
        self.window.geometry(f"{win_width}x{win_height}+{x}+{y}")
        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title = ctk.CTkLabel(main_frame, text="FFmpeg est Recommandé", font=("Helvetica", 22, "bold"), text_color="#FFCC00")
        title.pack(pady=(0, 15))
        
        info_text = (
            "FFmpeg est un outil essentiel pour obtenir la meilleure qualité vidéo et pour convertir les fichiers en MP3.\n\n"
            "Pourquoi est-il nécessaire ?\n"
            "• Fusion : YouTube sépare la vidéo HD et l'audio. FFmpeg les réunit.\n"
            "• Conversion : Indispensable pour le format MP3.\n\n"
            "Sans lui, vous serez limité au 720p et le MP3 échouera."
        )
        info_label = ctk.CTkLabel(main_frame, text=info_text, font=("Helvetica", 13), justify=tk.LEFT, wraplength=550)
        info_label.pack(pady=10, anchor="w")
        
        download_text = (
            "Comment l'obtenir ?\n"
            "1. Téléchargez FFmpeg (Essentiels) sur ffmpeg.org\n"
            "2. Décompressez l'archive.\n"
            "3. Indiquez le chemin vers le dossier 'bin' dans les paramètres."
        )
        download_label = ctk.CTkLabel(main_frame, text=download_text, font=("Helvetica", 13, "bold"), justify=tk.LEFT, wraplength=550)
        download_label.pack(pady=15, anchor="w")
        
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill=tk.X, pady=(20, 0), side=tk.BOTTOM)
        
        settings_btn = ctk.CTkButton(button_frame, text="Ouvrir les Paramètres", command=self.open_settings, height=35)
        settings_btn.pack(side=tk.LEFT, padx=(0, 10), expand=True)
        
        continue_btn = ctk.CTkButton(button_frame, text="Continuer sans FFmpeg", command=self.window.destroy, fg_color="gray", height=35)
        continue_btn.pack(side=tk.RIGHT, padx=(10, 0), expand=True)

    def open_settings(self):
        self.window.destroy()
        self.app_instance.show_settings()

class YouTubeDownloader:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("YouTube Downloader")
        self.window.geometry("800x800")
        self.window.resizable(True, True)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.download_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.url = tk.StringVar()
        self.is_playlist = tk.BooleanVar(value=False)
        self.api_key = tk.StringVar()
        self.ffmpeg_path = tk.StringVar()
        self.load_settings()
        self.message_queue = queue.Queue()
        self.format_var = tk.StringVar(value="mp4")
        self.quality_var = tk.StringVar(value="720p")
        self.available_qualities = []
        self.show_config_if_needed()
        self.create_widgets()
        self.window.after(100, self.process_messages)

    def load_settings(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.api_key.set(config.get('api_key', ''))
                    self.ffmpeg_path.set(config.get('ffmpeg_path', ''))
        except Exception as e:
            print("Erreur lors du chargement des paramètres: " + str(e))

    def show_config_if_needed(self):
        no_ffmpeg_path = not self.ffmpeg_path.get().strip()
        no_ffmpeg_global = not self._check_ffmpeg_global_availability()

        if no_ffmpeg_path and no_ffmpeg_global:
            self.window.after(100, self.show_ffmpeg_info_screen)
        elif not os.path.exists(CONFIG_FILE):
            self.window.after(100, self.show_config_screen)

    def show_config_screen(self):
        config_screen = ConfigScreen((self.window, self))
        self.window.wait_window(config_screen.window)

    def show_ffmpeg_info_screen(self):
        ffmpeg_screen = FFmpegInfoScreen((self.window, self))
        self.window.wait_window(ffmpeg_screen.window)

    def show_settings(self):
        config_screen = ConfigScreen((self.window, self))
        self.window.wait_window(config_screen.window)

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        title = ctk.CTkLabel(main_frame, text="YouTube Downloader", font=("Helvetica", 24, "bold"))
        title.pack(pady=20)
        url_frame = ctk.CTkFrame(main_frame)
        url_frame.pack(fill=tk.X, padx=20, pady=10)
        url_label = ctk.CTkLabel(url_frame, text="URL YouTube :")
        url_label.pack(side=tk.LEFT, padx=5)
        url_entry = ctk.CTkEntry(url_frame, textvariable=self.url, width=400)
        url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        check_btn = ctk.CTkButton(url_frame, text="Vérifier", command=self.check_available_qualities, width=80)
        check_btn.pack(side=tk.LEFT, padx=5)
        type_frame = ctk.CTkFrame(main_frame)
        type_frame.pack(fill=tk.X, padx=20, pady=10)
        video_radio = ctk.CTkRadioButton(type_frame, text="Vidéo unique", variable=self.is_playlist, value=False)
        video_radio.pack(side=tk.LEFT, padx=20)
        playlist_radio = ctk.CTkRadioButton(type_frame, text="Playlist", variable=self.is_playlist, value=True)
        playlist_radio.pack(side=tk.LEFT, padx=20)
        format_frame = ctk.CTkFrame(main_frame)
        format_frame.pack(fill=tk.X, padx=20, pady=10)
        format_label = ctk.CTkLabel(format_frame, text="Format :")
        format_label.pack(side=tk.LEFT, padx=5)
        mp4_radio = ctk.CTkRadioButton(format_frame, text="MP4 (Vidéo)", variable=self.format_var, value="mp4", command=self.update_quality_options)
        mp4_radio.pack(side=tk.LEFT, padx=20)
        mp3_radio = ctk.CTkRadioButton(format_frame, text="MP3 (Audio)", variable=self.format_var, value="mp3", command=self.update_quality_options)
        mp3_radio.pack(side=tk.LEFT, padx=20)
        self.quality_frame = ctk.CTkFrame(main_frame)
        self.quality_frame.pack(fill=tk.X, padx=20, pady=10)
        quality_label = ctk.CTkLabel(self.quality_frame, text="Qualité :")
        quality_label.pack(side=tk.LEFT, padx=5)
        self.quality_menu = ctk.CTkOptionMenu(self.quality_frame, variable=self.quality_var, values=["720p", "1080p", "480p", "360p", "Meilleure qualité"])
        self.quality_menu.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        path_frame = ctk.CTkFrame(main_frame)
        path_frame.pack(fill=tk.X, padx=20, pady=10)
        path_label = ctk.CTkLabel(path_frame, text="Dossier de téléchargement :")
        path_label.pack(side=tk.LEFT, padx=5)
        path_entry = ctk.CTkEntry(path_frame, textvariable=self.download_path, width=300)
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        browse_button = ctk.CTkButton(path_frame, text="Parcourir", command=self.browse_folder)
        browse_button.pack(side=tk.LEFT, padx=5)
        self.progress_frame = ctk.CTkFrame(main_frame)
        self.progress_frame.pack(fill=tk.X, padx=20, pady=10)
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="")
        self.progress_label.pack(pady=5)
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill=tk.X, pady=5)
        self.progress_bar.set(0)
        self.log_text = ctk.CTkTextbox(main_frame, height=200)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.download_button = ctk.CTkButton(main_frame, text="Télécharger", command=self.start_download, height=40, font=("Helvetica", 14, "bold"))
        self.download_button.pack(pady=20, fill=tk.X, padx=20)
        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.pack(fill=tk.X, padx=20, pady=10)
        settings_button = ctk.CTkButton(bottom_frame, text="⚙️ Paramètres", command=self.show_settings, height=30, font=("Helvetica", 12))
        settings_button.pack(side=tk.LEFT, padx=5)
        credit_label = ctk.CTkLabel(bottom_frame, text="Créé par Haytem CHRYAT", font=("Helvetica", 12, "italic"))
        credit_label.pack(side=tk.RIGHT, padx=5)

    def update_quality_options(self):
        if self.format_var.get() == "mp3":
            self.quality_menu.configure(values=["Meilleure qualité"])
            self.quality_var.set("Meilleure qualité")
        else:
            if self.available_qualities:
                qualities = self.available_qualities + ["Meilleure qualité"]
                self.quality_menu.configure(values=qualities)
                if self.quality_var.get() not in qualities:
                    self.quality_var.set(qualities[0] if qualities else "Meilleure qualité")
            else:
                self.quality_menu.configure(values=["720p", "1080p", "480p", "360p", "Meilleure qualité"])
    
    def check_available_qualities(self):
        yt_url = self.url.get().strip()
        if not yt_url or not yt_url.startswith(("https://www.youtube.com/", "https://youtu.be/")):
            messagebox.showwarning("Attention", "Veuillez entrer une URL YouTube valide")
            return
        
        if not YT_DLP_AVAILABLE:
            messagebox.showerror("Erreur", "yt-dlp n'est pas installé")
            return
        
        self.log("Vérification des qualités disponibles...")
        self.quality_menu.configure(state="disabled")
        
        def check_thread():
            try:
                opts = {
                    'quiet': True,
                    'no_warnings': True,
                }
                with yt_dlp.YoutubeDL(opts) as ydl:
                    data = ydl.extract_info(yt_url, download=False)
                    fmts = data.get('formats', [])
                    heights = set()
                    for fmt in fmts:
                        height = fmt.get('height')
                        if height and fmt.get('vcodec') != 'none':
                            heights.add(height)
                    sorted_h = sorted(heights, reverse=True)
                    q_list = [f"{h}p" for h in sorted_h]
                    self.window.after(0, lambda: self.update_quality_menu(q_list))
                    self.log(f"✓ Qualités disponibles: {', '.join(q_list)}")
            except Exception as e:
                err = str(e)
                if 'requested_formats' not in err:
                    self.log(f"❌ Erreur lors de la vérification: {err}")
                self.window.after(0, lambda: self.update_quality_menu([]))
        
        t = threading.Thread(target=check_thread)
        t.daemon = True
        t.start()
    
    def update_quality_menu(self, qualities):
        self.available_qualities = qualities
        if qualities:
            quality_values = qualities + ["Meilleure qualité"]
            self.quality_menu.configure(values=quality_values, state="normal")
            if self.quality_var.get() not in quality_values:
                self.quality_var.set(qualities[0] if qualities else "Meilleure qualité")
        else:
            quality_values = ["720p", "1080p", "480p", "360p", "Meilleure qualité"]
            self.quality_menu.configure(values=quality_values, state="normal")
            if self.quality_var.get() not in quality_values:
                self.quality_var.set("720p")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path.set(folder)

    def log(self, message):
        self.message_queue.put(("log", message))

    def update_progress(self, value, text=""):
        self.message_queue.put(("progress", (value, text)))

    def process_messages(self):
        # je vide la queue des logs/progress a chaque tick
        try:
            while True:
                kind, payload = self.message_queue.get_nowait()
                if kind == "log":
                    self.log_text.insert(tk.END, payload + "\n")
                    self.log_text.see(tk.END)
                elif kind == "progress":
                    val, txt = payload
                    self.progress_bar.set(val)
                    if txt:
                        self.progress_label.configure(text=txt)
        except queue.Empty:
            pass
        self.window.after(100, self.process_messages)

    def download_with_ytdlp(self, url):
        # Sécurité de base : si yt-dlp n'est pas là, on coupe tout
        if not YT_DLP_AVAILABLE:
            return False
        
        try:
            dl_path = self.download_path.get()
            
            # je prepare tout avt le telechargement pour eviter les bugs
            if self.format_var.get() == "mp3":
                fmt = "bestaudio/best"
                post = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                q = self.quality_var.get()
                if q == "Meilleure qualité":
                    fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                else:
                    try:
                        h = int(q.replace('p', ''))
                        fmt = (
                            f"bestvideo[height={h}][ext=mp4]+bestaudio[ext=m4a]/"
                            f"best[height={h}][ext=mp4]/"
                            f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/"
                            f"best[height<={h}][ext=mp4]"
                        )
                    except ValueError:
                        # si la qualite est bizarre je prends une valeur safe
                        fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                post = []

            # options envoyees a yt-dlp
            opts = {
                'format': fmt,
                'outtmpl': os.path.join(dl_path, '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'postprocessors': post,
                'progress_hooks': [self.ytdlp_progress_hook],
                'ignoreerrors': False,
                'logger': YTDLLogger(self.log),
                'noplaylist': True,
                'no_playlist': True,
            }

            # si ffmpeg est renseigne je le passe ici
            ffmpeg_loc = self.ffmpeg_path.get().strip()
            if ffmpeg_loc:
                opts['ffmpeg_location'] = ffmpeg_loc

            if self.format_var.get() == "mp4":
                opts['merge_output_format'] = 'mp4'

            # go telechargement
            with yt_dlp.YoutubeDL(opts) as ydl:
                vid_title = 'Vidéo'
                
                # je tente de recup le titre pour un log plus clean
                try:
                    data = ydl.extract_info(url, download=False)
                    vid_title = data.get('title', url)
                except Exception:
                    # si ca rate je bloque pas le download
                    pass
                
                self.log(f"Téléchargement de : {vid_title}")
                
                try:
                    ydl.download([url])
                    self.log(f"✓ {vid_title} téléchargé avec succès avec yt-dlp!")
                    return True
                    
                except Exception as dl_err:
                    err = str(dl_err).lower()
                    
                    # je check si ca vient de ffmpeg
                    ffmpeg_errs = ["could not find codec", "postprocessing", "error splitting", "ffmpeg"]
                    
                    if any(k in err for k in ffmpeg_errs):
                        self.log(f"❌ Erreur de post-traitement (probablement FFmpeg): {str(dl_err)}")
                        self.log("💡 Astuce: Assurez-vous que FFmpeg est installé et accessible dans votre PATH.")
                        self.log("         Vous pouvez le télécharger depuis https://ffmpeg.org/download.html")
                        
                        # je verifie si un fichier brut existe deja
                        pat = os.path.join(dl_path, f"{vid_title}.*")
                        files = glob.glob(pat)
                        
                        media = [f for f in files if os.path.isfile(f) and 
                                 (f.endswith('.mp4') or f.endswith('.mp3') or f.endswith('.webm') or f.endswith('.m4a')) and
                                 os.path.getsize(f) > 1024]
                        
                        if media:
                            self.log(f"⚠️ Un fichier média brut a été téléchargé : {os.path.basename(media[0])}")
                            self.log("  Cependant, le post-traitement (fusion/conversion) a échoué.")
                            return True
                        else:
                            self.log("❌ Aucun fichier média brut n'a été trouvé après l'échec du post-traitement.")
                            return False
                    else:
                        # si c pas ffmpeg je laisse remonter l'erreur
                        raise dl_err

        except Exception as e:
            err = str(e)
            # faux positif connu de yt-dlp
            if "requested_formats" in err:
                # cas bizarre yt-dlp, je force ok pour pas bloquer
                return True
                
            self.log(f"❌ Erreur avec yt-dlp: {err}")
            return False
                
    def _check_ffmpeg_global_availability(self):
        try:
            subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def ytdlp_progress_hook(self, d):
        try:
            if d['status'] == 'downloading':
                if 'total_bytes' in d and d['total_bytes']:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    self.update_progress(percent / 100, f"Téléchargement: {percent:.1f}%")
                elif 'downloaded_bytes' in d:
                    self.update_progress(0.5, "Téléchargement en cours...")
                else:
                    self.update_progress(0.3, "Téléchargement en cours...")
            elif d['status'] == 'finished':
                self.update_progress(1.0, "Téléchargement terminé!")
        except:
            # si y a une erreur dans le hook je bloque pas le download
            pass
     
    def download_video(self, url, max_retries=3):
        if not YT_DLP_AVAILABLE:
            self.log("❌ yt-dlp n'est pas installé. Installez-le avec: pip install yt-dlp")
            return False
        
        for tr in range(max_retries):
            if tr > 0:
                self.log(f"Tentative {tr + 1}/{max_retries}...")
                time.sleep(2)
            
            if self.download_with_ytdlp(url):
                return True
        
        return False

    def get_playlist_videos_with_api(self, playlist_url):
        try:
            pid_match = re.search(r'list=([a-zA-Z0-9_-]+)', playlist_url)
            if not pid_match:
                self.log("❌ URL de playlist invalide")
                return []
            pid = pid_match.group(1)
            key = self.api_key.get().strip()
            if not key:
                # pas de clé api -> fallback yt-dlp
                self.log("⚠️ Aucune clé API fournie. Tentative sans API...")
                return self.extract_playlist_videos(playlist_url)
            self.log("Récupération des vidéos de la playlist via l'API YouTube...")
            pl_api_url = f"https://www.googleapis.com/youtube/v3/playlists?part=snippet&id={pid}&key={key}"
            pl_res = requests.get(pl_api_url)
            pl_res.raise_for_status()
            pl_data = pl_res.json()
            
            if 'error' in pl_data:
                err_info = pl_data['error']
                err_msg = err_info.get('message', 'Erreur inconnue')
                self.log(f"❌ Erreur API YouTube: {err_msg}")
                return []
            
            if 'items' not in pl_data or not pl_data['items']:
                self.log("❌ Playlist non trouvée ou inaccessible")
                return []
            
            try:
                pl_title = pl_data['items'][0]['snippet']['title']
                self.log(f"Playlist trouvée : {pl_title}")
            except (KeyError, IndexError, TypeError) as e:
                self.log(f"⚠️ Erreur lors de la récupération du titre de la playlist: {e}")
                self.log("Continuation du téléchargement...")
            vid_urls = []
            next_token = None
            while True:
                if next_token:
                    items_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={pid}&pageToken={next_token}&key={key}"
                else:
                    items_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={pid}&key={key}"
                items_res = requests.get(items_url)
                items_res.raise_for_status()
                items_data = items_res.json()
                
                if 'error' in items_data:
                    err_info = items_data['error']
                    err_msg = err_info.get('message', 'Erreur inconnue')
                    self.log(f"❌ Erreur API YouTube: {err_msg}")
                    break
                
                if 'items' not in items_data:
                    self.log("❌ Erreur lors de la récupération des vidéos de la playlist")
                    break
                
                if not isinstance(items_data['items'], list):
                    self.log("❌ Format de données invalide dans la réponse de l'API")
                    break
                
                if not items_data['items']:
                    break
                
                for item in items_data['items']:
                    try:
                        if 'snippet' not in item or 'resourceId' not in item['snippet']:
                            continue
                        vid_id = item['snippet']['resourceId']['videoId']
                        if not vid_id:
                            continue
                        vid_url = f"https://www.youtube.com/watch?v={vid_id}"
                        vid_urls.append(vid_url)
                    except (KeyError, TypeError) as e:
                        self.log(f"⚠️ Erreur lors du traitement d'un élément de la playlist: {e}")
                        continue
                if 'nextPageToken' in items_data:
                    next_token = items_data['nextPageToken']
                else:
                    break
            self.log(f"✓ {len(vid_urls)} vidéos trouvées dans la playlist")
            return vid_urls
        except Exception as e:
            self.log(f"❌ Erreur lors de la récupération des vidéos via l'API: {str(e)}")
            self.log("Tentative sans API...")
            return self.extract_playlist_videos(playlist_url)

    def extract_playlist_videos(self, playlist_url):
        self.log("Récupération des vidéos de la playlist via yt-dlp (mode fallback)...")
        try:
            opts = {
                'quiet': True,
                'extract_flat': True,
                'force_generic_extractor': True,
                'noplaylist': False,
                'logger': YTDLLogger(self.log),
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = ydl.extract_info(playlist_url, download=False)
                
            vid_urls = []
            if 'entries' in data:
                for entry in data['entries']:
                    if 'url' in entry and entry.get('url'):
                        vid_urls.append(entry['url'])
            
            if not vid_urls:
                self.log("❌ Aucune vidéo trouvée dans la playlist")
                return []
            self.log(f"✓ {len(vid_urls)} vidéos trouvées dans la playlist")
            return vid_urls
        except Exception as e:
            self.log(f"❌ Erreur lors de l'extraction des vidéos de la playlist: {str(e)}")
            return []

    def download_playlist(self, url):
        try:
            vid_urls = self.get_playlist_videos_with_api(url)
            if not vid_urls:
                self.log("❌ Aucune vidéo trouvée dans la playlist")
                return False
            self.log(f"Téléchargement de la playlist avec {len(vid_urls)} vidéos")
            total = len(vid_urls)
            for i, vid_url in enumerate(vid_urls, 1):
                self.update_progress(i/total, f"Téléchargement {i}/{total}")
                self.download_video(vid_url)
            self.update_progress(1, "Téléchargement terminé!")
            return True
        except Exception as e:
            self.log(f"❌ Erreur lors du téléchargement de la playlist: {str(e)}")
            self.log("Conseil: Vérifiez que l'URL de la playlist est correcte et accessible")
            return False

    def start_download(self):
        yt_url = self.url.get().strip()
        if not yt_url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL YouTube")
            return
        if not re.match(r"^(https?://)?(www\.|m\.|music\.)?(youtube\.com|youtu\.be)/.+", yt_url):
            messagebox.showerror("Erreur", "Veuillez entrer une URL YouTube valide.")
            return
        dl_dir = self.download_path.get()
        if not os.path.exists(dl_dir):
            try:
                os.makedirs(dl_dir)
                self.log(f"Dossier créé : {dl_dir}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de créer le dossier de téléchargement : {str(e)}")
                return
        self.download_button.configure(state="disabled")
        self.update_progress(0, "")
        # je lance un thread pour pas freeze l'interface
        def download_thread():
            try:
                if self.is_playlist.get():
                    self.download_playlist(yt_url)
                else:
                    self.download_video(yt_url)
            except Exception as e:
                self.log(f"❌ Erreur critique lors du téléchargement: {str(e)}")
                self.log(f"Détails: {traceback.format_exc()}")
            finally:
                self.message_queue.put(("progress", (0, "")))
                self.message_queue.put(("log", "Téléchargement terminé"))
                self.window.after(0, lambda: self.download_button.configure(state="normal"))
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.window.mainloop()