import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
from datetime import datetime, timezone, timedelta


class Cekilis(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Aktif çekilişleri tut: {message_id: task}
        self.aktif_cekilisler: dict[int, asyncio.Task] = {}

    # ─── /cekilis komutu ──────────────────────────────────────────────────────
    @app_commands.command(name="cekilis", description="Yeni bir çekiliş başlatır.")
    @app_commands.describe(
        odul="Çekiliş ödülü (örn: 2X RX7)",
        sure="Süre saat cinsinden (örn: 1 = 1 saat, 0.5 = 30 dakika)",
        kazanan_sayisi="Kaç kişi kazanacak (varsayılan: 1)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def cekilis(
        self,
        interaction: discord.Interaction,
        odul: str,
        sure: float,
        kazanan_sayisi: int = 1
    ):
        if sure <= 0:
            return await interaction.response.send_message(
                "❌ Süre 0'dan büyük olmalı.", ephemeral=True
            )
        if kazanan_sayisi <= 0:
            return await interaction.response.send_message(
                "❌ Kazanan sayısı en az 1 olmalı.", ephemeral=True
            )

        # Saati dakikaya çevir
        sure_dakika = int(sure * 60)
        bitis = discord.utils.utcnow() + timedelta(minutes=sure_dakika)
        bitis_timestamp = int(bitis.timestamp())

        embed = discord.Embed(
            title=f"🎁 Ödül: {odul}",
            color=0x5865F2,
            timestamp=bitis
        )
        embed.description = (
            f"🎉 Katılmak için **🎉** reaksiyonuna tıkla!\n\n"
            f"🏆 **Kazanan Sayısı:** {kazanan_sayisi}\n"
            f"👤 **Başlatan:** {interaction.user.mention}\n"
            f"🗓️ **Bitiş Zamanı:** <t:{bitis_timestamp}:F> (<t:{bitis_timestamp}:R>)"
        )
        embed.set_footer(text=f"Bitiş Zamanı: •")
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)

        await interaction.response.send_message("✅ Çekiliş başlatıldı!", ephemeral=True)
        msg = await interaction.channel.send(content="🎉 **Çekiliş Başladı!** 🎉", embed=embed)
        await msg.add_reaction("🎉")

        # Zamanlayıcı başlat
        task = asyncio.create_task(
            self._cekilis_bitir(
                msg=msg,
                odul=odul,
                kazanan_sayisi=kazanan_sayisi,
                baslatan=interaction.user,
                bitis_timestamp=bitis_timestamp,
                sure_saniye=sure_dakika * 60
            )
        )
        self.aktif_cekilisler[msg.id] = task

    # ─── Çekiliş Bitirici ─────────────────────────────────────────────────────
    async def _cekilis_bitir(
        self,
        msg: discord.Message,
        odul: str,
        kazanan_sayisi: int,
        baslatan: discord.Member,
        bitis_timestamp: int,
        sure_saniye: int
    ):
        await asyncio.sleep(sure_saniye)

        # Mesajı yenile
        try:
            msg = await msg.channel.fetch_message(msg.id)
        except discord.NotFound:
            return

        # 🎉 reaksiyonunu al
        katilimcilar = []
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        katilimcilar.append(user)
                break

        # Kazananları seç
        if len(katilimcilar) == 0:
            kazananlar_str = "Kimse katılmadı 😔"
            kazanan_mention = "Yok"
        else:
            secilen = random.sample(katilimcilar, min(kazanan_sayisi, len(katilimcilar)))
            kazananlar_str = ", ".join(u.mention for u in secilen)
            kazanan_mention = kazananlar_str

        # Embed güncelle
        embed = discord.Embed(
            title=f"🎁 Ödül: {odul}",
            color=0xFF4444,
            timestamp=discord.utils.utcnow()
        )
        embed.description = (
            f"🏆 **Kazanan(lar):** {kazanan_mention}\n"
            f"👤 **Başlatan:** {baslatan.mention}\n"
            f"🗓️ **Bitiş Zamanı:** <t:{bitis_timestamp}:F>"
        )
        embed.set_footer(text=f"Bitiş Zamanı: • {discord.utils.utcnow().strftime('%d.%m.%Y %H:%M')}")
        embed.set_thumbnail(url=msg.guild.icon.url if msg.guild.icon else None)

        await msg.edit(content="🎉 **Çekiliş Sona Erdi!** 🎉", embed=embed)

        if len(katilimcilar) > 0:
            await msg.channel.send(
                f"🎊 Tebrikler {kazananlar_str}! **{odul}** ödülünü kazandınız!"
            )

        # Aktif listeden kaldır
        self.aktif_cekilisler.pop(msg.id, None)

    # ─── /cekilis-iptal komutu ────────────────────────────────────────────────
    @app_commands.command(name="cekilis-iptal", description="Aktif bir çekilişi iptal eder.")
    @app_commands.describe(mesaj_id="İptal edilecek çekilişin mesaj ID'si")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def cekilis_iptal(self, interaction: discord.Interaction, mesaj_id: str):
        if not mesaj_id.isdigit():
            return await interaction.response.send_message(
                "❌ Geçersiz mesaj ID'si.", ephemeral=True
            )

        mid = int(mesaj_id)
        task = self.aktif_cekilisler.get(mid)
        if not task:
            return await interaction.response.send_message(
                "❌ Bu ID'ye ait aktif çekiliş bulunamadı.", ephemeral=True
            )

        task.cancel()
        self.aktif_cekilisler.pop(mid, None)

        try:
            msg = await interaction.channel.fetch_message(mid)
            embed = msg.embeds[0] if msg.embeds else None
            if embed:
                embed.color = 0x808080
                embed.description = "❌ Bu çekiliş iptal edildi."
                await msg.edit(content="~~🎉 Çekiliş~~", embed=embed)
        except Exception:
            pass

        await interaction.response.send_message("✅ Çekiliş iptal edildi.", ephemeral=True)

    # ─── /cekilis-tekrar komutu ───────────────────────────────────────────────
    @app_commands.command(name="cekilis-tekrar", description="Bitmiş bir çekilişi yeniden çeker.")
    @app_commands.describe(mesaj_id="Yeniden çekilecek mesajın ID'si")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def cekilis_tekrar(self, interaction: discord.Interaction, mesaj_id: str):
        if not mesaj_id.isdigit():
            return await interaction.response.send_message(
                "❌ Geçersiz mesaj ID'si.", ephemeral=True
            )

        try:
            msg = await interaction.channel.fetch_message(int(mesaj_id))
        except discord.NotFound:
            return await interaction.response.send_message(
                "❌ Mesaj bulunamadı.", ephemeral=True
            )

        katilimcilar = []
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        katilimcilar.append(user)
                break

        if not katilimcilar:
            return await interaction.response.send_message(
                "❌ Katılımcı bulunamadı.", ephemeral=True
            )

        kazanan = random.choice(katilimcilar)
        await interaction.response.send_message(
            f"🎊 Yeni kazanan: {kazanan.mention}! Tebrikler!"
        )

    @cekilis.error
    @cekilis_iptal.error
    @cekilis_tekrar.error
    async def cekilis_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Bu komutu kullanmak için **Manage Guild** yetkisine ihtiyacın var.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Cekilis(bot))
