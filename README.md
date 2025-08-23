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
venv\Scripts\activate     # Windows

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