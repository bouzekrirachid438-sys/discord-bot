import discord
from discord.ext import commands
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
    print(f'Bot ID: {bot.user.id}')
    print(f'Connected to {len(bot.guilds)} server(s)')
    for guild in bot.guilds:
        print(f'  - {guild.name} (ID: {guild.id})')
    print('=' * 50)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    print(f'Message received: "{message.content}" from {message.author.name} in {message.guild.name if message.guild else "DM"}')
    
    if message.content == '!test':
        await message.channel.send('✅ Bot is working!')
        print('Test command executed!')
    
    await bot.process_commands(message)

@bot.command(name='test')
async def test(ctx):
    await ctx.send('✅ Test command works!')
    print(f'Test command executed by {ctx.author.name}')

if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("Error: DISCORD_BOT_TOKEN not found!")
    else:
        print("Starting test bot...")
        bot.run(token)
