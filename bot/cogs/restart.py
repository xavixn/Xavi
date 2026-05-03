import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import subprocess
import sys
import os


class Restart(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="restart", description="Botu yeniden başlatır.")
    @app_commands.checks.has_permissions(administrator=True)
    async def restart(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔄 Bot Yeniden Başlatılıyor",
            description="Bot **5-10 saniye** içinde tekrar aktif olacak...",
            color=0xFFA500,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="Nova Bot | Restart")
        await interaction.response.send_message(embed=embed)

        # Botu kapat ve yeni bir process olarak yeniden başlat
        script = os.path.abspath(sys.argv[0])
        python = sys.executable

        async def do_restart():
            await asyncio.sleep(2)
            await self.bot.close()
            # Mevcut process'ten bağımsız yeni process başlat
            subprocess.Popen(
                [python, script],
                cwd=os.path.dirname(script),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                if sys.platform == "win32" else 0
            )

        asyncio.create_task(do_restart())

    @restart.error
    async def restart_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Bu komutu kullanmak için **Administrator** yetkisine ihtiyacın var.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Restart(bot))
