import discord
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('=' * 50)
    print(f'Bot logged in as: {bot.user}')
    print('=' * 50)
    print()
    print('To get emoji ID:')
    print('1. Type in Discord: \\:vp: (with backslash)')
    print('2. Copy the ID from <:vp:ID>')
    print('3. Use it in the code as: <:vp:ID>')
    print()

if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if token:
        bot.run(token)
