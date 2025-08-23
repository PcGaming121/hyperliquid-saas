FROM python:3.11-slim

WORKDIR /app

# Installation des dependances systeme
RUN apt-get update && apt-get install -y \
    gcc \
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