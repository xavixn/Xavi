import discord
from discord import app_commands
from discord.ext import commands


class Clear(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="clear", description="Kanaldan mesaj siler. (varsayılan: 20)")
    @app_commands.describe(miktar="Silinecek mesaj sayısı (varsayılan: 20, max: 100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, miktar: int = 20):
        if miktar < 1 or miktar > 100:
            return await interaction.response.send_message(
                "❌ Miktar 1 ile 100 arasında olmalı.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        silinen = await interaction.channel.purge(limit=miktar)

        embed = discord.Embed(
            title="🗑️ Mesajlar Silindi",
            description=f"**{len(silinen)}** mesaj başarıyla silindi.",
            color=0x00FF88,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"İşlemi yapan: {interaction.user} | Nova Bot")

        await interaction.followup.send(embed=embed, ephemeral=True)

    @clear.error
    async def clear_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Bu komutu kullanmak için **Manage Messages** yetkisine ihtiyacın var.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Clear(bot))
