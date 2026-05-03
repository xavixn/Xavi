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


class NovaBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Bot başlarken bir kez çalışır — cog yükleme buraya."""
        cogs = [
            "cogs.ticket",
            "cogs.stat",
            "cogs.unban",
            "cogs.restart",
            "cogs.cekilis",
            "cogs.clear",
            "cogs.jail",
            "cogs.rol",
            "cogs.ban",
            "cogs.untimeout",
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ {cog} yüklendi.")
            except Exception as e:
                print(f"❌ {cog} yüklenemedi: {e}")

        try:
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} slash komutu senkronize edildi.")
        except Exception as e:
            print(f"❌ Komut senkronizasyon hatası: {e}")

    async def on_ready(self):
        print(f"✅ {self.user} olarak giriş yapıldı!")

        # ─── Ses kanalına bağlan (sadece local/bat ile çalışırken) ───────────
        if os.getenv("RAILWAY_ENVIRONMENT") is None:
            await asyncio.sleep(3)
            kanal_adi = os.getenv("VOICE_CHANNEL_NAME", ".gg/novapack")
            for guild in self.guilds:
                kanal = discord.utils.get(guild.voice_channels, name=kanal_adi)
                if kanal:
                    try:
                        if guild.voice_client:
                            await guild.voice_client.disconnect(force=True)
                            await asyncio.sleep(2)
                        await kanal.connect(
                            timeout=60, reconnect=True, self_deaf=True, self_mute=True
                        )
                        print(f"✅ {guild.name} → '{kanal_adi}' ses kanalına bağlanıldı.")
                    except Exception as e:
                        print(f"❌ {guild.name} → Ses kanalına bağlanılamadı: {e}")
                else:
                    print(f"⚠️ {guild.name} → '{kanal_adi}' adlı ses kanalı bulunamadı.")


bot = NovaBot()
bot.run(TOKEN)
