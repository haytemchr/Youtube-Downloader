# 🎵 YouTube Downloader

Un téléchargeur YouTube simple et sécurisé avec interface graphique, créé avec Python et CustomTkinter.

## ✨ Fonctionnalités

- 🎬 **Téléchargement de vidéos** en format MP4
- 🎵 **Téléchargement audio** en format MP3
- 📋 **Support des playlists** YouTube
- ⚙️ **Configuration facile** via interface graphique
- 📁 **Choix du dossier** de téléchargement

## 🚀 Installation

### Prérequis
- Python 3.7 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner le repository**
   ```bash
   git clone https://github.com/votre-username/youtube-downloader.git
   cd youtube-downloader
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Lancer l'application**
   ```bash
   python youtube_downloader.py
   ```

## 🔑 Configuration de la clé API YouTube

### Pourquoi une clé API ?
- **Vidéos uniques** : Pas besoin de clé API
- **Playlists** : Nécessite une clé API YouTube

### Comment obtenir une clé API ?

1. **Allez sur** [Google Cloud Console](https://console.cloud.google.com/)
2. **Créez un projet** ou sélectionnez-en un existant
3. **Activez l'API YouTube Data v3**
4. **Créez des identifiants** (clé API)
5. **Copiez la clé** et collez-la dans l'application

### Configuration dans l'application

1. **Lancez l'application** - L'écran de configuration s'affiche automatiquement
2. **Collez votre clé API** dans le champ prévu
3. **Cliquez sur "Sauvegarder"**
4. **Ou cliquez sur "Paramètres"** plus tard pour modifier

## 📖 Utilisation

### Télécharger une vidéo unique

1. **Collez l'URL YouTube** dans le champ
2. **Sélectionnez "Vidéo unique"**
3. **Choisissez le format** (MP4 ou MP3)
4. **Sélectionnez le dossier** de téléchargement
5. **Cliquez sur "Télécharger"**

### Télécharger une playlist

1. **Collez l'URL de la playlist** YouTube
2. **Sélectionnez "Playlist"**
3. **Assurez-vous d'avoir configuré** votre clé API
4. **Choisissez le format** et le dossier
5. **Cliquez sur "Télécharger"**

## 🛠️ Dépendances

- `customtkinter` - Interface graphique moderne
- `pytubefix` - Téléchargement YouTube
- `requests` - Requêtes HTTP
- `moviepy` - Conversion audio/vidéo
- `json` - Gestion de la configuration

## 🐛 Dépannage

### Erreur "Clé API introuvable"
- Configurez votre clé API via le bouton "Paramètres"
- Vérifiez que la clé est valide

### Erreur de téléchargement
- Vérifiez que l'URL YouTube est correcte
- Assurez-vous que la vidéo est publique
- Essayez une autre vidéo

### Problème de conversion MP3
- Vérifiez que `ffmpeg` est installé sur votre système

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👨‍💻 Auteur

**Haytem CHRYAT**

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Créer des pull requests

## ⚠️ Avertissement

Ce logiciel est destiné à un usage personnel et éducatif. Respectez les droits d'auteur et les conditions d'utilisation de YouTube. 