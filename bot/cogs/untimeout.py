import discord
from discord import app_commands
from discord.ext import commands


class Untimeout(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="untimeout", description="Bir kullanıcının timeout'unu kaldırır.")
    @app_commands.describe(
        kullanici="Timeout'u kaldırılacak kullanıcı",
        sebep="Sebep (opsiyonel)"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(
        self,
        interaction: discord.Interaction,
        kullanici: discord.Member,
        sebep: str = "Sebep belirtilmedi"
    ):
        # Botun yetkisi var mı?
        if not interaction.guild.me.guild_permissions.moderate_members:
            return await interaction.response.send_message(
                "❌ Botun timeout kaldırma yetkisi yok!", ephemeral=True
            )

        # Zaten timeout'ta değil mi?
        if not kullanici.is_timed_out():
            return await interaction.response.send_message(
                f"❌ {kullanici.mention} zaten timeout'ta değil.", ephemeral=True
            )

        try:
            await kullanici.timeout(None, reason=f"{interaction.user} | {sebep}")
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ Bu kullanıcının timeout'unu kaldırma yetkim yok.", ephemeral=True
            )

        embed = discord.Embed(
            title="🔊 Timeout Kaldırıldı",
            color=0x00FF88,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=kullanici.display_avatar.url)
        embed.add_field(name="👤 Kullanıcı", value=f"{kullanici.mention} (`{kullanici.id}`)", inline=True)
        embed.add_field(name="🛡️ İşlemi Yapan", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Sebep", value=sebep, inline=False)
        embed.set_footer(text="Nova Bot | Untimeout Sistemi")

        await interaction.response.send_message(embed=embed)

    @untimeout.error
    async def untimeout_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Bu komutu kullanmak için **Moderate Members** yetkisine ihtiyacın var.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Untimeout(bot))
