import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import json
import sys
import io

# Keep-alive for Replit (uncomment if hosting on Replit)
# from keep_alive import keep_alive

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Price list data
PRICE_LIST = {
    "5350": {"usd": 25, "dh": 249, "stock": False},
    "10000": {"usd": 55, "dh": 550, "stock": True},
    "12000": {"usd": 65, "dh": 650, "stock": True},
    "18000": {"usd": 85, "dh": 850, "stock": True},
    "25000": {"usd": 130, "dh": 1300, "stock": True},
    "50000": {"usd": 230, "dh": 2300, "stock": True},
    "100000": {"usd": 450, "dh": 4500, "stock": True}
}

@bot.event
async def on_ready():
    print('=' * 50)
    print(f'✅ {bot.user} has logged in!')
    print(f'✅ Bot ID: {bot.user.id}')
    print(f'✅ Connected to {len(bot.guilds)} server(s)')
    print('=' * 50)
    await bot.change_presence(activity=discord.Game(name="Karys Shop | !prices"))
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'❌ Error syncing commands: {e}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f'❌ Error: {error}')

@bot.event
async def on_error(event, *args, **kwargs):
    print(f'❌ Error in event {event}: {args}, {kwargs}')

@bot.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return
    
    # Debug: print ALL messages
    print(f'[MESSAGE] {message.author.name}: {message.content} (Guild: {message.guild.name if message.guild else "DM"})')
    
    # Process commands - IMPORTANT: must call this
    try:
        await bot.process_commands(message)
    except Exception as e:
        print(f'[ERROR] Error processing command: {e}')
        import traceback
        traceback.print_exc()

@bot.command(name='prices', aliases=['price', 'prix', 'اسعار', 'أسعار'])
async def prices(ctx):
    """عرض قائمة أسعار نقاط فالورانت"""
    print(f'[PRICES] Command executed by {ctx.author.name} in {ctx.guild.name if ctx.guild else "DM"}')
    
    try:
        # Create embed
        embed = discord.Embed(
            title="🔴 قائمة أسعار نقاط فالورانت (أسعار إقليمية) 🔴",
            color=0xFF0000  # Red color
        )
        
        # Add platform availability
        embed.add_field(
            name="📱 متوفر على:",
            value="<:playstation:> PlayStation 5 | <:xbox:> Xbox | <:pc:> PC",
            inline=False
        )
        
        # Add prices
        price_text = ""
        for points, info in PRICE_LIST.items():
            status = "❌ غير متوفر" if not info["stock"] else "✅"
            points_int = int(points)
            price_text += f"{status} **{points_int:,} نقطة** → {info['usd']} $ | {info['dh']} درهم\n"
        
        embed.add_field(
            name="💰 الأسعار:",
            value=price_text,
            inline=False
        )
        
        # Add delivery info
        embed.add_field(
            name="⚡ وقت التوصيل:",
            value="من 1 إلى 5 دقائق بعد تأكيد الدفع",
            inline=False
        )
        
        # Add payment methods
        embed.add_field(
            name="💵 طرق الدفع:",
            value="تحويل بنكي / Remitly / Binance (BTC | USDT) / Cashplus",
            inline=False
        )
        
        # Add order instructions
        embed.add_field(
            name="➡️ كيفية الطلب:",
            value="أرسل إثبات الدفع في غرفة الدفع أو راسل أحد المشرفين",
            inline=False
        )
        
        # Set footer
        embed.set_footer(text="Karys Shop | متجرك الموثوق لنقاط فالورانت")
        embed.set_thumbnail(url="https://i.imgur.com/valorant-logo.png")  # You can add your logo URL here
        
        await ctx.send(embed=embed)
        print(f'[PRICES] Embed sent successfully')
    except Exception as e:
        print(f'[ERROR] Error in prices command: {e}')
        import traceback
        traceback.print_exc()
        await ctx.send(f'❌ Error: {str(e)}')

@bot.command(name='stock', aliases=['inventory', 'المخزون', 'مخزون'])
async def stock(ctx):
    """التحقق من توفر المخزون"""
    
    embed = discord.Embed(
        title="📦 حالة المخزون",
        color=0x00FF00
    )
    
    in_stock = []
    out_of_stock = []
    
    for points, info in PRICE_LIST.items():
        points_int = int(points)
        if info["stock"]:
            in_stock.append(f"{points_int:,} نقطة")
        else:
            out_of_stock.append(f"{points_int:,} نقطة")
    
    if in_stock:
        embed.add_field(
            name="✅ متوفر:",
            value="\n".join(in_stock),
            inline=True
        )
    
    if out_of_stock:
        embed.add_field(
            name="❌ غير متوفر:",
            value="\n".join(out_of_stock),
            inline=True
        )
    
    await ctx.send(embed=embed)

@bot.command(name='order')
async def order(ctx, points: str = None):
    """Order Valorant Points"""
    if not points:
        await ctx.send("❌ Please specify the amount of Valorant Points you want to order.\nExample: `!order 10000`")
        return
    
    # Remove commas if user added them
    points = points.replace(",", "")
    
    if points not in PRICE_LIST:
        await ctx.send(f"❌ Invalid amount. Use `!prices` to see available options.")
        return
    
    info = PRICE_LIST[points]
    
    if not info["stock"]:
        points_int = int(points)
        await ctx.send(f"❌ {points_int:,} VP is currently out of stock.")
        return
    
    embed = discord.Embed(
        title="🛒 Order Confirmation",
        color=0x00FF00
    )
    
    points_int = int(points)
    embed.add_field(
        name="Amount:",
        value=f"{points_int:,} Valorant Points",
        inline=False
    )
    
    embed.add_field(
        name="Price:",
        value=f"{info['usd']} $ | {info['dh']} dh",
        inline=False
    )
    
    embed.add_field(
        name="Next Steps:",
        value="1. Make payment using one of the accepted methods\n2. Send payment proof in the payment room or DM an admin\n3. Receive your VP within 1-5 minutes",
        inline=False
    )
    
    embed.add_field(
        name="Payment Methods:",
        value="Bank transfer / Remitly / Binance (BTC | USDT) / Cashplus",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='help_shop', aliases=['shop_help', 'مساعدة'])
async def help_shop(ctx):
    """Show available commands"""
    embed = discord.Embed(
        title="🛍️ Karys Shop - Commands",
        color=0xFF0000
    )
    
    embed.add_field(
        name="!prices",
        value="View Valorant Points price list",
        inline=False
    )
    
    embed.add_field(
        name="!stock",
        value="Check stock availability",
        inline=False
    )
    
    embed.add_field(
        name="!order [amount]",
        value="Order Valorant Points (e.g., !order 10000)",
        inline=False
    )
    
    embed.add_field(
        name="!help_shop",
        value="Show this help message",
        inline=False
    )
    
    embed.set_footer(text="Karys Shop | Your trusted Valorant Points provider")
    
    await ctx.send(embed=embed)

def create_price_post():
    """Create price list post matching exact format"""
    # Create embed with exact format
    embed = discord.Embed(
        title="🔻 Valorant Points Price List 🔻",
        color=0xFF0000  # Red color
    )
    
    # Add platform availability
    embed.add_field(
        name="🎮 Available on:",
        value="PlayStation 5 | Xbox | PC",
        inline=False
    )
    
    # Add prices - matching exact format
    price_text = ""
    for points, info in PRICE_LIST.items():
        points_int = int(points)
        # Use :vp: custom emoji with ID
        price_text += f"{points_int:,} <:vp:1466944483504427008> → {info['usd']} $ │ {info['dh']} dh\n"
    
    embed.add_field(
        name="💰 Prices",
        value=price_text,
        inline=False
    )
    
    # Add delivery info
    embed.add_field(
        name="🚚 Delivery:",
        value="⏱️ 1–5 minutes after payment confirmation",
        inline=False
    )
    
    # Add payment methods
    embed.add_field(
        name="💳 Payment Methods:",
        value="• 🏦 Bank transfer: CIH Bank | BMCE Bank | Attijariwafa Bank\n• ⚡ Instant bank transfer\n• 🪙 Binance (USDT)\n• 💲 PayPal",
        inline=False
    )
    
    # Add order instructions
    embed.add_field(
        name="📩 Order:",
        value="Send payment proof in the payment <#1466942654800597085> .",
        inline=False
    )
    
    # Set footer
    embed.set_footer(text="Karys Shop | Your trusted Valorant Points provider")
    embed.set_thumbnail(url="https://i.imgur.com/valorant-logo.png")
    
    return embed

@bot.tree.command(name="post", description="إنشاء منشور قائمة الأسعار")
async def post(interaction: discord.Interaction):
    """Slash command to post price list"""
    embed = create_price_post()
    await interaction.response.send_message(embed=embed)

@bot.command(name='post', aliases=['منشور'])
async def post_command(ctx):
    """Create price list post"""
    embed = create_price_post()
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Please create a .env file with your bot token.")
    else:
        bot.run(token)
