# main.py - Backend FastAPI
from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import hashlib
import secrets
import os
import subprocess
import json

# Configuration
DATABASE_URL = "sqlite:///./hyperliquid_saas.db"
ADMIN_PASSWORD = "admin123"  # Changez ceci !

# Base de données
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    wallet_address = Column(String)
    api_private_key = Column(String)
    telegram_token = Column(String)
    telegram_chat_id = Column(String)
    is_active = Column(Boolean, default=False)
    signum_connected = Column(Boolean, default=False)  # ← NOUVELLE LIGNE
    created_at = Column(DateTime, default=datetime.utcnow)
    bot_process_id = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

# Models Pydantic
class UserCreate(BaseModel):
    email: str
    name: str
    wallet_address: str
    api_private_key: str
    telegram_token: str
    telegram_chat_id: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    wallet_address: str
    is_active: bool
    created_at: datetime

# FastAPI App
app = FastAPI(title="HyperLiquid SaaS", description="Plateforme de notifications trading")

# Static files et templates
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Dependency pour DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_user(
    email: str = Form(...),
    name: str = Form(...),
    wallet_address: str = Form(...),
    api_private_key: str = Form(...),
    telegram_token: str = Form(...),
    telegram_chat_id: str = Form(...),
    db: Session = Depends(get_db)
):
    # Vérifier si l'utilisateur existe déjà
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Cet email est déjà enregistré")
    
    # Créer le nouvel utilisateur
    db_user = User(
        email=email,
        name=name,
        wallet_address=wallet_address,
        api_private_key=api_private_key,
        telegram_token=telegram_token,
        telegram_chat_id=telegram_chat_id
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return RedirectResponse(url="/success", status_code=303)

@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin/login")
async def admin_login(password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    
    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    response.set_cookie(key="admin_session", value="authenticated", httponly=True)
    return response

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    # Vérifier session admin (simplifié)
    if not request.cookies.get("admin_session"):
        return RedirectResponse(url="/admin")
    
    users = db.query(User).all()
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request, 
        "users": users
    })

@app.post("/admin/activate/{user_id}")
async def activate_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if not user.is_active:
        # Activer l'utilisateur
        user.is_active = True
        
        # Générer et lancer le bot
        bot_process = create_user_bot(user)
        if bot_process:
            user.bot_process_id = str(bot_process.pid)
        
        db.commit()
        
        # Notifier l'utilisateur
        send_activation_notification(user)
    
    return {"message": "Utilisateur activé et bot lancé"}

@app.post("/admin/deactivate/{user_id}")
async def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if user.is_active:
        # Désactiver l'utilisateur
        user.is_active = False
        
        # Arrêter le bot
        if user.bot_process_id:
            stop_user_bot(user.bot_process_id)
            user.bot_process_id = None
        
        db.commit()
    
    return {"message": "Utilisateur désactivé et bot arrêté"}

def create_user_bot(user: User):
    """Crée et lance un bot pour l'utilisateur"""
    try:
        # Créer le fichier de configuration du bot
        bot_config = {
            'TELEGRAM_TOKEN': user.telegram_token,
            'CHAT_ID': user.telegram_chat_id,
            'WALLET_ADDRESS': user.wallet_address,
            'API_PRIVATE_KEY': user.api_private_key,
            'CHECK_INTERVAL': 30,
            'DAILY_REPORT_TIME': '23:59',
        }
        
        # Créer le dossier pour les bots utilisateurs
        os.makedirs("user_bots", exist_ok=True)
        
        # Sauvegarder la configuration
        config_path = f"user_bots/config_{user.id}.json"
        with open(config_path, 'w') as f:
            json.dump(bot_config, f)
        
        # Créer le script du bot personnalisé
        bot_script_path = f"user_bots/bot_{user.id}.py"
        create_user_bot_script(bot_script_path, config_path, user.id)
        
        # Lancer le bot
        process = subprocess.Popen([
            "python", bot_script_path
        ], cwd=os.getcwd())
        
        print(f"Bot lancé pour {user.email} - PID: {process.pid}")
        return process
        
    except Exception as e:
        print(f"Erreur création bot pour {user.email}: {e}")
        return None

def create_user_bot_script(script_path: str, config_path: str, user_id: int):
    """Crée le script du bot personnalisé pour l'utilisateur"""
    
    bot_script_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot HyperLiquid personnalisé - Utilisateur {user_id}
Généré automatiquement par la plateforme SaaS
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List

import requests
from hyperliquid.info import Info
from hyperliquid.utils import constants
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Chargement de la configuration
with open(r"{config_path}", 'r') as f:
    CONFIG = json.load(f)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'user_bots/bot_{user_id}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HyperLiquidBot:
    def __init__(self):
        self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
        self.last_known_trades = set()
        self.daily_stats = self.init_daily_stats()
        self.bot_start_time = datetime.now()
        
    def init_daily_stats(self) -> Dict:
        return {{
            'trades_count': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'total_volume': 0.0,
            'start_balance': 0.0,
            'date': datetime.now().strftime('%Y-%m-%d')
        }}

    def get_user_state(self) -> Dict:
        """Récupère l'état du compte utilisateur"""
        try:
            user_state = self.info.user_state(CONFIG['WALLET_ADDRESS'])
            return user_state
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'état utilisateur: {{e}}")
            return {{}}

    def get_user_fills(self) -> List[Dict]:
        """Récupère l'historique des trades"""
        try:
            fills = self.info.user_fills(CONFIG['WALLET_ADDRESS'])
            return fills if fills else []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des trades: {{e}}")
            return []

    def format_trade_notification(self, trade: Dict) -> str:
        """Formate une notification de trade"""
        try:
            side = "🟢 ACHAT" if trade.get('side') == 'B' else "🔴 VENTE"
            coin = trade.get('coin', 'Unknown')
            size = float(trade.get('sz', 0))
            price = float(trade.get('px', 0))
            total_value = size * price
            fee = float(trade.get('fee', 0))
            timestamp = datetime.fromtimestamp(int(trade.get('time', 0)) / 1000)
            
            pnl_text = ""
            if 'closedPnl' in trade:
                pnl = float(trade['closedPnl'])
                pnl_emoji = "💰" if pnl > 0 else "💸" if pnl < 0 else "⚖️"
                pnl_text = f"\\n{{pnl_emoji}} P&L: {{pnl:+.2f}} USDC"
            
            message = f"""
🎯 <b>NOUVEAU TRADE DÉTECTÉ</b>

{{side}} <b>{{coin}}</b>
📊 Quantité: {{size:.4f}}
💵 Prix: ${{price:.4f}}
💰 Valeur: ${{total_value:.2f}}
⚡ Frais: ${{fee:.4f}}
🕐 Heure: {{timestamp.strftime('%H:%M:%S')}}{{pnl_text}}

📈 Consultez vos stats avec /status
            """.strip()
            
            return message
        except Exception as e:
            logger.error(f"Erreur formatage trade: {{e}}")
            return f"🚨 Trade détecté (erreur de formatage): {{str(trade)[:100]}}..."

    def check_new_trades(self):
        """Vérifie s'il y a de nouveaux trades"""
        try:
            current_trades = self.get_user_fills()
            
            current_trade_ids = set()
            for trade in current_trades[:10]:
                trade_id = f"{{trade.get('oid', '')}}-{{trade.get('time', '')}}"
                current_trade_ids.add(trade_id)
                
                if trade_id not in self.last_known_trades:
                    logger.info(f"Nouveau trade détecté: {{trade_id}}")
                    message = self.format_trade_notification(trade)
                    self.send_telegram_message(message)
                    
            self.last_known_trades = current_trade_ids
            
        except Exception as e:
            logger.error(f"Erreur vérification trades: {{e}}")

    def send_telegram_message(self, message: str, parse_mode: str = 'HTML'):
        """Envoie un message via Telegram"""
        try:
            url = f"https://api.telegram.org/bot{{CONFIG['TELEGRAM_TOKEN']}}/sendMessage"
            payload = {{
                'chat_id': CONFIG['CHAT_ID'],
                'text': message,
                'parse_mode': parse_mode
            }}
            
            response = requests.post(url, json=payload)
            if response.status_code != 200:
                logger.error(f"Erreur Telegram: {{response.text}}")
                
        except Exception as e:
            logger.error(f"Erreur envoi message: {{e}}")

class TelegramBotHandlers:
    def __init__(self, hyperliquid_bot: HyperLiquidBot):
        self.hl_bot = hyperliquid_bot

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /start"""
        welcome_msg = """
🤖 <b>Votre Bot HyperLiquid Personnel</b>

Bienvenue ! Je surveille vos trades en temps réel.

🔄 Vérification: toutes les 30s
📊 Rapport quotidien: 23h59
🚨 Notifications instantanées

Tapez /status pour voir votre portfolio !
        """.strip()
        
        await update.message.reply_text(welcome_msg, parse_mode='HTML')

async def run_scheduled_jobs(hl_bot):
    """Exécute les tâches programmées"""
    last_check = 0
    
    while True:
        try:
            current_time = time.time()
            
            if current_time - last_check >= CONFIG['CHECK_INTERVAL']:
                hl_bot.check_new_trades()
                last_check = current_time
            
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Erreur dans les tâches: {{e}}")
            await asyncio.sleep(5)

async def main():
    """Fonction principale"""
    hl_bot = HyperLiquidBot()
    handlers = TelegramBotHandlers(hl_bot)
    
    app = Application.builder().token(CONFIG['TELEGRAM_TOKEN']).build()
    app.add_handler(CommandHandler("start", handlers.start))
    
    startup_msg = f"""
🚀 <b>VOTRE BOT EST ACTIF !</b>

✅ Surveillance de votre wallet
📱 Notifications configurées
🎯 Prêt à tracker vos trades !

Tapez /start pour commencer.
    """.strip()
    
    hl_bot.send_telegram_message(startup_msg)
    logger.info(f"Bot utilisateur {{user_id}} démarré")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    scheduled_task = asyncio.create_task(run_scheduled_jobs(hl_bot))
    
    try:
        logger.info("Bot en cours d'exécution...")
        await scheduled_task
    except KeyboardInterrupt:
        logger.info("Arrêt du bot")
    finally:
        scheduled_task.cancel()
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(bot_script_content)

def stop_user_bot(process_id: str):
    """Arrête le bot de l'utilisateur"""
    try:
        import psutil
        process = psutil.Process(int(process_id))
        process.terminate()
        print(f"Bot arrêté - PID: {process_id}")
    except Exception as e:
        print(f"Erreur arrêt bot PID {process_id}: {e}")

def send_activation_notification(user: User):
    """Envoie une notification d'activation à l'utilisateur"""
    try:
        url = f"https://api.telegram.org/bot{user.telegram_token}/sendMessage"
        message = f"""
🎉 <b>FÉLICITATIONS !</b>

Votre compte HyperLiquid SaaS a été <b>activé</b> !

✅ Bot de notifications: <b>ACTIF</b>
📊 Surveillance de votre wallet: <b>EN COURS</b>
🚨 Notifications temps réel: <b>CONFIGURÉES</b>

Tapez /start à ce bot pour commencer !

Bon trading ! 🚀
        """.strip()
        
        payload = {
            'chat_id': user.telegram_chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        requests.post(url, json=payload)
        
    except Exception as e:
        print(f"Erreur notification activation: {e}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Lancement de la plateforme HyperLiquid SaaS...")
    print("📱 Interface: http://localhost:8000")
    print("👨‍💼 Admin: http://localhost:8000/admin")

    uvicorn.run(app, host="0.0.0.0", port=8000)

