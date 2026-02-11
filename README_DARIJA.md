# Karys Shop Discord Bot - Guide Kamil

## 🚀 Bach Tdir Setup B Click Wahd:

### Option 1: Full Setup (Kolchi Automatic)
Dgh double-click 3la `full_setup.bat` w tbi3 l-instructions.

### Option 2: Manual Setup
1. Dgh `full_setup.bat` bach tinstalli packages
2. Dgh `create_env.py` bach tdir fichier .env w tkteb token
3. Dgh `start_bot.bat` bach t7rek l-bot

## 📋 L-Steps Dyal Setup:

### 1️⃣ Dir Bot f Discord Developer Portal

**Khassk tdir hadchi bach tkhdem:**
- Mchi l: https://discord.com/developers/applications
- Dgh "New Application" → smiha "Karys Shop"
- Mchi l "Bot" → "Add Bot" → "Yes, do it!"
- F "Token", dgh "Reset Token" w khod l-token (7fedah!)
- F "Privileged Gateway Intents", 3ti:
  - ✅ **Message Content Intent** (mohim bzaf!)

### 2️⃣ Zid l-Bot l Server dyalek

- F Developer Portal → "OAuth2" → "URL Generator"
- F "Scopes", 3ti:
  - ✅ `bot`
  - ✅ `applications.commands`
- F "Bot Permissions", 3ti:
  - ✅ Send Messages
  - ✅ Embed Links
  - ✅ Read Message History
- Khod l-URL w fti7ha f browser
- Khtar server dyalek w dgh "Authorize"

### 3️⃣ Khod l-Token w 7to f .env

**Option A: B Python Script**
```bash
python create_env.py
```
W dkhel l-token.

**Option B: Manual**
- Dir fichier jdid smito `.env`
- Kteb fih:
```
DISCORD_BOT_TOKEN=token_dyalek_hna
```

### 4️⃣ 7rek l-Bot

**Option A: B Batch File**
Dgh `start_bot.bat`

**Option B: B Command**
```bash
python bot.py
```

Ila kan kolchi mzayn, ghadi tshof:
```
==================================================
✅ Karys Shop#1234 has logged in!
✅ Bot ID: 1234567890
✅ Connected to 1 server(s)
==================================================
```

## 🎮 L-Commands:

- `!prices` - Tshof l-as3ar dyal Valorant Points
- `!stock` - Tshof stock (wajed aw ma-wajed)
- `!order 10000` - Tdir order (bdl 10000 b l-montant li bghiti)
- `!help_shop` - Tshof kolchi commands

## ❌ Ila Kan 3ndek Moshkil:

**"DISCORD_BOT_TOKEN not found"**
→ Khassk tdir fichier `.env` w tkteb fih l-token

**"Bot ma kaykhdem"**
→ Check wach 3titi "Message Content Intent" f Developer Portal

**"Bot ma kayjib"**
→ Check wach zidtih l server w 3titi permissions

**"Python ma kaynch"**
→ Installi Python mn: https://www.python.org/downloads/

## 📁 L-Files Dyal Project:

- `bot.py` - L-code dyal bot
- `requirements.txt` - L-packages dyal Python
- `config.json` - L-settings dyal shop
- `create_env.py` - Script bach tdir .env
- `start_bot.bat` - Script bach t7rek l-bot
- `full_setup.bat` - Script bach tdir full setup
- `SETUP_DARIJA.md` - Guide tafsil b Darija

## 💡 Tips:

- 7fed l-token dyal bot bzaf! Ma t3tih l-wahd!
- Ila bghiti tbdl l-as3ar, 7awel f `bot.py` f `PRICE_LIST`
- L-bot kaykhdem 24/7 ila kan l-computer dyalek kaykhdem
