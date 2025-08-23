#!/bin/bash
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
