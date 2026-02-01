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
            print(f"Erreur lors du chargement de la configuration: {e}")

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
            print(f"Erreur lors du chargement des paramètres: {e}")

    def show_config_if_needed(self):
        ffmpeg_path_missing_in_config = not self.ffmpeg_path.get().strip()
        ffmpeg_not_globally_available = not self._check_ffmpeg_global_availability()

        if ffmpeg_path_missing_in_config and ffmpeg_not_globally_available:
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
        url = self.url.get().strip()
        if not url or not url.startswith(("https://www.youtube.com/", "https://youtu.be/")):
            messagebox.showwarning("Attention", "Veuillez entrer une URL YouTube valide")
            return
        
        if not YT_DLP_AVAILABLE:
            messagebox.showerror("Erreur", "yt-dlp n'est pas installé")
            return
        
        self.log("Vérification des qualités disponibles...")
        self.quality_menu.configure(state="disabled")
        
        def check_thread():
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    formats = info.get('formats', [])
                    available_heights = set()
                    for fmt in formats:
                        height = fmt.get('height')
                        if height and fmt.get('vcodec') != 'none':
                            available_heights.add(height)
                    sorted_heights = sorted(available_heights, reverse=True)
                    quality_list = [f"{h}p" for h in sorted_heights]
                    self.window.after(0, lambda: self.update_quality_menu(quality_list))
                    self.log(f"✓ Qualités disponibles: {', '.join(quality_list)}")
            except Exception as e:
                error_str = str(e)
                if 'requested_formats' not in error_str:
                    self.log(f"❌ Erreur lors de la vérification: {error_str}")
                self.window.after(0, lambda: self.update_quality_menu([]))
        
        thread = threading.Thread(target=check_thread)
        thread.daemon = True
        thread.start()
    
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
        try:
            while True:
                msg_type, content = self.message_queue.get_nowait()
                if msg_type == "log":
                    self.log_text.insert(tk.END, content + "\n")
                    self.log_text.see(tk.END)
                elif msg_type == "progress":
                    value, text = content
                    self.progress_bar.set(value)
                    if text:
                        self.progress_label.configure(text=text)
        except queue.Empty:
            pass
        self.window.after(100, self.process_messages)

    def download_with_ytdlp(self, url):
        if not YT_DLP_AVAILABLE:
            return False
        
        try:
            download_path = self.download_path.get()
            if self.format_var.get() == "mp3":
                format_selector = "bestaudio/best"
                postprocessors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                quality = self.quality_var.get()
                if quality == "Meilleure qualité":
                    format_selector = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                else:
                    try:
                        height = int(quality.replace('p', ''))
                        format_selector = (
                            f"bestvideo[height={height}][ext=mp4]+bestaudio[ext=m4a]/"
                            f"best[height={height}][ext=mp4]/"
                            f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
                            f"best[height<={height}][ext=mp4]"
                        )
                    except ValueError:
                        format_selector = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                postprocessors = []
            
            ydl_opts = {
                'format': format_selector,
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'postprocessors': postprocessors,
                'progress_hooks': [self.ytdlp_progress_hook],
                'ignoreerrors': False,
                'logger': YTDLLogger(self.log),
                'noplaylist': True,
                'no_playlist': True,
            }

            ffmpeg_location = self.ffmpeg_path.get().strip()
            if ffmpeg_location:
                ydl_opts['ffmpeg_location'] = ffmpeg_location

            if self.format_var.get() == "mp4":
                ydl_opts['merge_output_format'] = 'mp4'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_title = 'Vidéo'
                try:
                    info = ydl.extract_info(url, download=False)
                    video_title = info.get('title', url)
                except (KeyError, TypeError) as info_error:
                    error_str = str(info_error)
                    if 'requested_formats' in error_str:
                        pass
                    else:
                        pass
                except Exception as info_error:
                    pass
                
                self.log(f"Téléchargement de : {video_title}")
                
                try:
                    ydl.download([url])
                    self.log(f"✓ {video_title} téléchargé avec succès avec yt-dlp!")
                    return True
                except Exception as download_error:
                    error_str = str(download_error)
                    if "could not find codec" in error_str.lower() or \
                       "postprocessing" in error_str.lower() or \
                       "error splitting" in error_str.lower() or \
                       "ffmpeg" in error_str.lower():
                          
                          self.log(f"❌ Erreur de post-traitement (probablement FFmpeg): {error_str}")
                          self.log("💡 Astuce: Assurez-vous que FFmpeg est installé et accessible dans votre PATH.")
                          self.log("         Vous pouvez le télécharger depuis https://ffmpeg.org/download.html")
                          
                          import glob
                          download_path_check = self.download_path.get()
                          pattern_check = os.path.join(download_path_check, f"{video_title}.*")
                          existing_files = glob.glob(pattern_check)
                          
                          media_files = [f for f in existing_files if os.path.isfile(f) and 
                                         (f.endswith('.mp4') or f.endswith('.mp3') or f.endswith('.webm') or f.endswith('.m4a')) and
                                         os.path.getsize(f) > 1024]
                          
                          if media_files:
                              self.log(f"⚠️ Un fichier média brut a été téléchargé : {os.path.basename(media_files[0])}")
                              self.log("   Cependant, le post-traitement (fusion/conversion) a échoué.")
                              return True
                          else:
                              self.log("❌ Aucun fichier média brut n'a été trouvé après l'échec du post-traitement.")
                              return False
                    else:
                        raise download_error

        except Exception as e:
            error_str = str(e)
            if "'requested_formats'" in error_str or "requested_formats" in error_str:
                return True
            self.log(f"❌ Erreur avec yt-dlp: {error_str}")
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
             pass
     
    def download_video(self, url, max_retries=3):
        if not YT_DLP_AVAILABLE:
            self.log("❌ yt-dlp n'est pas installé. Installez-le avec: pip install yt-dlp")
            return False
        
        for attempt in range(max_retries):
            if attempt > 0:
                self.log(f"Tentative {attempt + 1}/{max_retries}...")
                time.sleep(2)
            
            if self.download_with_ytdlp(url):
                return True
        
        return False

    def get_playlist_videos_with_api(self, playlist_url):
        try:
            playlist_id_match = re.search(r'list=([a-zA-Z0-9_-]+)', playlist_url)
            if not playlist_id_match:
                self.log("❌ URL de playlist invalide")
                return []
            playlist_id = playlist_id_match.group(1)
            api_key = self.api_key.get().strip()
            if not api_key:
                self.log("⚠️ Aucune clé API fournie. Tentative sans API...")
                return self.extract_playlist_videos(playlist_url)
            self.log("Récupération des vidéos de la playlist via l'API YouTube...")
            playlist_url_api = f"https://www.googleapis.com/youtube/v3/playlists?part=snippet&id={playlist_id}&key={api_key}"
            playlist_response = requests.get(playlist_url_api)
            playlist_response.raise_for_status()
            playlist_data = playlist_response.json()
            
            if 'error' in playlist_data:
                error_info = playlist_data['error']
                error_message = error_info.get('message', 'Erreur inconnue')
                self.log(f"❌ Erreur API YouTube: {error_message}")
                return []
            
            if 'items' not in playlist_data or not playlist_data['items']:
                self.log("❌ Playlist non trouvée ou inaccessible")
                return []
            
            try:
                playlist_title = playlist_data['items'][0]['snippet']['title']
                self.log(f"Playlist trouvée : {playlist_title}")
            except (KeyError, IndexError, TypeError) as e:
                self.log(f"⚠️ Erreur lors de la récupération du titre de la playlist: {e}")
                self.log("Continuation du téléchargement...")
            video_urls = []
            next_page_token = None
            while True:
                if next_page_token:
                    playlist_items_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={playlist_id}&pageToken={next_page_token}&key={api_key}"
                else:
                    playlist_items_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={playlist_id}&key={api_key}"
                playlist_items_response = requests.get(playlist_items_url)
                playlist_items_response.raise_for_status()
                playlist_items_data = playlist_items_response.json()
                
                if 'error' in playlist_items_data:
                    error_info = playlist_items_data['error']
                    error_message = error_info.get('message', 'Erreur inconnue')
                    self.log(f"❌ Erreur API YouTube: {error_message}")
                    break
                
                if 'items' not in playlist_items_data:
                    self.log("❌ Erreur lors de la récupération des vidéos de la playlist")
                    break
                
                if not isinstance(playlist_items_data['items'], list):
                    self.log("❌ Format de données invalide dans la réponse de l'API")
                    break
                
                if not playlist_items_data['items']:
                    break
                
                for item in playlist_items_data['items']:
                    try:
                        if 'snippet' not in item or 'resourceId' not in item['snippet']:
                            continue
                        video_id = item['snippet']['resourceId']['videoId']
                        if not video_id:
                            continue
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        video_urls.append(video_url)
                    except (KeyError, TypeError) as e:
                        self.log(f"⚠️ Erreur lors du traitement d'un élément de la playlist: {e}")
                        continue
                if 'nextPageToken' in playlist_items_data:
                    next_page_token = playlist_items_data['nextPageToken']
                else:
                    break
            self.log(f"✓ {len(video_urls)} vidéos trouvées dans la playlist")
            return video_urls
        except Exception as e:
            self.log(f"❌ Erreur lors de la récupération des vidéos via l'API: {str(e)}")
            self.log("Tentative sans API...")
            return self.extract_playlist_videos(playlist_url)

    def extract_playlist_videos(self, playlist_url):
        self.log("Récupération des vidéos de la playlist via yt-dlp (mode fallback)...")
        try:
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
                'force_generic_extractor': True,
                'noplaylist': False,
                'logger': YTDLLogger(self.log),
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                
            video_urls = []
            if 'entries' in info:
                for entry in info['entries']:
                    if 'url' in entry and entry.get('url'):
                        video_urls.append(entry['url'])
            
            if not video_urls:
                self.log("❌ Aucune vidéo trouvée dans la playlist")
                return []
            self.log(f"✓ {len(video_urls)} vidéos trouvées dans la playlist")
            return video_urls
        except Exception as e:
            self.log(f"❌ Erreur lors de l'extraction des vidéos de la playlist: {str(e)}")
            return []

    def download_playlist(self, url):
        try:
            video_urls = self.get_playlist_videos_with_api(url)
            if not video_urls:
                self.log("❌ Aucune vidéo trouvée dans la playlist")
                return False
            self.log(f"Téléchargement de la playlist avec {len(video_urls)} vidéos")
            total_videos = len(video_urls)
            for i, video_url in enumerate(video_urls, 1):
                self.update_progress(i/total_videos, f"Téléchargement {i}/{total_videos}")
                self.download_video(video_url)
            self.update_progress(1, "Téléchargement terminé!")
            return True
        except Exception as e:
            self.log(f"❌ Erreur lors du téléchargement de la playlist: {str(e)}")
            self.log("Conseil: Vérifiez que l'URL de la playlist est correcte et accessible")
            return False

    def start_download(self):
        url = self.url.get().strip()
        if not url:
            messagebox.showerror("Erreur", "Veuillez entrer une URL YouTube")
            return
        if not re.match(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+", url):
            messagebox.showerror("Erreur", "Veuillez entrer une URL YouTube valide.")
            return
        if self.is_playlist.get():
            pass
        download_dir = self.download_path.get()
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir)
                self.log(f"Dossier créé : {download_dir}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de créer le dossier de téléchargement : {str(e)}")
                return
        self.download_button.configure(state="disabled")
        self.update_progress(0, "")
        def download_thread():
            try:
                if self.is_playlist.get():
                    self.download_playlist(url)
                else:
                    self.download_video(url)
            except Exception as e:
                self.log(f"❌ Erreur critique lors du téléchargement: {str(e)}")
                import traceback
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