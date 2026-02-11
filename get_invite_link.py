# -*- coding: utf-8 -*-
import sys
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

print("=" * 60)
print("  Karys Shop Bot - Discord Invite Link Generator")
print("=" * 60)
print()

print("1. Go to: https://discord.com/developers/applications")
print("2. Select 'Karys Shop' application")
print("3. Go to 'General Information'")
print("4. Copy 'Application ID' (Client ID)")
print()

client_id = input("Paste Client ID here: ").strip()

if not client_id:
    print("Error: Client ID is required!")
    exit(1)

# Generate invite link with required permissions
# Permissions: Send Messages (2048) + Embed Links (16384) + Read Message History (65536) = 83968
permissions = "83968"

invite_link = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&permissions={permissions}&scope=bot%20applications.commands"

print()
print("=" * 60)
print("  SUCCESS! Bot Invite Link:")
print("=" * 60)
print()
print(invite_link)
print()
print("=" * 60)
print("  Instructions:")
print("=" * 60)
print("1. Copy the link above")
print("2. Open it in your browser")
print("3. Select the server you want to add the bot to")
print("4. Click 'Authorize'")
print()
print("=" * 60)
