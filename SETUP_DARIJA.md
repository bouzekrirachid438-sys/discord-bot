# Kifach Tdir Setup dyal Karys Shop Bot

## L-Marra L-Oula: Installi Python Packages

1. Fti7 PowerShell aw Command Prompt
2. Dir:
```bash
pip install -r requirements.txt
```

## L-Marra Tania: Dir Bot f Discord

1. Mchi l: https://discord.com/developers/applications
2. Dkhel b account dyal Discord dyalek
3. Dgh "New Application" w smiha "Karys Shop"
4. Mchi l "Bot" (f l-left menu)
5. Dgh "Add Bot" w confirm
6. F "Token", dgh "Reset Token" w khod l-token (7fedah bzaf, ma t3tih l-wahd!)
7. F "Privileged Gateway Intents", 3tih:
   - ✅ Message Content Intent

## L-Marra Talta: Khod l-Token w 7to f .env

1. Dir fichier jdid smito `.env` f nfs l-folder dyal bot.py
2. Kteb fih:
```
DISCORD_BOT_TOKEN=token_dyalek_hna
```
3. Bdl `token_dyalek_hna` b l-token li khdti mn Discord Developer Portal

**Matalan:**
```
DISCORD_BOT_TOKEN=YOUR_TOKEN_HERE
```

## L-Marra Rabe3a: Zid l-Bot l Server dyalek

1. F Discord Developer Portal, mchi l "OAuth2" > "URL Generator"
2. F "Scopes", 3tih:
   - ✅ bot
   - ✅ applications.commands
3. F "Bot Permissions", 3tih:
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Read Message History
4. Khod l-URL li tban f l-bottom w fti7ha f browser
5. Khtar server dyalek w dgh "Authorize"

## L-Marra Khamesa: 7rek l-Bot

1. F PowerShell, mchi l folder dyal bot
2. Dir:
```bash
python bot.py
```

Ila kan kolchi mzayn, ghadi tshof:
```
Karys Shop#1234 has logged in!
```

## L-Commands li Kaynin:

- `!prices` - Tshof l-as3ar dyal Valorant Points
- `!stock` - Tshof stock (wajed aw ma-wajed)
- `!order 10000` - Tdir order (bdl 10000 b l-montant li bghiti)
- `!help_shop` - Tshof kolchi commands

## Ila Kan 3ndek Moshkil:

- Ila kan "DISCORD_BOT_TOKEN not found": Khassk tdir fichier `.env` w tkteb fih l-token
- Ila kan l-bot ma kaykhdem: Check wach 3titi Message Content Intent
- Ila kan l-bot ma kayjib: Check wach zidtih l server w 3titi permissions
