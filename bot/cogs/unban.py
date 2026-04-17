import discord
from discord import app_commands
from discord.ext import commands


class Unban(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="unban", description="Bir kullanıcının banını kaldırır.")
    @app_commands.describe(
        kullanici_id="Banı kaldırılacak kullanıcının ID'si",
        sebep="Unban sebebi (opsiyonel)"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(
        self,
        interaction: discord.Interaction,
        kullanici_id: str,
        sebep: str = "Sebep belirtilmedi"
    ):
        # ID sadece rakam olmalı
        if not kullanici_id.isdigit():
            return await interaction.response.send_message(
                "❌ Geçersiz kullanıcı ID'si! Sadece sayısal bir ID girin.",
                ephemeral=True
            )

        # Bot'un yetkisi var mı?
        if not interaction.guild.me.guild_permissions.ban_members:
            return await interaction.response.send_message(
                "❌ Botun ban kaldırma yetkisi yok!",
                ephemeral=True
            )

        # Banlı kullanıcıları getir
        try:
            ban_entry = await interaction.guild.fetch_ban(discord.Object(id=int(kullanici_id)))
        except discord.NotFound:
            return await interaction.response.send_message(
                f"❌ `{kullanici_id}` ID'li kullanıcı bu sunucuda banlı değil.",
                ephemeral=True
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ Ban listesine erişim iznim yok.",
                ephemeral=True
            )

        # Unban işlemi
        try:
            await interaction.guild.unban(ban_entry.user, reason=sebep)
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ Kullanıcının banını kaldırma yetkim yok.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="🔓 Kullanıcı Unban Edildi",
            color=0x00FF88,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=ban_entry.user.display_avatar.url)
        embed.add_field(
            name="👤 Kullanıcı",
            value=f"{ban_entry.user} (`{kullanici_id}`)",
            inline=True
        )
        embed.add_field(
            name="🛡️ İşlemi Yapan",
            value=str(interaction.user),
            inline=True
        )
        embed.add_field(name="📝 Sebep", value=sebep, inline=False)
        embed.set_footer(text="303 Bot | Unban Sistemi")

        await interaction.response.send_message(embed=embed)

    @unban.error
    async def unban_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Bu komutu kullanmak için **Ban Members** yetkisine ihtiyacın var.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Unban(bot))
