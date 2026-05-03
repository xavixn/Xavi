import discord
from discord import app_commands
from discord.ext import commands
import os

PROTECTED_IDS = set(
    uid.strip()
    for uid in os.getenv("PROTECTED_IDS", "").split(",")
    if uid.strip()
)


class Rol(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ─── /rol-ver ─────────────────────────────────────────────────────────────
    @app_commands.command(name="rol-ver", description="Bir kullanıcıya rol verir.")
    @app_commands.describe(
        kullanici="Rol verilecek kullanıcı",
        rol="Verilecek rol"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rol_ver(
        self,
        interaction: discord.Interaction,
        kullanici: discord.Member,
        rol: discord.Role
    ):
        # Korumalı kullanıcıya herkes rol verebilir ama jail tetiklemez
        # Rol veren kişi korumalı değilse kendi üstündeki rolü veremez
        if str(interaction.user.id) not in PROTECTED_IDS:
            if rol.position >= interaction.user.top_role.position:
                return await interaction.response.send_message(
                    f"❌ Kendi rolünden üst veya eşit bir rolü (`{rol.name}`) veremezsin.",
                    ephemeral=True
                )

        # Botun rolü verebilecek pozisyonu var mı?
        if rol.position >= interaction.guild.me.top_role.position:
            return await interaction.response.send_message(
                f"❌ Botun rolü (`{rol.name}`) verebilecek yetkisi yok. Bot rolü bu rolden üstte olmalı.",
                ephemeral=True
            )

        # Zaten rolü var mı?
        if rol in kullanici.roles:
            return await interaction.response.send_message(
                f"❌ {kullanici.mention} zaten `{rol.name}` rolüne sahip.",
                ephemeral=True
            )

        await kullanici.add_roles(rol, reason=f"{interaction.user} tarafından rol verildi.")

        embed = discord.Embed(
            title="✅ Rol Verildi",
            color=rol.color if rol.color != discord.Color.default() else 0x00FF88,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="👤 Kullanıcı", value=kullanici.mention, inline=True)
        embed.add_field(name="🏷️ Rol", value=rol.mention, inline=True)
        embed.add_field(name="🛡️ İşlemi Yapan", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Nova Bot | Rol Sistemi")
        await interaction.response.send_message(embed=embed)

    @rol_ver.error
    async def rol_ver_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Bu komutu kullanmak için **Manage Roles** yetkisine ihtiyacın var.",
                ephemeral=True
            )

    # ─── /rol-al ──────────────────────────────────────────────────────────────
    @app_commands.command(name="rol-al", description="Bir kullanıcıdan rol alır.")
    @app_commands.describe(
        kullanici="Rolü alınacak kullanıcı",
        rol="Alınacak rol"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rol_al(
        self,
        interaction: discord.Interaction,
        kullanici: discord.Member,
        rol: discord.Role
    ):
        # Korumalı değilse kendi üstündeki rolü alamaz
        if str(interaction.user.id) not in PROTECTED_IDS:
            if rol.position >= interaction.user.top_role.position:
                return await interaction.response.send_message(
                    f"❌ Kendi rolünden üst veya eşit bir rolü (`{rol.name}`) alamazsın.",
                    ephemeral=True
                )

        # Botun rolü alabileceği pozisyon var mı?
        if rol.position >= interaction.guild.me.top_role.position:
            return await interaction.response.send_message(
                f"❌ Botun rolü (`{rol.name}`) alabileceği yetkisi yok.",
                ephemeral=True
            )

        # Kullanıcıda bu rol var mı?
        if rol not in kullanici.roles:
            return await interaction.response.send_message(
                f"❌ {kullanici.mention} zaten `{rol.name}` rolüne sahip değil.",
                ephemeral=True
            )

        await kullanici.remove_roles(rol, reason=f"{interaction.user} tarafından rol alındı.")

        embed = discord.Embed(
            title="🗑️ Rol Alındı",
            color=0xFF4444,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="👤 Kullanıcı", value=kullanici.mention, inline=True)
        embed.add_field(name="🏷️ Rol", value=rol.mention, inline=True)
        embed.add_field(name="🛡️ İşlemi Yapan", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Nova Bot | Rol Sistemi")
        await interaction.response.send_message(embed=embed)

    @rol_al.error
    async def rol_al_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Bu komutu kullanmak için **Manage Roles** yetkisine ihtiyacın var.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Rol(bot))
