import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

# ─── Bot Ayarları ─────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ─── Cog'ları Yükle ───────────────────────────────────────────────────────────
async def load_cogs():
    cogs = ["cogs.ticket", "cogs.stat", "cogs.unban", "cogs.restart", "cogs.cekilis", "cogs.clear", "cogs.jail", "cogs.rol", "cogs.ban", "cogs.untimeout"]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ {cog} yüklendi.")
        except Exception as e:
            print(f"❌ {cog} yüklenemedi: {e}")

@bot.event
async def on_ready():
    await load_cogs()
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} slash komutu senkronize edildi.")
    except Exception as e:
        print(f"❌ Komut senkronizasyon hatası: {e}")
    print(f"✅ {bot.user} olarak giriş yapıldı!")

bot.run(TOKEN)
