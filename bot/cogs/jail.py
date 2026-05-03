import discord
from discord.ext import commands
import os

# Korunan kullanıcılar - sunucudan atılmaz
PROTECTED_IDS = set(
    uid.strip()
    for uid in os.getenv("PROTECTED_IDS", "").split(",")
    if uid.strip()
)


class Jail(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Korunan kullanıcıları atla
        if str(after.id) in PROTECTED_IDS:
            return

        # Rol değişikliği var mı?
        eklenen_roller = set(after.roles) - set(before.roles)
        if not eklenen_roller:
            return

        # Kimin rol verdiğini bul (audit log)
        veren_kisi = None
        try:
            async for entry in after.guild.audit_logs(
                limit=5,
                action=discord.AuditLogAction.member_role_update
            ):
                if entry.target.id == after.id:
                    veren_kisi = entry.user
                    break
        except discord.Forbidden:
            pass

        # Rol veren kişi korumalıysa işlem yapma
        if veren_kisi and str(veren_kisi.id) in PROTECTED_IDS:
            return

        # Rol veren kişi botsa işlem yapma
        if veren_kisi and veren_kisi.bot:
            return

        # Eklenen rollerin herhangi biri, rol veren kişinin en yüksek rolünden üstte mi?
        if veren_kisi is None:
            return

        veren_max_pos = veren_kisi.top_role.position

        for rol in eklenen_roller:
            if rol.position >= veren_max_pos:
                # Kendi üstündeki veya eşit bir rol vermeye çalıştı → kick
                try:
                    await after.kick(
                        reason=f"⚠️ Jail: {veren_kisi} tarafından yetkisiz rol atandı ({rol.name})"
                    )
                except discord.Forbidden:
                    pass

                # Log mesajı gönder (ilk bulduğu text kanalına)
                log_kanalı = discord.utils.find(
                    lambda c: c.permissions_for(after.guild.me).send_messages,
                    after.guild.text_channels
                )
                if log_kanalı:
                    embed = discord.Embed(
                        title="⚠️ Jail Sistemi — Yetkisiz Rol",
                        color=0xFF0000,
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(
                        name="👤 Atılan Kullanıcı",
                        value=f"{after.mention} (`{after.id}`)",
                        inline=True
                    )
                    embed.add_field(
                        name="🛡️ Rol Veren",
                        value=f"{veren_kisi.mention} (`{veren_kisi.id}`)",
                        inline=True
                    )
                    embed.add_field(
                        name="🏷️ Yetkisiz Rol",
                        value=f"{rol.mention} (Pozisyon: {rol.position})",
                        inline=False
                    )
                    embed.set_footer(text="Nova Bot | Jail Sistemi")
                    await log_kanalı.send(embed=embed)

                return  # İlk ihlalde kick yeterli


async def setup(bot: commands.Bot):
    await bot.add_cog(Jail(bot))
