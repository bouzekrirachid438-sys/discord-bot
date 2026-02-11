# Karys Shop Discord Bot

A Discord bot for Karys Shop that displays Valorant Points pricing and handles orders.

## Features

- 📋 Display Valorant Points price list with regional pricing (USD and DH)
- 📦 Check stock availability
- 🛒 Order Valorant Points
- 💰 Multiple payment methods support
- ⚡ Fast delivery information

## Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and name it "Karys Shop"
3. Go to the "Bot" section
4. Click "Add Bot"
5. Copy the bot token
6. Enable "Message Content Intent" under "Privileged Gateway Intents"

### 3. Configure Bot Token

1. Copy `env_example.txt` to `.env`
2. Replace `your_bot_token_here` with your actual bot token

### 4. Invite Bot to Server

1. Go to "OAuth2" > "URL Generator"
2. Select scopes: `bot` and `applications.commands`
3. Select bot permissions: `Send Messages`, `Embed Links`, `Read Message History`
4. Copy the generated URL and open it in your browser
5. Select your server and authorize

### 5. Run the Bot

```bash
python bot.py
```

## Commands

- `!prices` - View Valorant Points price list
- `!stock` - Check stock availability
- `!order [amount]` - Order Valorant Points (e.g., `!order 10000`)
- `!help_shop` - Show available commands

## Customization

You can modify the price list in `bot.py` by editing the `PRICE_LIST` dictionary. You can also customize the shop information in `config.json`.

## License

This project is for Karys Shop use only.
