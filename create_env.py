import os

print("=" * 50)
print("  Karys Shop Bot - Token Setup")
print("=" * 50)
print()

token = input("Dkhel l-Token dyal Discord Bot dyalek: ").strip()

if not token:
    print("❌ Khassk tdkhel token!")
    exit(1)

# Create .env file
with open('.env', 'w') as f:
    f.write(f"DISCORD_BOT_TOKEN={token}\n")

print()
print("✅ Fichier .env tdir b success!")
print()
print("Daba khassk:")
print("1. Zid l-bot l server dyalek (shof SETUP_DARIJA.md)")
print("2. Dir: python bot.py")
print()
