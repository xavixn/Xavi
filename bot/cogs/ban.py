import discord
from discord import app_commands
from discord.ext import commands
import os

# Sadece bu ID'ler /ban komutunu kullanabilir
ALLOWED_BAN_IDS = {
    1080510912903008388,
    1363206369993429203,
}


class Ban(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Bir kullanıcıyı sunucudan banlar. (Etiket veya ID)")
    @app_commands.describe(
        kullanici="Banlanacak kullanıcı (etiketle)",
        kullanici_id="Banlanacak kullanıcının ID'si (sunucuda olmayan biri için)",
        sebep="Ban sebebi (opsiyonel)",
        sure="Mesaj silme süresi (gün, 0-7)"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        kullanici: discord.Member = None,
        kullanici_id: str = None,
        sebep: str = "Sebep belirtilmedi",
        sure: int = 0
    ):
        # Sadece izinli ID'ler kullanabilir
        if interaction.user.id not in ALLOWED_BAN_IDS:
            return await interaction.response.send_message(
                "❌ Bu komutu kullanma yetkin yok.",
                ephemeral=True
            )

        # En az biri girilmeli
        if kullanici is None and kullanici_id is None:
            return await interaction.response.send_message(
                "❌ Bir kullanıcı etiketle ya da ID gir.",
                ephemeral=True
            )

        # Botun ban yetkisi var mı?
        if not interaction.guild.me.guild_permissions.ban_members:
            return await interaction.response.send_message(
                "❌ Botun ban yetkisi yok!",
                ephemeral=True
            )

        # Mesaj silme süresi 0-7 arasında olmalı
        sure = max(0, min(7, sure))

        # ── Etiketli kullanıcı ──────────────────────────────────────────────
        if kullanici:
            hedef = kullanici

            # Kendini banlayamaz
            if hedef.id == interaction.user.id:
                return await interaction.response.send_message(
                    "❌ Kendini banlayamazsın.", ephemeral=True
                )

            # Botu banlayamaz
            if hedef.id == interaction.guild.me.id:
                return await interaction.response.send_message(
                    "❌ Botu banlayamazsın.", ephemeral=True
                )

            # Hiyerarşi kontrolü
            if hedef.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
                return await interaction.response.send_message(
                    "❌ Kendi rolünden üst veya eşit birisini banlayamazsın.",
                    ephemeral=True
                )

            if hedef.top_role >= interaction.guild.me.top_role:
                return await interaction.response.send_message(
                    "❌ Botun rolünden üst veya eşit birisini banlayamam.",
                    ephemeral=True
                )

            try:
                await hedef.ban(
                    reason=f"{interaction.user} | {sebep}",
                    delete_message_days=sure
                )
            except discord.Forbidden:
                return await interaction.response.send_message(
                    "❌ Bu kullanıcıyı banlama yetkim yok.", ephemeral=True
                )

            embed = discord.Embed(
                title="🔨 Kullanıcı Banlandı",
                color=0xFF0000,
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=hedef.display_avatar.url)
            embed.add_field(name="👤 Kullanıcı", value=f"{hedef.mention} (`{hedef.id}`)", inline=True)
            embed.add_field(name="🛡️ İşlemi Yapan", value=interaction.user.mention, inline=True)
            embed.add_field(name="📝 Sebep", value=sebep, inline=False)
            if sure > 0:
                embed.add_field(name="🗑️ Mesaj Silme", value=f"Son {sure} günün mesajları silindi", inline=False)
            embed.set_footer(text="303 Bot | Ban Sistemi")
            return await interaction.response.send_message(embed=embed)

        # ── ID ile ban (sunucuda olmayan kullanıcı) ──────────────────────────
        if not kullanici_id.isdigit():
            return await interaction.response.send_message(
                "❌ Geçersiz kullanıcı ID'si! Sadece sayısal bir ID girin.",
                ephemeral=True
            )

        user_obj = discord.Object(id=int(kullanici_id))

        try:
            await interaction.guild.ban(
                user_obj,
                reason=f"{interaction.user} | {sebep}",
                delete_message_days=sure
            )
        except discord.NotFound:
            return await interaction.response.send_message(
                f"❌ `{kullanici_id}` ID'li kullanıcı bulunamadı.", ephemeral=True
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ Bu kullanıcıyı banlama yetkim yok.", ephemeral=True
            )

        embed = discord.Embed(
            title="🔨 Kullanıcı Banlandı",
            color=0xFF0000,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="👤 Kullanıcı ID", value=f"`{kullanici_id}`", inline=True)
        embed.add_field(name="🛡️ İşlemi Yapan", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Sebep", value=sebep, inline=False)
        if sure > 0:
            embed.add_field(name="🗑️ Mesaj Silme", value=f"Son {sure} günün mesajları silindi", inline=False)
        embed.set_footer(text="303 Bot | Ban Sistemi")
        await interaction.response.send_message(embed=embed)

    @ban.error
    async def ban_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Bu komutu kullanmak için **Ban Members** yetkisine ihtiyacın var.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Ban(bot))
