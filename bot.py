import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import json
import random
from typing import Literal

# Load environment variables
load_dotenv()

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Price list data
PRICE_LIST = {
    "1000": {"usd": 5.0, "dh": 50, "stock": False},
    "5000": {"usd": 25.0, "dh": 250, "stock": False},
    "10000": {"usd": 50.0, "dh": 500, "stock": True},
    "12000": {"usd": 55.0, "dh": 550, "stock": True},
    "13000": {"usd": 60.0, "dh": 600, "stock": True},
    "14000": {"usd": 65.0, "dh": 650, "stock": True},
    "16000": {"usd": 75.0, "dh": 750, "stock": True},
    "18000": {"usd": 85.0, "dh": 850, "stock": True},
    "20000": {"usd": 100.0, "dh": 1000, "stock": True},
    "100000": {"usd": 450.0, "dh": 4500, "stock": True}
}

VBUCKS_PRICES = {
    "10000": "400",
    "12000": "480",
    "15000": "600",
    "25000": "1000",
    "50000": "1800"
}

# --- Data Management ---
def load_data(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# Load data on startup
invites_data = load_data('invites.json') # Structure: {"user_id": {"regular": 0, "fake": 0, "bonus": 0, "leaves": 0}}
giveaways_data = load_data('giveaways.json')
invite_cache = {} # Cache for tracking invite uses

def get_invites(user_id):
    user_id = str(user_id)
    if user_id not in invites_data:
        invites_data[user_id] = {"regular": 0, "fake": 0, "bonus": 0, "leaves": 0}
    
    data = invites_data[user_id]
    total = (data["regular"] + data["bonus"]) - (data["leaves"] + data["fake"])
    return total if total > 0 else 0

# --- Giveaway System ---
class GiveawayJoinButton(discord.ui.View):
    def __init__(self, message_id, required_invites):
        super().__init__(timeout=None)
        self.message_id = str(message_id)
        self.required_invites = required_invites

    @discord.ui.button(label="🎉 Join Giveaway", style=discord.ButtonStyle.green, custom_id="join_giveaway_btn")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Determine giveaway ID from message
        giveaway_id = str(interaction.message.id)
        
        # Check if giveaway exists
        if giveaway_id not in giveaways_data:
            await interaction.response.send_message("❌ This giveaway has ended or does not exist.", ephemeral=True)
            return

        giveaway = giveaways_data[giveaway_id]
        
        if giveaway["ended"]:
            await interaction.response.send_message("❌ This giveaway has already ended.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        
        # Check if already joined
        if user_id in giveaway["participants"]:
            await interaction.response.send_message("⚠️ You have already joined this giveaway!", ephemeral=True)
            return

        # Check invites
        user_invites = get_invites(user_id)
        if user_invites < self.required_invites:
            await interaction.response.send_message(f"❌ You need **{self.required_invites}** invites to join. You currently have **{user_invites}**.", ephemeral=True)
            return

        # Add to participants
        giveaway["participants"].append(user_id)
        save_data('giveaways.json', giveaways_data)
        
        # Update Embed count
        embed = interaction.message.embeds[0]
        field_index = -1
        for i, field in enumerate(embed.fields):
            if "Entries" in field.name:
                field_index = i
                break
        
        if field_index != -1:
            embed.set_field_at(field_index, name="👥 Entries", value=str(len(giveaway["participants"])), inline=True)
            await interaction.message.edit(embed=embed)

        await interaction.response.send_message(f"✅ You successfully joined the giveaway! (Invites: {user_invites})", ephemeral=True)

class TicketButton(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__()
        # Link to the specific channel
        url = f"https://discord.com/channels/{guild_id}/1466942654800597085"
        self.add_item(discord.ui.Button(label="Open a Ticket", style=discord.ButtonStyle.link, url=url, emoji="🎟️"))

class TicketAdminView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="� Reopen Ticket", style=discord.ButtonStyle.green, custom_id="reopen_ticket_btn")
    async def reopen_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # Get Tickets Category
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category("Tickets")
            
        await interaction.channel.edit(category=category)
        
        # Restore user permissions
        # We need to find the user from the channel name or topic, but easier:
        # Just restore permissions for the specific user found in overwrites
        for target, overwrite in interaction.channel.overwrites.items():
            if isinstance(target, discord.Member) and target != guild.me:
                # Use view_channel for d.py 2.0+
                await interaction.channel.set_permissions(target, view_channel=True, send_messages=True, read_message_history=True)
                
                # Try to rename, but don't fail if rate limited
                try:
                    await interaction.channel.edit(name=f"ticket-{target.name}")
                except Exception as e:
                    print(f"[WARNING] Could not rename channel on reopen: {e}")
                    
                await interaction.channel.send(f"🔓 Ticket reopened! Welcome back {target.mention}")
                return
        
        await interaction.followup.send("✅ Ticket reopened (User not found in overwrites)", ephemeral=True)

    @discord.ui.button(label="⛔ Delete Ticket", style=discord.ButtonStyle.red, custom_id="delete_ticket_btn")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⛔ Deleting ticket in 5 seconds...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="📝 Force Rename", style=discord.ButtonStyle.secondary, custom_id="force_rename_btn", emoji="📝")
    async def force_rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Admin tool to retry renaming if rate limited
        try:
             # Sanitize owner name query
             new_name = f"closedorder-{interaction.channel.name.split('-')[-1]}"
             # Try to find original owner from embed if possible, but channel name suffix is safest fallback
             
             await interaction.response.defer()
             await interaction.channel.edit(name=new_name)
             await interaction.followup.send(f"✅ Renamed to {new_name}", ephemeral=True)
        except Exception as e:
             await interaction.followup.send(f"❌ Failed to rename: {e}\n(Discord limits renames to 2 per 10 mins. Try again later.)", ephemeral=True)

class TicketCloseConfirmationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, custom_id="confirm_close_btn", emoji="🔒")
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⛔ Closing ticket in 5 seconds...", ephemeral=False)
        await asyncio.sleep(5)
        
        channel = interaction.channel
        guild = interaction.guild
        
        # 0. Extract Info (Owner & Order) before closing
        ticket_owner = "Unknown"
        order_info = "General Support / No Order Found"
        
        # Try to find owner from channel name or permissions
        # Best guess: Find the user who has view permissions and isn't a bot/admin
        # OR scan chat for the welcome message mention
        
        # Scan chat for Order Embed to get valid info
        try:
            async for msg in channel.history(limit=50, oldest_first=True):
                # Check for Welcome Mention for owner
                if not ticket_owner or ticket_owner == "Unknown":
                    if msg.mentions and not msg.author.bot:
                         # First human mention might be owner? No, bot mentions user in welcome.
                         pass
                
                # Check for Bot's Embeds
                if msg.author.id == interaction.client.user.id and msg.embeds:
                    embed = msg.embeds[0]
                    # Check for Order
                    if "Order" in (embed.title or ""):
                        for field in embed.fields:
                            if field.name in ["🛒 Item", "📦 Service"]:
                                order_info = field.value
                        # Also get author if available
                        if embed.author:
                            ticket_owner = embed.author.name
                    
                    # Check for Welcome to grab owner if not found yet
                    if "Welcome" in (embed.title or "") and "Ticket" not in (embed.title or ""):
                         # "👋 Welcome username!"
                         if "Welcome" in embed.title:
                             ticket_owner = embed.title.replace("👋 Welcome ", "").replace("!", "")

        except:
             pass

        try:
            try:
                await interaction.message.delete()
            except:
                pass
            
            # Get Logs Category
            category = discord.utils.get(guild.categories, name="Ticket Logs") or discord.utils.get(guild.categories, name="Logs")
            if not category:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False)
                }
                category = await guild.create_category("Ticket Logs", overwrites=overwrites)
            
            # Step 1: Move category (Critical)
            await channel.edit(category=category)
            
            # Step 2: Remove permissions (Security)
            for target, overwrite in channel.overwrites.items():
                if isinstance(target, discord.Member) and target != guild.me:
                    await channel.set_permissions(target, view_channel=False, send_messages=False, read_message_history=False)

            # Step 3: Send Enhanced Embed (Controls + Info)
            embed = discord.Embed(
                title="🔒 **Ticket Closed**",
                color=0xFF0000,
                timestamp=datetime.now()
            )
            embed.add_field(name="👤 Ticket Owner", value=f"**{ticket_owner}**", inline=True)
            embed.add_field(name="🛡️ Closed By", value=interaction.user.mention, inline=True)
            embed.add_field(name="📝 Order Info", value=order_info, inline=False)
            embed.set_footer(text="Manage this ticket below ⬇️")
            
            await channel.send(embed=embed, view=TicketAdminView())
            
            # Step 4: Rename Channel (Cosmetic - Low Priority)
            # We put this last so if it fails (rate limit), the ticket is still closed and usable by admins
            try:
                # Sanitize owner name (remove spaces/special chars)
                safe_owner = "unknown"
                if ticket_owner and ticket_owner != "Unknown":
                    safe_owner = "".join(c for c in ticket_owner if c.isalnum()).lower()
                else:
                    # Fallback to channel name suffix
                    safe_owner = channel.name.split('-')[-1]
                
                # "closedorder" stuck together as requested
                new_name = f"closedorder-{safe_owner}"
                await channel.edit(name=new_name[:100])
            except Exception as e:
                print(f"[WARNING] Rename failed (Rate Limit?): {e}")
            
        except Exception as e:
            print(f"[ERROR] processing ticket close: {e}")
            import traceback
            traceback.print_exc()
            try:
                await interaction.followup.send(f"❌ Error closing ticket: {e}", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray, custom_id="cancel_close_btn")
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            await interaction.message.delete()
        except:
            pass

class OrderModal(discord.ui.Modal):
    def __init__(self, service_name, title="Order Details"):
        super().__init__(title=title)
        self.service_name = service_name
        
        self.quantity = discord.ui.TextInput(
            label="Quantity / Amount",
            placeholder="Ex: 1000 VP, 1 Year Nitro, etc...",
            required=True,
            style=discord.TextStyle.short
        )
        self.notes = discord.ui.TextInput(
            label="Additional Notes / Payment Method",
            placeholder="Ex: Paying with CIH, I need fast delivery...",
            required=False,
            style=discord.TextStyle.long
        )
        self.add_item(self.quantity)
        self.add_item(self.notes)

    async def on_submit(self, interaction: discord.Interaction):
        # Update the ticket name to reflect the order (optional)
        try:
            # Normalize service name for channel name
            safe_service = self.service_name.lower().replace(' ', '-').replace('/', '-').replace('v-bucks', 'vbucks')
            new_name = f"order-{safe_service}-{interaction.user.name}"
            # Truncate to 100 chars just in case
            await interaction.channel.edit(name=new_name[:100])
        except:
            pass # Ignore rename errors

        embed = discord.Embed(
            title="📝 **New Order Request**",
            color=0xF1C40F, # Gold/Yellow for order
            timestamp=datetime.now()
        )
        embed.add_field(name="📦 Service", value=f"**{self.service_name}**", inline=True)
        embed.add_field(name="🔢 Quantity", value=str(self.quantity.value), inline=True)
        if self.notes.value:
            embed.add_field(name="🗒️ Notes", value=str(self.notes.value), inline=False)
        
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.set_footer(text="Wait for support to process your order.")

        await interaction.response.send_message(embed=embed)
        # Ping support/admin here if needed
        await interaction.channel.send(f"{interaction.user.mention} Thank you! Support will be with you shortly.")

class PackageSelect(discord.ui.Select):
    def __init__(self, service_type, options):
        self.service_type = service_type
        super().__init__(placeholder=f"Select {service_type} Package...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        package = self.values[0]
        # Open Modal for notes only, since package is selected
        modal = OrderModal(service_name=f"{self.service_type} - {package}", title="Confirm Order")
        # Remove Quantity field since they picked a package, or keep it for "How many codes?" 
        # For simplicity, we keep the original Modal but pre-fill or guide user.
        # Actually creating a specific modal is cleaner.
        
        # specific modal for package
        await interaction.response.send_modal(PackageOrderModal(f"{self.service_type}: {package}"))

class PackageOrderModal(discord.ui.Modal):
    def __init__(self, title_str):
        super().__init__(title="Payment & Delivery")
        self.item_str = title_str
        
        self.payment_method = discord.ui.TextInput(
            label="Payment Method",
            placeholder="CIH, Attijari, Binance, PayPal...",
            required=True,
            style=discord.TextStyle.short
        )
        self.notes = discord.ui.TextInput(
            label="Notes / Riot ID (if applicable)",
            placeholder="Riot ID for VP, Email for Nitro...",
            required=False,
            style=discord.TextStyle.long
        )
        self.add_item(self.payment_method)
        self.add_item(self.notes)

    async def on_submit(self, interaction: discord.Interaction):
        try:
             # Rename channel to order
            safe_item = self.item_str.split(':')[0].lower().replace(' ', '-').replace('v-bucks', 'vbucks')
            await interaction.channel.edit(name=f"order-{safe_item}-{interaction.user.name}"[:100])
            
            # Move to Category
            guild = interaction.guild
            category_name = "Orders" # Default
            
            if "VP" in self.item_str or "Valorant" in self.item_str:
                category_name = "Valorant Orders"
            elif "Nitro" in self.item_str:
                category_name = "Nitro Orders"
            elif "V-Bucks" in self.item_str:
                category_name = "Fortnite Orders"
                
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False)
                }
                category = await guild.create_category(category_name, overwrites=overwrites)
            
            await interaction.channel.edit(category=category)
            
        except Exception as e:
            print(f"Error moving/renaming: {e}")
            pass

        embed = discord.Embed(title="📝 **Order Confirmed**", color=0x2ECC71, timestamp=datetime.now())
        embed.add_field(name="🛒 Item", value=f"**{self.item_str}**", inline=False)
        embed.add_field(name="💳 Payment", value=str(self.payment_method.value), inline=True)
        if self.notes.value:
            embed.add_field(name="🗒️ Notes", value=str(self.notes.value), inline=True)
        
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        embed.set_footer(text="Please verify payment details in the ticket.")
        
        await interaction.response.send_message(embed=embed)
        await interaction.channel.send(f"{interaction.user.mention} Order received! Support will process it shortly.")


class ServiceSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Valorant Points", emoji="<:vp:1466944483504427008>", description="VP Top-up for all regions", value="vp"),
            discord.SelectOption(label="Discord Nitro", emoji="🚀", description="Nitro Boost, Classic, Basic", value="nitro"),
            discord.SelectOption(label="Fortnite V-Bucks", emoji="🎮", description="V-Bucks Top-up", value="vbucks"),
            discord.SelectOption(label="Other / Support", emoji="❓", description="General questions or other services", value="other")
        ]
        super().__init__(placeholder="Select the service you want...", min_values=1, max_values=1, options=options, custom_id="service_select_menu")

    async def callback(self, interaction: discord.Interaction):
        service = self.values[0]
        
        if service == "vp":
            # Show VP Options
            embed = discord.Embed(title="<:vp:1466944483504427008> **Valorant Points Packages**", description="Select your package below:", color=0xFF4654)
            
            # Full List from PRICE_LIST
            options = []
            # Sort by price (int key)
            sorted_prices = sorted(PRICE_LIST.items(), key=lambda x: int(x[0]))
            
            for points, info in sorted_prices:
                points_int = int(points)
                status = " (Out of Stock)" if not info['stock'] else ""
                # Format: 1,000 VP
                label = f"{points_int:,} VP"
                # Description: 5.0 $ | 50 dh (Out of Stock)
                description = f"{info['usd']} $ | {info['dh']} dh{status}"
                
                options.append(discord.SelectOption(
                    label=label, 
                    description=description, 
                    emoji="<:vp:1466944483504427008>"
                ))
            
            # Split into two selects if needed, but max is 25 options, so one is fine.
            view = discord.ui.View()
            view.add_item(PackageSelect("VP", options))
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        elif service == "nitro":
            # Show Nitro Options
            embed = discord.Embed(title="🚀 **Discord Nitro Packages**", description="Select your plan below:", color=0x5865F2)
            options = [
                discord.SelectOption(label="Nitro Boost 1 Month", description="Gift Link - $8 (90 DH)", emoji="🎁"),
                discord.SelectOption(label="Nitro Boost 1 Year", description="Gift Link - $90 (900 DH)", emoji="🎁"),
                discord.SelectOption(label="Nitro Basic 1 Year", description="Gift Link - $30 (300 DH)", emoji="🎁"),
                discord.SelectOption(label="Nitro Boost 1 Year (No Login)", description="Safe - $60 (600 DH)", emoji="🛡️"),
                discord.SelectOption(label="Nitro Boost 1 Year (Login)", description="Login Req - $50 (500 DH)", emoji="⚡")
            ]
            view = discord.ui.View()
            view.add_item(PackageSelect("Nitro", options))
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        elif service == "vbucks":
            embed = discord.Embed(title="🎮 **Fortnite V-Bucks Packages**", description="Select your package below:", color=0x00A2FF)
            
            options = []
            sorted_vbucks = sorted(VBUCKS_PRICES.items(), key=lambda x: int(x[0]))
            
            for vb, price in sorted_vbucks:
                label = f"{int(vb):,} V-Bucks"
                desc = f"{price} DH"
                options.append(discord.SelectOption(label=label, description=desc, emoji="🎮"))

            view = discord.ui.View()
            view.add_item(PackageSelect("V-Bucks", options))
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        else:
            # "Other" - No Modal, just prompt user to speak in chat
            try:
                await interaction.channel.edit(name=f"support-{interaction.user.name}"[:100])
                
                # Move to Support Category
                guild = interaction.guild
                category = discord.utils.get(guild.categories, name="Support Tickets")
                if not category:
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(view_channel=False)
                    }
                    category = await guild.create_category("Support Tickets", overwrites=overwrites)
                
                await interaction.channel.edit(category=category)
            except:
                pass
            
            embed = discord.Embed(
                title="❓ **Other / Support**",
                description="Please describe your Request / Issue directly in this chat.\nSupport will be with you shortly!",
                color=0x95A5A6
            )
            await interaction.response.send_message(embed=embed)

class ServiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ServiceSelect())

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Are you sure you would like to close this ticket?", view=TicketCloseConfirmationView(), ephemeral=False)

class TicketSystemView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 Open Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tickets")
        
        if not category:
            category = await guild.create_category("Tickets")
            
        # Check if user already has a ticket in this category (Active)
        for channel in category.text_channels:
            if interaction.user in channel.overwrites:
                if channel.overwrites[interaction.user].view_channel:
                     await interaction.followup.send(f"❌ You already have a ticket open: {channel.mention}", ephemeral=True)
                     return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }

        channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)
        
        embed = discord.Embed(
            title=f"👋 Welcome {interaction.user.name}!",
            description="Please select the service you are interested in from the menu below.\nاختر الخدمة التي تريدها من القائمة أسفله.",
            color=0x2ECC71
        )
        
        # Send ServiceView which has the Dropdown AND Close button
        await channel.send(f"{interaction.user.mention}", embed=embed, view=ServiceView())
        
        await interaction.followup.send(f"✅ Ticket created: {channel.mention}", ephemeral=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('Bot is ready!')
    
    # Set Status
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Karys Shop | !help_shop"))
    
    # Register Persistent Views
    bot.add_view(TicketSystemView())
    # bot.add_view(TicketControlView()) # Removed/Replaced by ServiceView
    bot.add_view(ServiceView())
    bot.add_view(TicketAdminView())
    bot.add_view(TicketCloseConfirmationView())
    

    
    # Reload active giveaways
    for giveaway_id, data in giveaways_data.items():
        if not data["ended"]:
            bot.add_view(GiveawayJoinButton(giveaway_id, data["required_invites"]))
            
            # Resume timer
            try:
                end_time_ts = data.get("end_time")
                if end_time_ts:
                    now_ts = datetime.now().timestamp()
                    remaining = end_time_ts - now_ts
                    
                    if remaining <= 0:
                        # Ended while offline
                        bot.loop.create_task(end_giveaway_logic(giveaway_id))
                    else:
                        # Resume timer
                        bot.loop.create_task(schedule_giveaway_end(giveaway_id, remaining))
            except Exception as e:
                print(f"Error resuming giveaway {giveaway_id}: {e}")
            
    # Initialize invite cache
    for guild in bot.guilds:
        try:
            invite_cache[guild.id] = await guild.invites()
        except:
            pass
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.command(name='prices', aliases=['p', 'price', 'prix', 'cost'])
async def prices(ctx):
    """Display price list"""
    try:
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
        
        # Add prices
        price_text = ""
        for points, info in PRICE_LIST.items():
            # Using specific logic to match user request while keeping stock status
            # User template: 5,350 :vp: → 25 $ │ 249 dh
            points_int = int(points)
            if not info["stock"]:
                # Strikethrough for out of stock or just mark with X
                price_text += f"{points_int:,} <:vp:1466944483504427008> → {info['usd']} $ │ {info['dh']} dh (Out of Stock)\n"
            else:
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
            value="Send payment proof in the payment ticket channel",
            inline=False
        )
        
        # Set footer
        embed.set_footer(text="Karys Shop | Trusted Valorant Points Provider")

        
        view = TicketButton(ctx.guild.id)
        # Use karys.png for prices command as well (consistent branding)
        # Use karys.png from current directory
        bot_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(bot_dir, "karys.png")
             
        if os.path.exists(image_path):
            file = discord.File(image_path, filename="karys.png")
            embed.set_image(url="attachment://karys.png")
            await ctx.send(embed=embed, file=file, view=view)
        else:
            await ctx.send(embed=embed, view=view)
        print(f'[PRICES] Embed sent successfully')
    except Exception as e:
        print(f'[ERROR] Error in prices command: {e}')
        import traceback
        traceback.print_exc()
        await ctx.send(f'❌ Error: {str(e)}')

@bot.command(name='stock', aliases=['inventory'])
async def stock(ctx):
    """Check stock availability"""
    
    embed = discord.Embed(
        title="📦 Stock Status",
        color=0x00FF00
    )
    
    in_stock = []
    out_of_stock = []
    
    for points, info in PRICE_LIST.items():
        points_int = int(points)
        if info["stock"]:
            in_stock.append(f"{points_int:,} VP")
        else:
            out_of_stock.append(f"{points_int:,} VP")
    
    if in_stock:
        embed.add_field(
            name="✅ In Stock:",
            value="\n".join(in_stock),
            inline=True
        )
    
    if out_of_stock:
        embed.add_field(
            name="❌ Out of Stock:",
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
        value="1. Make payment using one of the accepted methods\n2. Send payment proof in a ticket\n3. Receive your VP within 1-5 minutes",
        inline=False
    )
    
    embed.add_field(
        name="Payment Methods:",
        value="Bank transfer (CIH/BMCE/Attijari) / Binance (USDT) / PayPal",
        inline=False
    )
    
    view = TicketButton(ctx.guild.id)
    await ctx.send(embed=embed, view=view)

@bot.command(name='help_shop', aliases=['shop_help'])
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
        name="!rules",
        value="Display buying terms and rules",
        inline=False
    )
    
    embed.add_field(
        name="!spotify",
        value="Display Spotify Premium subscription plans",
        inline=False
    )
    
    embed.add_field(
        name="!nitro",
        value="Display Discord Nitro Premium plans",
        inline=False
    )

    embed.add_field(
        name="!boost",
        value="Display Server Boost prices",
        inline=False
    )

    embed.add_field(
        name="!gift",
        value="Display Valorant Gifting Service",
        inline=False
    )
    
    embed.add_field(
        name="!help_shop",
        value="Show this help message",
        inline=False
    )
    
    embed.set_footer(text="Karys Shop | Your trusted Valorant Points provider")
    
    await ctx.send(embed=embed)

@bot.command(name='rules', aliases=['terms'])
async def rules(ctx):
    """Display buying terms and rules"""
    embed = discord.Embed(
        title="📜 RULES — BUYING TERMS",
        color=0xFF0000
    )
    
    # Security & Trust
    embed.add_field(
        name="🔐 Security & Trust",
        value="🛡️ Purchases must be made only through verified admins or sellers.\n👤 Anyone claiming to be staff without official confirmation should be ignored.",
        inline=False
    )
    
    # Order Processing
    embed.add_field(
        name="⏱️ Order Processing",
        value="⚡ Orders are delivered within 1 to 5 minutes after payment confirmation.",
        inline=False
    )
    
    # Refund Policy
    embed.add_field(
        name="💸 Refund Policy",
        value="❌ No refunds will be issued once the product has been successfully delivered.",
        inline=False
    )
    
    # Liability
    embed.add_field(
        name="🚫 Liability",
        value="📩 The server is not responsible for scams via private messages or fake accounts.\n🔎 Always verify the official Discord tag before sending payment.",
        inline=False
    )
    
    # Important Warning
    embed.add_field(
        name="🚨 Important Warning",
        value="🎁 Do not trust fake discounts, giveaways, or edited screenshots.",
        inline=False
    )
    
    # Secure Payments
    embed.add_field(
        name="🏦 Secure Payments",
        value="✅ Payments must be made only through official payment channels or verified shop contacts.",
        inline=False
    )
    
    embed.set_footer(text="Karys Shop")
    
    await ctx.send(embed=embed)

@bot.command(name='spotify', aliases=['spotify_plans', 'سبوتيفاي'])
async def spotify(ctx):
    """Display Spotify subscription plans"""
    embed = discord.Embed(
        title="🎵 Spotify Premium | Karys Shop",
        description="**Unleash the power of music!** 🎧\nAd-free music listening, offline playback, and more.",
        color=0x1DB954
    )
    
    # Individual Plan
    embed.add_field(
        name="👤 Individual Plan",
        value="> *Your own personal premium account*\n```ini\n[ 6 Months  ]  $30  (was $59.99)\n[ 12 Months ]  $40  (was $99.99)\n```",
        inline=False
    )
    
    # Duo Plan
    embed.add_field(
        name="👥 Duo Plan (2 Accounts)",
        value="> *Perfect for couples or besties*\n```ini\n[ 6 Months  ]  $40  (was $89.99)\n[ 12 Months ]  $55  (was $179.99)\n```",
        inline=False
    )
    
    # Features
    embed.add_field(
        name="✨ Why Choose Premium?",
        value="✅ *Full Warranty coverage*\n✅ *Works on your existing account*\n✅ *No VPN needed*\n❌ *Account must be free (no active sub)*",
        inline=False
    )
    
    # Ready to buy
    embed.add_field(
        name="💳 Ready to Upgrade?",
        value="Click the **Open a Ticket** button below or go to <#1466942654800597085>! 📩",
        inline=False
    )
    
    embed.set_footer(text="Karys Shop • 100% Satisfaction 💚")
    
    # Add Spotify image from local file (current directory)
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(bot_dir, "spotify.png")
    
    if os.path.exists(image_path):
        try:
            file = discord.File(image_path, filename="spotify.png")
            embed.set_image(url=f"attachment://spotify.png")
            view = TicketButton(ctx.guild.id)
            await ctx.send(embed=embed, file=file, view=view)
        except Exception as e:
            print(f"[ERROR] Failed to send Spotify image: {e}")
            view = TicketButton(ctx.guild.id)
            await ctx.send(embed=embed, view=view)
    else:
        # Fallback
        embed.set_image(url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/1200px-Spotify_logo_without_text.svg.png")
        view = TicketButton(ctx.guild.id)
        await ctx.send(embed=embed, view=view)

@bot.command(name='nitro', aliases=['discord_nitro', 'نترو'])
async def nitro(ctx):
    """Display Discord Nitro Premium plans"""
    embed = discord.Embed(
        title="✨ Discord Nitro Premium | Karys Shop",
        description="**Upgrade your Discord experience with premium perks!** 🚀\nChoose the plan that suits you best below.",
        color=0x5865F2
    )

    # Gift Plan
    embed.add_field(
        name="🎁 Nitro Premium (Gift)",
        value="> *Safe, Stackable, Instant Delivery*\n```ini\n[ 1 Month ]  $8   (was $9.99)\n[ 1 Year  ]  $90  (was $99.99)\n```",
        inline=False
    )
    
    # No Login Plan
    embed.add_field(
        name="🛡️ Nitro Premium (No Login)",
        value="> *No password needed, 100% Safe*\n```ini\n[ 1 Year  ]  $60  (was $99.99)\n```\n❌ *Must have no active subscription*",
        inline=False
    )
    
    # Login Plan
    embed.add_field(
        name="⚡ Nitro Premium (Login)",
        value="> *Cheapest Option, Login Required*\n```ini\n[ 1 Year  ]  $50  (was $99.99)\n```\n❌ *Must have no active subscription*",
        inline=False
    )
    
    # Check current day/time availability or random footer
    embed.add_field(
        name="💳 Ready to buy?",
        value="Click the **Open a Ticket** button below or go to <#1466942654800597085>! 📩",
        inline=False
    )
    
    embed.set_footer(text="Karys Shop • Trusted Service 💎")
    
    # Image handling logic (nitro.png in current dir)
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(bot_dir, "nitro.png")
    
    view = TicketButton(ctx.guild.id)
    
    if os.path.exists(image_path):
        try:
            file = discord.File(image_path, filename="nitro.png")
            embed.set_image(url=f"attachment://nitro.png")
            await ctx.send(embed=embed, file=file, view=view)
        except Exception as e:
            print(f"[ERROR] Failed to send Nitro image: {e}")
            await ctx.send(embed=embed, view=view)
    else:
        # Fallback
        embed.set_image(url="https://cdn.discordapp.com/attachments/1061648397301522472/1061648397301522473/nitro-banner.png")
        await ctx.send(embed=embed, view=view)

@bot.command(name='boost', aliases=['boosts', 'server_boost', 'بوست'])
async def boost(ctx):
    """Display Server Boost prices"""
    embed = discord.Embed(
        title="🚀 Server Boosts | Karys Shop",
        description="**Level up your community!** 💎\nPremium boosts with 3 months warranty.",
        color=0xF47FFF
    )
    
    # 6x Boosts
    embed.add_field(
        name="<:boost_icon:1335969248479707136> 6x Server Boosts",
        value="○ 3 Months\n╰ $8",
        inline=False
    )

    # 8x Boosts
    embed.add_field(
        name="<:boost_icon:1335969248479707136> 8x Server Boosts (Level 2)",
        value="○ 3 Months\n╰ $10",
        inline=False
    )
    
    # 14x Boosts
    embed.add_field(
        name="<:boost_icon:1335969248479707136> 14x Server Boosts (Level 3)",
        value="○ 3 Months\n╰ $20",
        inline=False
    )

    # 20x Boosts
    embed.add_field(
        name="<:boost_icon:1335969248479707136> 20x Server Boosts",
        value="○ 3 Months\n╰ $25",
        inline=False
    )

    # 26x Boosts
    embed.add_field(
        name="<:boost_icon:1335969248479707136> 26x Server Boosts",
        value="○ 3 Months\n╰ $30",
        inline=False
    )

    # 30x Boosts
    embed.add_field(
        name="🔥 30x Server Boosts",
        value="○ 3 Months\n╰ $35",
        inline=False
    )
    
    # Ready to buy
    embed.add_field(
        name="💳 Ready to Boost?",
        value="Click the **Open a Ticket** button below or go to <#1466942654800597085>! 📩",
        inline=False
    )
    
    embed.set_footer(text="Karys Shop • High Quality Boosts 💎")
    
    # Image handling logic (boost.png in current dir)
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(bot_dir, "boost.png")
    
    view = TicketButton(ctx.guild.id)
    
    if os.path.exists(image_path):
        try:
            file = discord.File(image_path, filename="boost.png")
            embed.set_image(url=f"attachment://boost.png")
            await ctx.send(embed=embed, file=file, view=view)
        except Exception as e:
            print(f"[ERROR] Failed to send Boost image: {e}")
            await ctx.send(embed=embed, view=view)
    else:
        # Fallback image
        embed.set_image(url="https://support.discord.com/hc/article_attachments/360013500334/Nitro_Server_Boost_101.jpg")
        await ctx.send(embed=embed, view=view)

@bot.command(name='gift', aliases=['gifting', 'الهدايا', 'هدايا'])
async def gift(ctx):
    """Display Gifting Announcement"""
    embed = discord.Embed(
        title="🎁 OFFICIAL GIFTING SERVICE",
        description="**Get your favorite Valorant skins & bundles directly in-game!**\nWe offer a safe and instant gifting service.",
        color=0xFD4556  # Valorant Red
    )
    
    # Riot ID Section with clear formatting
    embed.add_field(
        name="🆔 Riot ID to Add",
        value="```\nGaprex#Karys\n```\n*Send a friend request to this ID to start.*",
        inline=False
    )
    
    # English Process
    embed.add_field(
        name="🇺🇸 How it works",
        value=(
            "**1️⃣ Add Friend:** Send a request to the ID above.\n"
            "**2️⃣ Wait 7 Days:** Wait the mandatory 7-day period (Riot Rule).\n" # Corrected to 24h as standard validation, though user said 7 days? standard is 24h for gifting usually, but user said 7 days "mandatory". I should STICK TO USER TEXT calling it 7 days.
            "**3️⃣ Payment:** Pay via CIH / Attijari / Crypto.\n"
            "**4️⃣ Receive:** Get your skin/bundle instantly!"
        ),
        inline=False
    )
    
    embed.add_field(name=" ", value="━━━━━━━━━━━━━━━━━━━━━━", inline=False) # Separator

    # Arabic Process
    embed.add_field(
        name="🇲🇦 طريقة العمل",
        value=(
            "**1️⃣ طلب صداقة:** أرسل طلب للآيدي الموضح أعلاه.\n"
            "**2️⃣ الانتظار:** انتظر مدة 7 أيام (قانون اللعبة).\n" # Stick to user's "7 days"
            "**3️⃣ الدفع:** ادفع عبر CIH / التجاري / Crypto.\n"
            "**4️⃣ الاستلام:** استلم هديتك فوراً!"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🛡️ 100% Safe & Secure",
        value="Click the **Open a Ticket** button below to order! 📩",
        inline=False
    )

    embed.set_footer(text="Karys Shop | Valorant Gifting Service", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    
    # Try to add a thumbnail if Karys logo exists (karys.png in current dir)
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(bot_dir, "karys.png")
         
    view = TicketButton(ctx.guild.id)

    if os.path.exists(image_path):
        file = discord.File(image_path, filename="karys.png")
        embed.set_thumbnail(url="attachment://karys.png")
        await ctx.send(embed=embed, file=file, view=view)
    else:
        await ctx.send(embed=embed, view=view)

@bot.tree.command(name="gift", description="Display Gifting Announcement")
async def gift_slash(interaction: discord.Interaction):
    """Slash command to display Gifting Announcement"""
    embed = discord.Embed(
        title="🎁 OFFICIAL GIFTING SERVICE",
        description="**Get your favorite Valorant skins & bundles directly in-game!**\nWe offer a safe and instant gifting service.",
        color=0xFD4556  # Valorant Red
    )
    
    # Riot ID with code block
    embed.add_field(
        name="🆔 Riot ID to Add",
        value="```\nGaprex#Karys\n```\n*Send a friend request to this ID to start.*",
        inline=False
    )
    
    # How it works
    embed.add_field(
        name="✨ How it works",
        value=(
            "**1️⃣ Add Friend:** Send a request to the ID above.\n"
            "**2️⃣ Wait 7 Days:** Wait the mandatory 7-day period (Riot Rule).\n"
            "**3️⃣ Payment:** Pay via Credit Card / Crypto / PayPal.\n"
            "**4️⃣ Receive:** Get your skin/bundle instantly!"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🛡️ 100% Safe & Secure",
        value="Click the **Order Ticket** button below to order! 📩",
        inline=False
    )

    embed.set_footer(text="Karys Shop | Valorant Gifting Service", icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None)
    
    # Image logic for slash command (karys.png in current dir)
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(bot_dir, "karys.png")
    
    view = TicketButton(interaction.guild_id)
    
    if os.path.exists(image_path):
        file = discord.File(image_path, filename="karys.png")
        embed.set_thumbnail(url="attachment://karys.png")
        await interaction.response.send_message(embed=embed, file=file, view=view)
    else:
        await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="spotify", description="عرض خطط Spotify Premium")
async def spotify_slash(interaction: discord.Interaction):
    """Slash command to display Spotify plans"""
    embed = discord.Embed(
        title="🎵 Spotify Premium | Karys Shop",
        description="**Unleash the power of music!** 🎧\nAd-free music listening, offline playback, and more.",
        color=0x1DB954
    )
    
    # Individual Plan
    embed.add_field(
        name="👤 Individual Plan",
        value="> *Your own personal premium account*\n```ini\n[ 6 Months  ]  $30  (was $59.99)\n[ 12 Months ]  $40  (was $99.99)\n```",
        inline=False
    )
    
    # Duo Plan
    embed.add_field(
        name="👥 Duo Plan (2 Accounts)",
        value="> *Perfect for couples or besties*\n```ini\n[ 6 Months  ]  $40  (was $89.99)\n[ 12 Months ]  $55  (was $179.99)\n```",
        inline=False
    )
    
    # Features
    embed.add_field(
        name="✨ Why Choose Premium?",
        value="✅ *Full Warranty coverage*\n✅ *Works on your existing account*\n✅ *No VPN needed*\n❌ *Account must be free (no active sub)*",
        inline=False
    )
    
    # Ready to buy
    embed.add_field(
        name="💳 Ready to Upgrade?",
        value="Click the **Order Ticket** below or contact an admin! 📩",
        inline=False
    )
    
    embed.set_footer(text="Karys Shop • 100% Satisfaction 💚")
    
    # Image handling logic (spotify.png in current dir)
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(bot_dir, "spotify.png")
    
    if os.path.exists(image_path):
        try:
            file = discord.File(image_path, filename="spotify.png")
            embed.set_image(url=f"attachment://spotify.png")
            view = TicketButton(interaction.guild_id)
            await interaction.response.send_message(embed=embed, file=file, view=view)
        except Exception as e:
            print(f"[ERROR] Failed to send Spotify image: {e}")
            view = TicketButton(interaction.guild_id)
            await interaction.response.send_message(embed=embed, view=view)
    else:
        # Fallback
        embed.set_image(url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/1200px-Spotify_logo_without_text.svg.png")
        view = TicketButton(interaction.guild_id)
        await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="nitro", description="عرض خطط Discord Nitro Premium")
async def nitro_slash(interaction: discord.Interaction):
    """Slash command to display Nitro plans"""
    embed = discord.Embed(
        title="✨ Discord Nitro Premium | Karys Shop",
        description="**Upgrade your Discord experience with premium perks!** 🚀\nChoose the plan that suits you best below.",
        color=0x5865F2
    )

    # Gift Plan
    embed.add_field(
        name="🎁 Nitro Premium (Gift)",
        value="> *Safe, Stackable, Instant Delivery*\n```ini\n[ 1 Month ]  $8   (was $9.99)\n[ 1 Year  ]  $90  (was $99.99)\n```",
        inline=False
    )
    
    # No Login Plan
    embed.add_field(
        name="🛡️ Nitro Premium (No Login)",
        value="> *No password needed, 100% Safe*\n```ini\n[ 1 Year  ]  $60  (was $99.99)\n```\n❌ *Must have no active subscription*",
        inline=False
    )
    
    # Login Plan
    embed.add_field(
        name="⚡ Nitro Premium (Login)",
        value="> *Cheapest Option, Login Required*\n```ini\n[ 1 Year  ]  $50  (was $99.99)\n```\n❌ *Must have no active subscription*",
        inline=False
    )
    
    # Check current day/time availability or random footer
    embed.add_field(
        name="💳 Ready to buy?",
        value="Click the **Open a Ticket** button below or go to <#1466942654800597085>! 📩",
        inline=False
    )
    
    embed.set_footer(text="Karys Shop • Trusted Service 💎")
    
    # Image handling logic (nitro.png in current dir)
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(bot_dir, "nitro.png")
    
    view = TicketButton(interaction.guild_id)
    
    if os.path.exists(image_path):
        try:
            file = discord.File(image_path, filename="nitro.png")
            embed.set_image(url=f"attachment://nitro.png")
            await interaction.response.send_message(embed=embed, file=file, view=view)
        except Exception as e:
            print(f"[ERROR] Failed to send Nitro image: {e}")
            await interaction.response.send_message(embed=embed, view=view)
    else:
        # Fallback
        embed.set_image(url="https://cdn.discordapp.com/attachments/1061648397301522472/1061648397301522473/nitro-banner.png")
        await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="boost", description="عرض أسعار Server Boosts")
async def boost_slash(interaction: discord.Interaction):
    """Slash command to display Boost prices"""
    embed = discord.Embed(
        title="🚀 Server Boosts | Karys Shop",
        description="**Level up your community!** 💎\nPremium boosts with 3 months warranty.",
        color=0xF47FFF
    )
    
    # 6x Boosts
    embed.add_field(
        name="<:boost_icon:1335969248479707136> 6x Server Boosts",
        value="○ 3 Months\n╰ $8",
        inline=False
    )

    # 8x Boosts
    embed.add_field(
        name="<:boost_icon:1335969248479707136> 8x Server Boosts (Level 2)",
        value="○ 3 Months\n╰ $10",
        inline=False
    )
    
    # 14x Boosts
    embed.add_field(
        name="<:boost_icon:1335969248479707136> 14x Server Boosts (Level 3)",
        value="○ 3 Months\n╰ $20",
        inline=False
    )

    # 20x Boosts
    embed.add_field(
        name="<:boost_icon:1335969248479707136> 20x Server Boosts",
        value="○ 3 Months\n╰ $25",
        inline=False
    )

    # 26x Boosts
    embed.add_field(
        name="<:boost_icon:1335969248479707136> 26x Server Boosts",
        value="○ 3 Months\n╰ $30",
        inline=False
    )

    # 30x Boosts
    embed.add_field(
        name="🔥 30x Server Boosts",
        value="○ 3 Months\n╰ $35",
        inline=False
    )
    
    # Ready to buy
    embed.add_field(
        name="💳 Ready to Boost?",
        value="Click the **Open a Ticket** button below or go to <#1466942654800597085>! 📩",
        inline=False
    )
    
    embed.set_footer(text="Karys Shop • High Quality Boosts 💎")
    
    # Image handling logic (boost.png in current dir)
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(bot_dir, "boost.png")
    
    view = TicketButton(interaction.guild_id)
    
    if os.path.exists(image_path):
        try:
            file = discord.File(image_path, filename="boost.png")
            embed.set_image(url=f"attachment://boost.png")
            await interaction.response.send_message(embed=embed, file=file, view=view)
        except Exception as e:
            print(f"[ERROR] Failed to send Boost image: {e}")
            await interaction.response.send_message(embed=embed, view=view)
    else:
        # Fallback image
        embed.set_image(url="https://support.discord.com/hc/article_attachments/360013500334/Nitro_Server_Boost_101.jpg")
        await interaction.response.send_message(embed=embed, view=view)

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
    embed.set_footer(text="Karys Shop")
    
    return embed

@bot.tree.command(name="post", description="إنشاء منشور قائمة الأسعار")
async def post(interaction: discord.Interaction):
    """Slash command to post price list"""
    embed = create_price_post()
    # Add KARYS SHOP promotional image from local file (karys.png in current dir)
    # Get the directory where bot.py is located
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(bot_dir, "karys.png")
    
    if os.path.exists(image_path):
        print(f"[INFO] Found image at: {image_path}")
        try:
            # Create Discord File object directly from file path
            file = discord.File(image_path, filename="karys.png")
            embed.set_image(url=f"attachment://karys.png")
            view = TicketButton(interaction.guild_id)
            await interaction.response.send_message(embed=embed, file=file, view=view)
            print(f"[SUCCESS] Image sent successfully")
        except Exception as e:
            print(f"[ERROR] Failed to send image: {e}")
            # Try sending without image
            view = TicketButton(interaction.guild_id)
            await interaction.response.send_message(embed=embed, view=view)
    else:
        print(f"[WARNING] Image not found at: {image_path}")
        view = TicketButton(interaction.guild_id)
        await interaction.response.send_message(embed=embed, view=view)

@bot.command(name='post', aliases=['منشور'])
async def post_command(ctx):
    """Create price list post"""
    embed = create_price_post()
    # Add KARYS SHOP promotional image from local file (karys.png in current dir)
    # Get the directory where bot.py is located
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(bot_dir, "karys.png")
    
    view = TicketButton(ctx.guild.id)
    if os.path.exists(image_path):
        print(f"[INFO] Found image at: {image_path}")
        try:
            # Create Discord File object directly from file path
            file = discord.File(image_path, filename="karys.png")
            embed.set_image(url=f"attachment://karys.png")
            await ctx.send(embed=embed, file=file, view=view)
            print(f"[SUCCESS] Image sent successfully")
        except Exception as e:
            print(f"[ERROR] Failed to send image: {e}")
            # Try sending without image
            await ctx.send(embed=embed, view=view)
    else:
        print(f"[WARNING] Image not found at: {image_path}")
        await ctx.send(embed=embed, view=view)

@bot.command(name='payment', aliases=['pay', 'bank', 'rib', 'الدفع'])
async def payment(ctx):
    """Display Payment Methods"""
    embed = discord.Embed(
        title="💳 **SECURE PAYMENT METHODS** | طرق الدفع",
        description=(
            "To complete your purchase, please choose a payment method below and **open a ticket**.\n"
            "لإتمام عملية الشراء، اختر طريقة الدفع وافتح تذكرة."
        ),
        color=0xFF0000 
    )

    # Bank Transfer Section
    embed.add_field(
        name="🏦 **Bank Transfer** (تحويل بنكي)",
        value=(
            "> **CIH Bank**\n"
            "> **BMCE Bank**\n"
            "> **Attijariwafa Bank**\n"
            "> **Barid Bank**\n"
            "```fix\n"
            "Open a ticket to receive RIB / Account Number\n"
            "افتح تذكرة للحصول على رقم الحساب البنكي"
            "\n```"
        ),
        inline=False
    )
    
    # Crypto & Electronic Section
    embed.add_field(
        name="🪙 **Crypto & E-Wallets**",
        value=(
            "> **Binance Pay** (USDT)\n"
            "> **USDT (TRC20)**\n"
            "> **PayPal** (FnF Only)\n"
            "```fix\n"
            "Open a ticket to receive Wallet / Email\n"
            "افتح تذكرة للحصول على المحفظة أو البريد"
            "\n```"
        ),
        inline=False
    )

    # Separator
    embed.add_field(name=" ", value="━━━━━━━━━━━━━━━━━━━━━━", inline=False)
    
    # Process Steps
    embed.add_field(
        name="📝 **How to Order?** (كيفاش تشري؟)",
        value=(
            "1️⃣ **Open Ticket** 📩 : Click the button below.\n"
            "2️⃣ **Selection** 🗣️ : Tell us payment method + Product.\n"
            "3️⃣ **Payment** 💸 : Send the money & Screenshot.\n"
            "4️⃣ **Delivery** 🚀 : Receive your product instantly!"
        ),
        inline=False
    )
    
    embed.set_footer(text="Karys Shop | Trusted & Secure 🔒", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    
    # Image handling logic (karys.png in current dir)
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    karys_image_path = os.path.join(bot_dir, "karys.png")

    view = TicketButton(ctx.guild.id)
    
    if os.path.exists(karys_image_path):
        try:
            file = discord.File(karys_image_path, filename="karys.png")
            embed.set_thumbnail(url="attachment://karys.png")
            await ctx.send(embed=embed, file=file, view=view)
        except Exception as e:
            print(f"[ERROR] Failed to send image: {e}")
            await ctx.send(embed=embed, view=view)
    else:
        await ctx.send(embed=embed, view=view)


@bot.tree.command(name="payment", description="عرض طرق الدفع (Show Payment Methods)")
async def payment_slash(interaction: discord.Interaction):
    """Slash command to display Payment Methods"""
    embed = discord.Embed(
        title="💳 **SECURE PAYMENT METHODS** | طرق الدفع",
        description=(
            "To complete your purchase, please choose a payment method below and **open a ticket**.\n"
            "لإتمام عملية الشراء، اختر طريقة الدفع وافتح تذكرة."
        ),
        color=0xFF0000 
    )

    # Bank Transfer Section
    embed.add_field(
        name="🏦 **Bank Transfer** (تحويل بنكي)",
        value=(
            "> **CIH Bank**\n"
            "> **BMCE Bank**\n"
            "> **Attijariwafa Bank**\n"
            "> **Barid Bank**\n"
            "```fix\n"
            "Open a ticket to receive RIB / Account Number\n"
            "افتح تذكرة للحصول على رقم الحساب البنكي"
            "\n```"
        ),
        inline=False
    )
    
    # Crypto & Electronic Section
    embed.add_field(
        name="🪙 **Crypto & E-Wallets**",
        value=(
            "> **Binance Pay** (USDT)\n"
            "> **USDT (TRC20)**\n"
            "> **PayPal** (FnF Only)\n"
            "```fix\n"
            "Open a ticket to receive Wallet / Email\n"
            "افتح تذكرة للحصول على المحفظة أو البريد"
            "\n```"
        ),
        inline=False
    )

    # Separator
    embed.add_field(name=" ", value="━━━━━━━━━━━━━━━━━━━━━━", inline=False)
    
    # Process Steps
    embed.add_field(
        name="📝 **How to Order?** (كيفاش تشري؟)",
        value=(
            "1️⃣ **Open Ticket** 📩 : Click the button below.\n"
            "2️⃣ **Selection** 🗣️ : Tell us payment method + Product.\n"
            "3️⃣ **Payment** 💸 : Send the money & Screenshot.\n"
            "4️⃣ **Delivery** 🚀 : Receive your product instantly!"
        ),
        inline=False
    )
    
    embed.set_footer(text="Karys Shop | Trusted & Secure 🔒", icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None)
    
    # Image handling logic
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(bot_dir)
    karys_image_path = os.path.join(parent_dir, "IMG", "karys.png")
    if not os.path.exists(karys_image_path):
         karys_image_path = os.path.join(bot_dir, "IMG", "karys.png")
    
    view = TicketButton(interaction.guild_id)
    
    if os.path.exists(karys_image_path):
        try:
            file = discord.File(karys_image_path, filename="karys.png")
            embed.set_thumbnail(url="attachment://karys.png")
            await interaction.response.send_message(embed=embed, file=file, view=view)
        except Exception as e:
            print(f"[ERROR] Failed to send image: {e}")
            await interaction.response.send_message(embed=embed, view=view)
    else:
        await interaction.response.send_message(embed=embed, view=view)

@bot.command(name='vbucks', aliases=['vb', 'fortnite', 'vbuck', 'فورتنايت'])
async def vbucks(ctx):
    """Display Fortnite V-Bucks Prices"""
    embed = discord.Embed(
        title="<:Vbucks:1470075477975630059> **FORTNITE V-BUCKS PRICES**",
        description="**Get your V-Bucks safely and instantly!** ⚡\n*Legal & Safe 100%*",
        color=0x9146FF # Purple Color
    )
    
    # Price List
    embed.add_field(
        name="💸 **Price List**",
        value=(
            "> **10,000 V-Bucks**  →  **400 DH**\n"
            "> **12,000 V-Bucks**  →  **480 DH**\n"
            "> **15,000 V-Bucks**  →  **600 DH**\n"
            "> **25,000 V-Bucks**  →  **1000 DH**\n"
            "> **50,000 V-Bucks**  →  **1800 DH**"
        ),
        inline=False
    )
    
    # Process
    embed.add_field(
        name="📝 **How to Buy?**",
        value=(
            "1️⃣ **Open Ticket** 📩 : Click button below\n"
            "2️⃣ **Payment** 💳 : <#1466153813323808849>\n"
            "3️⃣ **Delivery** 🚀 : Instant delivery to your account"
        ),
        inline=False
    )
    
    embed.set_footer(text="Karys Shop | Fortnite Services 🛒", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    
    # Image handling logic
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    
    # User requested specific image: image.png for vbucks
    image_path = os.path.join(bot_dir, "image.png")
    
    # Fallback to vbucks.png if image.png doesn't exist (safety)
    if not os.path.exists(image_path):
         image_path = os.path.join(bot_dir, "vbucks.png")

    view = TicketButton(ctx.guild.id)
    
    if os.path.exists(image_path):
        try:
            filename = os.path.basename(image_path)
            file = discord.File(image_path, filename=filename)
            embed.set_image(url=f"attachment://{filename}")
            await ctx.send(embed=embed, file=file, view=view)
        except Exception as e:
            print(f"[ERROR] Failed to send image: {e}")
            await ctx.send(embed=embed, view=view)
    else:
        # Web fallback if no local image
        embed.set_image(url="https://cdn2.unrealengine.com/fortnite-v-bucks-1920x1080-866247833.jpg")
        await ctx.send(embed=embed, view=view)


@bot.tree.command(name="vbucks", description="عرض أسعار الفيباكس (Show V-Bucks Prices)")
async def vbucks_slash(interaction: discord.Interaction):
    """Slash command to display V-Bucks Prices"""
    embed = discord.Embed(
        title="<:Vbucks:1470075477975630059> **FORTNITE V-BUCKS PRICES**",
        description="**Get your V-Bucks safely and instantly!** ⚡\n*Legal & Safe 100%*",
        color=0x9146FF # Purple Color
    )
    
    # Price List
    embed.add_field(
        name="💸 **Price List**",
        value=(
            "> **10,000 V-Bucks**  →  **400 DH**\n"
            "> **12,000 V-Bucks**  →  **480 DH**\n"
            "> **15,000 V-Bucks**  →  **600 DH**\n"
            "> **25,000 V-Bucks**  →  **1000 DH**\n"
            "> **50,000 V-Bucks**  →  **1800 DH**"
        ),
        inline=False
    )
    
    # Process
    embed.add_field(
        name="📝 **How to Buy?**",
        value=(
            "1️⃣ **Open Ticket** 📩 : Click button below\n"
            "2️⃣ **Payment** 💳 : <#1466153813323808849>\n"
            "3️⃣ **Delivery** 🚀 : Instant delivery to your account"
        ),
        inline=False
    )
    
    embed.set_footer(text="Karys Shop | Fortnite Services 🛒", icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None)
    
    # Image handling logic (image.png in current dir)
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    
    # User requested specific image: image.png for vbucks
    image_path = os.path.join(bot_dir, "image.png")
    
    # Fallback to vbucks.png if image.png doesn't exist
    if not os.path.exists(image_path):
         image_path = os.path.join(bot_dir, "vbucks.png")
    
    view = TicketButton(interaction.guild_id)
    
    if os.path.exists(image_path):
        try:
            filename = os.path.basename(image_path)
            file = discord.File(image_path, filename=filename)
            embed.set_image(url=f"attachment://{filename}")
            await interaction.response.send_message(embed=embed, file=file, view=view)
        except Exception as e:
            print(f"[ERROR] Failed to send image: {e}")
            await interaction.response.send_message(embed=embed, view=view)
    else:
        # Web fallback
        embed.set_image(url="https://cdn2.unrealengine.com/fortnite-v-bucks-1920x1080-866247833.jpg")
        await interaction.response.send_message(embed=embed, view=view)

@bot.command(name='scan')
@commands.has_permissions(administrator=True)
async def scan_accounts(ctx):
    """Scan for accounts created less than 1 month ago and timeout them"""
    await ctx.send("🔍 Scanning members... This might take a moment.")
    
    count_scanned = 0
    count_timed_out = 0
    timed_out_members = []
    
    # 1 month ago (30 days)
    # Ensure timezone awareness for comparison
    one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    try:
        # Iterate over all members in the guild
        for member in ctx.guild.members:
            if member.bot:
                continue
                
            count_scanned += 1
            
            # Check if account creation date is less than 30 days ago
            # member.created_at is timezone-aware (UTC)
            if member.created_at > one_month_ago:
                try:
                    # Timeout for 7 days
                    await member.timeout(timedelta(days=7), reason="Account too new (< 1 month) - Auto Scan")
                    count_timed_out += 1
                    timed_out_members.append(member.mention)
                    print(f"[SCAN] Timed out {member.name} (Created: {member.created_at})")
                except discord.Forbidden:
                    print(f"[SCAN] Failed to timeout {member.name} (Missing permissions)")
                except Exception as e:
                    print(f"[SCAN] Error timing out {member.name}: {e}")
        
        # Prepare result message
        result_msg = f"✅ Scan complete.\n📊 **Results:**\n- Scanned: `{count_scanned}` members\n- Timed out: `{count_timed_out}` members (Account < 30 days old)\n- Timeout Duration: 7 Days"
        
        if count_timed_out > 0:
            result_msg += "\n\n**Timed Out Members:**"
            await ctx.send(result_msg)
            
            # Send members in chunks of 2000 characters
            chunk = ""
            for member_mention in timed_out_members:
                entry = f"• {member_mention}\n"
                if len(chunk) + len(entry) > 1900: # Leave some buffer
                    await ctx.send(chunk)
                    chunk = entry
                else:
                    chunk += entry
            
            if chunk:
                await ctx.send(chunk)
        else:
            await ctx.send(result_msg)
            
    except Exception as e:
        print(f"[ERROR] Scan failed: {e}")
        await ctx.send(f"❌ An error occurred during scan: {str(e)}")

@bot.command(name='remove')
@commands.has_permissions(administrator=True)
async def remove_timeouts(ctx):
    """Remove timeout from all members"""
    await ctx.send("🔓 Removing timeouts from all members... This might take a moment.")
    
    count_removed = 0
    
    try:
        # Iterate over all members in the guild
        for member in ctx.guild.members:
            if member.bot:
                continue
            
            # Check if member is timed out
            if member.is_timed_out():
                try:
                    # Remove timeout by setting it to None
                    await member.timeout(None, reason="Admin Remove Command")
                    count_removed += 1
                    print(f"[REMOVE] Removed timeout from {member.name}")
                except discord.Forbidden:
                    print(f"[REMOVE] Failed to remove timeout from {member.name} (Missing permissions)")
                except Exception as e:
                    print(f"[REMOVE] Error removing timeout from {member.name}: {e}")
        
        await ctx.send(f"✅ Removal complete.\n🔓 **Result:** Removed timeout from `{count_removed}` members.")
        
    except Exception as e:
        print(f"[ERROR] Remove failed: {e}")
        await ctx.send(f"❌ An error occurred during removal: {str(e)}")

@bot.command(name='setup_roles')
@commands.has_permissions(administrator=True)
async def setup_roles(ctx):
    """Create shop roles with no permissions"""
    await ctx.send("🛠️ Setting up roles...")
    
    # Define roles: Name, Color
    roles_to_create = [
        {"name": "👑・Mythic Clients", "color": 0x992D22},    # Dark Red
        {"name": "💎・Royalty +500$", "color": 0xE67E22},    # Dark Gold/Orange
        {"name": "🌟・Prestige +100$", "color": 0xF1C40F},   # Gold Yellow
        {"name": "🔮・Premium +50$", "color": 0x71368A}      # Dark Purple
    ]
    
    created_count = 0
    skipped_count = 0
    
    try:
        guild = ctx.guild
        for role_data in roles_to_create:
            existing_role = discord.utils.get(guild.roles, name=role_data["name"])
            
            if existing_role:
                # Update existing role
                await existing_role.edit(
                    color=discord.Color(role_data["color"]),
                    permissions=discord.Permissions.none(),
                    reason="Setup Roles Command - Update"
                )
                print(f"[ROLES] Updated role: {role_data['name']}")
                skipped_count += 1 # Counting as skipped for creation, but it is updated
            else:
                # Create role with NO permissions
                await guild.create_role(
                    name=role_data["name"],
                    color=discord.Color(role_data["color"]),
                    permissions=discord.Permissions.none(),
                    reason="Setup Roles Command - Create"
                )
                created_count += 1
                print(f"[ROLES] Created role: {role_data['name']}")
            
        await ctx.send(f"✅ Setup complete!\n✨ **Created:** `{created_count}` roles\n🔄 **Updated:** `{skipped_count}` roles")
        
    except Exception as e:
        print(f"[ERROR] Setup roles failed: {e}")
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name='bdal')
@commands.has_permissions(administrator=True)
async def change_role_name(ctx, old_name: str, new_name: str):
    """Change role name. Usage: !bdal "Old Name" "New Name" """
    role = discord.utils.get(ctx.guild.roles, name=old_name)
    
    if role:
        try:
            await role.edit(name=new_name, reason="Admin Rename Command")
            await ctx.send(f"✅ Role renamed successfully!\nOld: `{old_name}`\nNew: `{new_name}`")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to edit this role.")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")
    else:
        await ctx.send(f"❌ Role `{old_name}` not found!")

@change_role_name.error
async def change_role_name_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ **Usage:** `!bdal "Old Name" "New Name"`\nExample: `!bdal "👑・Mythic Clients" "👑・King Clients"`')

@bot.command(name='say')
@commands.has_permissions(administrator=True)
async def say(ctx, *, message):
    """Make the bot say something"""
    await ctx.message.delete()
    await ctx.send(message)





@bot.command(name='ticket_panel')
@commands.has_permissions(administrator=True)
async def ticket_panel(ctx):
    """Deploy the ticket panel"""
    await ctx.message.delete()
    embed = discord.Embed(
        title="🛒 **KARYS SHOP | SUPPORT & ORDERS**",
        description=(
            "**Welcome to Karys Shop!** 🌟\n"
            "مرحباً بكم في متجر كاريس! 🇲🇦\n\n"
            "**Open a ticket for:**\n"
            "💸 **Buying & Selling** (Accounts, Points, Nitro)\n"
            "🛠️ **Support & Assistance**\n"
            "🤝 **Business Inquiries**\n\n"
            "*Click the button below to start your transaction!* 📩"
        ),
        color=0xFF0000
    )
    
    # Image handling logic (karys.png in current dir)
    bot_dir = os.path.dirname(os.path.abspath(__file__))
    karys_image_path = os.path.join(bot_dir, "karys.png")
    
    if os.path.exists(karys_image_path):
        try:
            file = discord.File(karys_image_path, filename="karys.png")
            embed.set_thumbnail(url="attachment://karys.png")
            await ctx.send(embed=embed, file=file, view=TicketSystemView())
        except Exception as e:
            print(f"[ERROR] Failed to send image: {e}")
            await ctx.send(embed=embed, view=TicketSystemView())
    else:
        # Fallback to just embed
        await ctx.send(embed=embed, view=TicketSystemView())


# --- Utility Commands ---

@bot.command(name="sync")
async def sync(ctx):
    """Sync slash commands manually"""
    if ctx.author.guild_permissions.administrator:
        try:
            synced = await bot.tree.sync()
            await ctx.send(f"✅ Synced {len(synced)} slash commands.")
        except Exception as e:
            await ctx.send(f"❌ Error syncing: {e}")
    else:
        await ctx.send("❌ You do not have permission to use this command.")

@bot.command(name="giveaway")
async def giveaway_prefix(ctx):
    await ctx.send("⚠️ **Please use the new slash command:** `/kgiveaway`\nExample: `/kgiveaway` then select `create`")

@bot.command(name="invites")
async def invites_prefix(ctx):
    await ctx.send("⚠️ **Please use the slash command:** `/invites`")

# --- Giveaway Commands ---

@bot.tree.command(name="invites", description="Check your invites or another user's")
async def invites(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    user_id = str(target.id)
    
    if user_id not in invites_data:
        invites_data[user_id] = {"regular": 0, "fake": 0, "bonus": 0, "leaves": 0}
        
    data = invites_data[user_id]
    total = (data["regular"] + data["bonus"]) - (data["leaves"] + data["fake"])
    if total < 0: total = 0
    
    embed = discord.Embed(title=f"✉️ Invites for {target.name}", color=0x3498DB)
    embed.add_field(name="Total Valid", value=f"**{total}**", inline=False)
    embed.add_field(name="Details", value=f"✅ Regular: {data['regular']}\n🎁 Bonus: {data['bonus']}\n🚪 Left: {data['leaves']}\n❌ Fake: {data['fake']}", inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="kgiveaway", description="Manage Giveaways (Admin Only)")
@discord.app_commands.describe(
    action="Select an action to perform",
    duration="Duration (e.g. 10m, 1h, 1d) (For create)",
    winners="Number of winners (For create/reroll)",
    prize="Prize description (For create)",
    required_invites="Invites required to join (For create)",
    message_id="Message ID of the giveaway (For end/reroll/list)",
    user="User to manage chances (For chance)",
    amount="Amount of chances to add (For chance)"
)
async def kgiveaway(interaction: discord.Interaction, action: Literal["create", "end", "reroll", "list", "chance"], duration: str = None, winners: int = 1, prize: str = None, required_invites: int = 0, message_id: str = None, user: discord.Member = None, amount: int = None):
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        return

    if action == "create":
        if not duration or not prize:
            await interaction.response.send_message("❌ Usage: `/giveaway create <duration> <winners> <prize> [invites]`", ephemeral=True)
            return
            
        # Parse duration
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        try:
            unit = duration[-1]
            value = int(duration[:-1])
            if unit not in time_units:
                raise ValueError
            seconds = value * time_units[unit]
        except:
             await interaction.response.send_message("❌ Invalid duration format. Use 10m, 1h, 1d etc.", ephemeral=True)
             return

        end_time = datetime.now() + timedelta(seconds=seconds)
        timestamp = int(end_time.timestamp())
        
        embed = discord.Embed(title=f"🎉 **GIVEAWAY: {prize}** 🎉", description=f"React to join!\n\n**Ends:** <t:{timestamp}:R>", color=0xFF00FF)
        embed.add_field(name="🏆 Winners", value=str(winners), inline=True)
        embed.add_field(name="📨 Required Invites", value=str(required_invites), inline=True)
        embed.add_field(name="👥 Entries", value="0", inline=True)
        embed.add_field(name="Hosted By", value=interaction.user.mention, inline=False)
        embed.set_footer(text=f"Ends at")
        embed.timestamp = end_time
        
        await interaction.response.send_message("🎉 Giveaway created!", ephemeral=True)
        message = await interaction.channel.send(embed=embed)
        
        # Save giveaway
        giveaways_data[str(message.id)] = {
            "channel_id": interaction.channel_id,
            "prize": prize,
            "winners": winners,
            "required_invites": required_invites,
            "end_time": timestamp,
            "participants": [],
            "ended": False
        }
        save_data('giveaways.json', giveaways_data)
        
        # Add View
        await message.edit(view=GiveawayJoinButton(message.id, required_invites))
        
        # Background task to end giveaway
        asyncio.create_task(schedule_giveaway_end(message.id, seconds))

    elif action == "end":
        if not message_id:
            await interaction.response.send_message("❌ Please provide the Message ID.", ephemeral=True)
            return
        await end_giveaway_logic(int(message_id))
        await interaction.response.send_message("✅ Giveaway process triggered.", ephemeral=True)

    elif action == "reroll":
        if not message_id:
            await interaction.response.send_message("❌ Please provide the Message ID.", ephemeral=True)
            return
            
        await reroll_giveaway(interaction, message_id, winners)

    elif action == "list":
        if not message_id:
            await interaction.response.send_message("❌ Please provide the Message ID.", ephemeral=True)
            return
            
        if message_id not in giveaways_data:
             await interaction.response.send_message("❌ Giveaway not found.", ephemeral=True)
             return
             
        participants = giveaways_data[message_id]["participants"]
        await interaction.response.send_message(f"📂 **Participants ({len(participants)}):**\n" + ", ".join([f"<@{uid}>" for uid in participants[:50]]) + (f"... and {len(participants)-50} more" if len(participants) > 50 else ""), ephemeral=True)

    elif action == "chance":
        if not user or amount is None:
             await interaction.response.send_message("❌ Usage: `/giveaway chance @user <amount>`", ephemeral=True)
             return
        
        user_id = str(user.id)
        if user_id not in invites_data:
            invites_data[user_id] = {"regular": 0, "fake": 0, "bonus": 0, "leaves": 0}
            
        invites_data[user_id]["bonus"] += amount
        save_data('invites.json', invites_data)
        
        await interaction.response.send_message(f"✅ Added **{amount}** bonus chances to {user.mention}. Total Bonus: {invites_data[user_id]['bonus']}", ephemeral=True)

async def schedule_giveaway_end(message_id, delay):
    await asyncio.sleep(delay)
    await end_giveaway_logic(message_id)

async def end_giveaway_logic(message_id):
    message_id = str(message_id)
    if message_id not in giveaways_data or giveaways_data[message_id]["ended"]:
        return

    data = giveaways_data[message_id]
    channel = bot.get_channel(data["channel_id"])
    
    if channel:
        try:
            message = await channel.fetch_message(int(message_id))
            
            # Select winners
            participants = data["participants"]
            winners_count = data["winners"]
            
            if not participants:
                await message.reply("❌ **Giveaway Ended:** No one joined.")
                data["ended"] = True
                save_data('giveaways.json', giveaways_data)
                return

            # Logic for chances: Simple pool expansion (User ID * Chance)
            weighted_pool = []
            for uid in participants:
                # Base chance = 1
                chance = 1
                if uid in invites_data:
                    chance += invites_data[uid]["bonus"]
                
                # Check for negative?
                if chance < 1: chance = 1 
                
                # Add to pool
                weighted_pool.extend([uid] * chance)
            
            winners = []
            if len(participants) < winners_count:
                winners = participants # Everyone wins
            else:
                 try:
                     temp_pool = weighted_pool.copy()
                     for _ in range(winners_count):
                         if not temp_pool: break
                         winner = random.choice(temp_pool)
                         winners.append(winner)
                         temp_pool = [x for x in temp_pool if x != winner]
                 except:
                     winners = [random.choice(participants)]

            winners_mentions = ", ".join([f"<@{uid}>" for uid in winners])
            
            embed = message.embeds[0]
            embed.color = 0x2ECC71
            embed.title = "🎉 **GIVEAWAY ENDED** 🎉"
            embed.description = f"**Prize:** {data['prize']}\n**Winners:** {winners_mentions}"
            embed.set_footer(text="Ended")
            
            await message.edit(embed=embed, view=None) # Remove button
            await message.reply(f"🎉 **Congratulations** {winners_mentions}! You won **{data['prize']}**!")
            
            data["ended"] = True
            data["winners_list"] = winners
            save_data('giveaways.json', giveaways_data)

        except Exception as e:
            print(f"Error ending giveaway: {e}")

async def reroll_giveaway(interaction, message_id, winners_count):
    message_id = str(message_id)
    if message_id not in giveaways_data:
        await interaction.response.send_message("❌ Giveaway not found.", ephemeral=True)
        return

    data = giveaways_data[message_id]
    participants = data["participants"]
    
    if not participants:
        await interaction.response.send_message("❌ No participants to reroll.", ephemeral=True)
        return

    # Weighted Logic again
    weighted_pool = []
    for uid in participants:
        chance = 1
        if uid in invites_data:
            chance += invites_data[uid]["bonus"]
        if chance < 1: chance = 1 
        weighted_pool.extend([uid] * chance)
    
    winners = []
    temp_pool = weighted_pool.copy()
    
    for _ in range(winners_count):
        if not temp_pool: break
        winner = random.choice(temp_pool)
        winners.append(winner)
        temp_pool = [x for x in temp_pool if x != winner]

    winners_mentions = ", ".join([f"<@{uid}>" for uid in winners])
    await interaction.channel.send(f"🎉 **New Winner(s):** {winners_mentions}!")
    
    await interaction.response.send_message("✅ Rerolled.", ephemeral=True)


# --- Invite Tracking Events ---

@bot.event
async def on_invite_create(invite):
    if invite.guild.id not in invite_cache:
        invite_cache[invite.guild.id] = []
    # Refresh cache for this guild
    invite_cache[invite.guild.id] = await invite.guild.invites()

@bot.event
async def on_invite_delete(invite):
    if invite.guild.id in invite_cache:
        invite_cache[invite.guild.id] = await invite.guild.invites()

@bot.event
async def on_member_join(member):
    # Find inviter
    inviter = None
    try:
        current_invites = await member.guild.invites()
        cached_invites = invite_cache.get(member.guild.id, [])
        
        for invite in current_invites:
            for cached in cached_invites:
                if invite.code == cached.code and invite.uses > cached.uses:
                    inviter = invite.inviter
                    break
            if inviter: break
        
        invite_cache[member.guild.id] = current_invites
        
        if inviter:
            inviter_id = str(inviter.id)
            if inviter_id not in invites_data:
                invites_data[inviter_id] = {"regular": 0, "fake": 0, "bonus": 0, "leaves": 0}
            
            # Check for fake (account age < 3 days?)
            if (datetime.now(timezone.utc) - member.created_at).days < 3:
                invites_data[inviter_id]["fake"] += 1
            else:
                invites_data[inviter_id]["regular"] += 1
                
            save_data('invites.json', invites_data)
            
    except Exception as e:
        print(f"Error tracking invite: {e}")

@bot.event
async def on_member_remove(member):
    # Optional: Track leaves
    pass


# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Please create a .env file with your bot token.")
    else:
        bot.run(token)
