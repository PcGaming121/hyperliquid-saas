#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'installation HyperLiquid SaaS
Installation automatique de la plateforme
"""

import os
import subprocess
import sys
from pathlib import Path

def print_step(step, description):
    print(f"\n🔄 Étape {step}: {description}")
    print("-" * 50)

def run_command(command, description):
    print(f"Exécution: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erreur: {e}")
        print(f"Output: {e.output}")
        return False

def create_directory_structure():
    """Crée la structure de dossiers nécessaire"""
    directories = [
        "templates",
        "static", 
        "user_bots",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Dossier créé: {directory}")

def create_requirements_file():
    """Crée le fichier requirements.txt"""
    requirements = """
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
jinja2==3.1.2
python-multipart==0.0.6
hyperliquid-python-sdk==0.1.9
python-telegram-bot==20.7
requests==2.31.0
psutil==5.9.6
    """.strip()
    
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements)
    print("✅ Fichier requirements.txt créé")

def create_env_file():
    """Crée un fichier .env d'exemple"""
    env_content = """
# Configuration HyperLiquid SaaS
DATABASE_URL=sqlite:///./hyperliquid_saas.db
ADMIN_PASSWORD=admin123
SECRET_KEY=your-secret-key-here
HOST=0.0.0.0
PORT=8000

# Pour production, changez ces valeurs !
    """.strip()
    
    with open(".env.example", "w", encoding="utf-8") as f:
        f.write(env_content)
    print("✅ Fichier .env.example créé")

def create_startup_script():
    """Crée un script de démarrage"""
    startup_content = '''#!/bin/bash
# Script de demarrage HyperLiquid SaaS

echo "Demarrage HyperLiquid SaaS..."

# Verification de l'environnement virtuel
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Attention: Aucun environnement virtuel detecte"
    echo "Recommandation: Utilisez 'python -m venv venv && source venv/bin/activate'"
fi

# Installation des dependances si necessaire
if [ ! -d "venv" ]; then
    echo "Creation de l'environnement virtuel..."
    python -m venv venv
fi

echo "Activation de l'environnement virtuel..."
source venv/bin/activate

echo "Installation des dependances..."
pip install -r requirements.txt

echo "Initialisation de la base de donnees..."
python -c "from main import Base, engine; Base.metadata.create_all(bind=engine); print('Base de donnees initialisee')"

echo "Lancement du serveur..."
python main.py
'''
    
    with open("start.sh", "w", encoding="utf-8") as f:
        f.write(startup_content)
    
    # Rendre le script exécutable
    os.chmod("start.sh", 0o755)
    print("✅ Script de démarrage créé: start.sh")

def create_docker_files():
    """Crée les fichiers Docker pour le déploiement"""
    dockerfile_content = """
FROM python:3.11-slim

WORKDIR /app

# Installation des dependances systeme
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Creation des dossiers necessaires
RUN mkdir -p user_bots logs static templates

# Port d'exposition
EXPOSE 8000

# Commande de demarrage
CMD ["python", "main.py"]
    """.strip()
    
    with open("Dockerfile", "w", encoding="utf-8") as f:
        f.write(dockerfile_content)
    
    docker_compose_content = """
version: '3.8'

services:
  hyperliquid-saas:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./user_bots:/app/user_bots
      - ./logs:/app/logs
      - ./hyperliquid_saas.db:/app/hyperliquid_saas.db
    environment:
      - DATABASE_URL=sqlite:///./hyperliquid_saas.db
      - ADMIN_PASSWORD=admin123
    restart: unless-stopped
    """.strip()
    
    with open("docker-compose.yml", "w", encoding="utf-8") as f:
        f.write(docker_compose_content)
    
    print("✅ Fichiers Docker créés (Dockerfile, docker-compose.yml)")

def create_readme():
    """Crée le fichier README avec les instructions"""
    readme_content = """
# HyperLiquid SaaS - Plateforme de Notifications Trading

## 🚀 Installation Rapide

### Option 1: Installation Locale

```bash
# 1. Cloner et entrer dans le dossier
cd hyperliquid-saas

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\\Scripts\\activate     # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer la plateforme
python main.py
```

### Option 2: Docker (Recommandé pour production)

```bash
# Lancement avec Docker Compose
docker-compose up -d
```

## 🌐 Accès

- **Interface Client**: http://localhost:8000
- **Panel Admin**: http://localhost:8000/admin
- **Mot de passe admin**: `admin123` (à changer !)

## 📊 Fonctionnalités

### Pour vos clients:
✅ **Inscription simple** avec configuration wallet + Telegram  
✅ **Bot personnel** généré automatiquement  
✅ **Notifications temps réel** de leurs trades  
✅ **Interface web** pour voir leurs statistiques  

### Pour vous (admin):
✅ **Activation manuelle** des comptes après paiement  
✅ **Dashboard** de gestion des utilisateurs  
✅ **Monitoring** de tous les bots clients  
✅ **Logs** détaillés de toutes les activités  

## 🔧 Configuration

### Changements Recommandés:

1. **Mot de passe admin** dans `main.py`:
   ```python
   ADMIN_PASSWORD = "votre_mot_de_passe_securise"
   ```

2. **Base de données** (pour plus d'utilisateurs):
   - Remplacer SQLite par PostgreSQL
   - Modifier `DATABASE_URL` dans la config

3. **Sécurité** (production):
   - Utiliser HTTPS avec SSL
   - Configurer un reverse proxy (Nginx)
   - Chiffrer les clés API des clients

## 📈 Workflow Client

1. **Inscription**: Client remplit le formulaire avec ses infos
2. **Paiement**: Vous gérez le paiement manuellement
3. **Activation**: Vous activez le compte via le panel admin
4. **Bot automatique**: Bot personnel lancé automatiquement
5. **Notifications**: Client reçoit ses trades en temps réel

## 🛠️ Maintenance

### Logs des bots clients:
```bash
ls user_bots/bot_*.log
```

### Arrêter un bot spécifique:
Via le panel admin ou manuellement avec le PID

### Backup base de données:
```bash
cp hyperliquid_saas.db backup_$(date +%Y%m%d).db
```

## 🚨 Sécurité

- Les clés API des clients sont stockées en base (chiffrement recommandé)
- Chaque client a son bot isolé
- Accès admin protégé par mot de passe
- Logs détaillés de toutes les activités

## 📞 Support

Pour vos clients, vous pouvez créer une page de documentation ou FAQ.

## 🔄 Mise à Jour

```bash
git pull origin main
pip install -r requirements.txt --upgrade
python main.py
```

---

**🎯 Votre SaaS est prêt !** Vos clients peuvent maintenant s'inscrire et vous gérez les activations.
    """.strip()
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ Documentation créée: README.md")

def main():
    """Installation principale"""
    print("🚀 Installation HyperLiquid SaaS")
    print("=" * 50)
    
    # Étape 1: Structure de dossiers
    print_step(1, "Création de la structure de dossiers")
    create_directory_structure()
    
    # Étape 2: Fichiers de configuration
    print_step(2, "Création des fichiers de configuration")
    create_requirements_file()
    create_env_file()
    create_startup_script()
    
    # Étape 3: Docker (optionnel)
    print_step(3, "Création des fichiers Docker")
    create_docker_files()
    
    # Étape 4: Documentation
    print_step(4, "Création de la documentation")
    create_readme()
    
    # Étape 5: Installation des dépendances
    print_step(5, "Installation des dépendances Python")
    install_deps = input("Installer les dépendances maintenant ? (y/n): ").lower().strip()
    
    if install_deps == 'y':
        if run_command("pip install -r requirements.txt", "Installation des dépendances"):
            print("✅ Installation terminée avec succès !")
        else:
            print("⚠️ Erreur lors de l'installation, installez manuellement:")
            print("pip install -r requirements.txt")
    
    # Instructions finales
    print("\n" + "=" * 60)
    print("🎉 INSTALLATION TERMINÉE !")
    print("=" * 60)
    print("\n📋 Prochaines étapes:")
    print("1. Modifiez le mot de passe admin dans main.py")
    print("2. Lancez la plateforme: python main.py")
    print("3. Accédez à: http://localhost:8000")
    print("4. Admin: http://localhost:8000/admin")
    print("\n💡 Consultez le README.md pour plus d'infos")
    print("\n🚀 Votre SaaS HyperLiquid est prêt !")

if __name__ == "__main__":
    main()