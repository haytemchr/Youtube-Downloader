import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from pytubefix import YouTube, Playlist
import os
import threading
import time
import queue
import re
import requests
import json
from moviepy.editor import AudioFileClip

class ConfigScreen:
    def __init__(self, parent):
        self.parent = parent
        self.api_key = tk.StringVar()
        self.config_file = "config.json"
        self.load_config()
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Configuration - YouTube Downloader")
        self.window.geometry("600x500")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.window.winfo_screenheight() // 2) - (500 // 2)
        self.window.geometry(f"600x500+{x}+{y}")
        self.create_widgets()
    def create_widgets(self):
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        title = ctk.CTkLabel(main_frame, text="Configuration", font=("Helvetica", 20, "bold"))
        title.pack(pady=20)
        desc = ctk.CTkLabel(main_frame, text="Pour télécharger des PLAYLISTS, vous devez fournir une clé API YouTube.", font=("Helvetica", 12), wraplength=400, text_color="red")
        desc.pack(pady=10)
        desc2 = ctk.CTkLabel(main_frame, text="En revanche, pour les VIDÉOS UNIQUES, vous n'en avez pas besoin.", font=("Helvetica", 12), wraplength=400, text_color="green")
        desc2.pack(pady=5)
        api_frame = ctk.CTkFrame(main_frame)
        api_frame.pack(fill=tk.X, padx=20, pady=20)
        api_label = ctk.CTkLabel(api_frame, text="Clé API YouTube :")
        api_label.pack(side=tk.LEFT, padx=5)
        api_entry = ctk.CTkEntry(api_frame, textvariable=self.api_key, width=300, show="*")
        api_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.show_key_var = tk.BooleanVar(value=False)
        show_key_btn = ctk.CTkCheckBox(api_frame, text="Afficher", variable=self.show_key_var, command=self.toggle_key_visibility)
        show_key_btn.pack(side=tk.RIGHT, padx=5)
        instructions = ctk.CTkLabel(main_frame, text="Instructions pour obtenir une clé API :\n1. Allez sur https://console.cloud.google.com/\n2. Créez un projet ou sélectionnez-en un existant\n3. Activez l'API YouTube Data v3\n4. Créez des identifiants (clé API)\n5. Copiez la clé et collez-la ci-dessus", font=("Helvetica", 17), justify=tk.LEFT, wraplength=500)
        instructions.pack(pady=10)
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        save_btn = ctk.CTkButton(button_frame, text="Sauvegarder", command=self.save_config, height=35, font=("Helvetica", 12, "bold"))
        save_btn.pack(side=tk.RIGHT, padx=5)
        skip_btn = ctk.CTkButton(button_frame, text="Passer", command=self.skip_config, height=35, font=("Helvetica", 12))
        skip_btn.pack(side=tk.RIGHT, padx=5)
    def toggle_key_visibility(self):
        for widget in self.window.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ctk.CTkEntry):
                                if self.show_key_var.get():
                                    grandchild.configure(show="")
                                else:
                                    grandchild.configure(show="*")
                                return
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.api_key.set(config.get('api_key', ''))
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
    def save_config(self):
        try:
            config = {
                'api_key': self.api_key.get().strip()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            messagebox.showinfo("Succès", "Configuration sauvegardée avec succès!")
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")
    def skip_config(self):
        self.window.destroy()
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
        self.load_api_key()
        self.message_queue = queue.Queue()
        self.format_var = tk.StringVar(value="mp4")
        self.quality_var = tk.StringVar(value="720p")
        self.available_qualities = []
        self.show_config_if_needed()
        self.create_widgets()
        self.window.after(100, self.process_messages)
    def load_api_key(self):
        try:
            config_file = "config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.api_key.set(config.get('api_key', ''))
        except Exception as e:
            print(f"Erreur lors du chargement de la clé API: {e}")
    def show_config_if_needed(self):
        if not self.api_key.get().strip():
            self.window.after(100, self.show_config_screen)
    def show_config_screen(self):
        config_screen = ConfigScreen(self.window)
        self.window.wait_window(config_screen.window)
        self.load_api_key()
    def show_settings(self):
        config_screen = ConfigScreen(self.window)
        self.window.wait_window(config_screen.window)
        self.load_api_key()
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
        self.quality_menu = ctk.CTkOptionMenu(self.quality_frame, variable=self.quality_var, values=["720p", "1080p", "480p", "360p"])
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
            self.quality_menu.configure(values=["Meilleure qualité"])
            self.quality_var.set("Meilleure qualité")
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
    def convert_to_mp3(self, video_path):
        try:
            self.log("Conversion en MP3 en cours...")
            audio_path = os.path.splitext(video_path)[0] + ".mp3"
            audio = AudioFileClip(video_path)
            audio.write_audiofile(audio_path, codec='mp3', bitrate='192k')
            audio.close()
            os.remove(video_path)
            self.log("Conversion en MP3 terminée!")
            return audio_path
        except Exception as e:
            self.log(f"❌ Erreur lors de la conversion en MP3: {str(e)}")
            try:
                self.log("Tentative de conversion alternative...")
                import subprocess
                audio_path = os.path.splitext(video_path)[0] + ".mp3"
                subprocess.run([
                    "ffmpeg", "-i", video_path, 
                    "-vn", "-ab", "192k", "-ar", "44100", "-y", audio_path
                ], check=True)
                os.remove(video_path)
                self.log("Conversion en MP3 terminée avec la méthode alternative!")
                return audio_path
            except Exception as e2:
                self.log(f"❌ Erreur lors de la conversion alternative: {str(e2)}")
                return video_path
    def download_video(self, url, max_retries=3):
        if not url.startswith(("https://www.youtube.com/", "https://youtu.be/")):
            self.log("❌ URL invalide. L'URL doit commencer par https://www.youtube.com/ ou https://youtu.be/")
            return False
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    time.sleep(2)
                yt = YouTube(url)
                self.log(f"Téléchargement de : {yt.title}")
                if self.format_var.get() == "mp4":
                    quality = self.quality_var.get()
                    video = yt.streams.filter(progressive=True, file_extension='mp4', resolution=quality).first()
                    if not video:
                        self.log(f"⚠️ La qualité {quality} n'est pas disponible. Téléchargement de la meilleure qualité disponible.")
                        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                    if not video:
                        video = yt.streams.get_highest_resolution()
                else:
                    video = yt.streams.filter(only_audio=True).first()
                if not video:
                    raise Exception("Aucun flux disponible")
                file_path = video.download(self.download_path.get())
                if self.format_var.get() == "mp3":
                    file_path = self.convert_to_mp3(file_path)
                self.log(f"✓ {yt.title} téléchargé avec succès!")
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    self.log(f"Tentative {attempt + 1} échouée, nouvelle tentative dans 2 secondes...")
                    self.log(f"Erreur : {str(e)}")
                else:
                    self.log(f"❌ Erreur lors du téléchargement de {url}: {str(e)}")
                    self.log("Conseils:")
                    self.log("1. Essayez de copier-coller l'URL directement depuis YouTube")
                    self.log("2. Vérifiez que la vidéo est publique et accessible")
                    self.log("3. Essayez une autre vidéo pour vérifier si le problème persiste")
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
            playlist_data = playlist_response.json()
            if 'items' not in playlist_data or not playlist_data['items']:
                self.log("❌ Playlist non trouvée ou inaccessible")
                return []
            playlist_title = playlist_data['items'][0]['snippet']['title']
            self.log(f"Playlist trouvée : {playlist_title}")
            video_urls = []
            next_page_token = None
            while True:
                if next_page_token:
                    playlist_items_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={playlist_id}&pageToken={next_page_token}&key={api_key}"
                else:
                    playlist_items_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={playlist_id}&key={api_key}"
                playlist_items_response = requests.get(playlist_items_url)
                playlist_items_data = playlist_items_response.json()
                if 'items' not in playlist_items_data:
                    self.log("❌ Erreur lors de la récupération des vidéos de la playlist")
                    break
                for item in playlist_items_data['items']:
                    video_id = item['snippet']['resourceId']['videoId']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    video_urls.append(video_url)
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
        try:
            response = requests.get(playlist_url)
            html = response.text
            playlist_id_match = re.search(r'list=([a-zA-Z0-9_-]+)', playlist_url)
            if not playlist_id_match:
                self.log("❌ URL de playlist invalide")
                return []
            playlist_id = playlist_id_match.group(1)
            video_pattern = f'list={playlist_id}.*?watch\\?v=([a-zA-Z0-9_-]+)'
            video_ids = re.findall(video_pattern, html)
            video_urls = []
            for video_id in video_ids:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                if video_url not in video_urls:
                    video_urls.append(video_url)
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
        if self.is_playlist.get():
            api_key = self.api_key.get().strip()
            if not api_key:
                messagebox.showerror("Erreur", "Clé API introuvable !\n\nPour télécharger des playlists, vous devez configurer une clé API YouTube.\n\nCliquez sur le bouton 'Paramètres' pour configurer votre clé API.")
                return
        self.download_button.configure(state="disabled")
        self.update_progress(0, "")
        def download_thread():
            try:
                if self.is_playlist.get():
                    self.download_playlist(url)
                else:
                    self.download_video(url)
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