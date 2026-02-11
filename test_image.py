import os
import sys
import io
import discord
from dotenv import load_dotenv

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

# Test if image can be loaded
bot_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(bot_dir)
image_path = os.path.join(parent_dir, "IMG", "karys.png")

print("=" * 50)
print("Testing Image Path")
print("=" * 50)
print(f"Bot directory: {bot_dir}")
print(f"Parent directory: {parent_dir}")
print(f"Image path: {image_path}")
print(f"Image exists: {os.path.exists(image_path)}")

if os.path.exists(image_path):
    file_size = os.path.getsize(image_path) / (1024 * 1024)  # MB
    print(f"Image size: {file_size:.2f} MB")
    
    # Try to create Discord File object
    try:
        file = discord.File(image_path, filename="karys.png")
        print("✅ Discord File object created successfully!")
        print(f"File object: {file}")
    except Exception as e:
        print(f"❌ Error creating Discord File: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ Image not found!")

print("=" * 50)
