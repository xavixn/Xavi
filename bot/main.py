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
    cogs = ["cogs.ticket", "cogs.stat", "cogs.unban", "cogs.restart", "cogs.cekilis", "cogs.clear", "cogs.jail", "cogs.rol", "cogs.ban"]
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

    # ─── Ses kanalına bağlan ──────────────────────────────────────────────────
    await asyncio.sleep(3)
    kanal_adi = os.getenv("VOICE_CHANNEL_NAME", ".gg/novapack")
    for guild in bot.guilds:
        kanal = discord.utils.get(guild.voice_channels, name=kanal_adi)
        if kanal:
            try:
                if guild.voice_client:
                    await guild.voice_client.disconnect(force=True)
                    await asyncio.sleep(2)
                vc = await kanal.connect(timeout=60, reconnect=True, self_deaf=True, self_mute=True)
                print(f"✅ {guild.name} → '{kanal_adi}' ses kanalına bağlanıldı (mute+deaf).")
            except Exception as e:
                print(f"❌ {guild.name} → Ses kanalına bağlanılamadı: {e}")
        else:
            print(f"⚠️ {guild.name} → '{kanal_adi}' adlı ses kanalı bulunamadı.")

bot.run(TOKEN)
