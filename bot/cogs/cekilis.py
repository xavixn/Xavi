import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import json
import os
from datetime import datetime, timezone, timedelta

CEKILIS_DB = os.path.join(os.path.dirname(__file__), "..", "data", "cekilisler.json")


def _load_cekilisler() -> dict:
    if os.path.exists(CEKILIS_DB):
        try:
            with open(CEKILIS_DB, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cekilisler(data: dict):
    with open(CEKILIS_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Cekilis(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Aktif çekilişleri tut: {message_id: task}
        self.aktif_cekilisler: dict[int, asyncio.Task] = {}

    async def cog_load(self):
        """Bot başlarken kayıtlı çekilişleri yeniden başlat."""
        await self.bot.wait_until_ready()
        await asyncio.sleep(2)  # Guild cache'in dolması için kısa bekle
        cekilisler = _load_cekilisler()
        for msg_id_str, veri in list(cekilisler.items()):
            msg_id = int(msg_id_str)
            bitis_ts = veri["bitis_timestamp"]
            kalan = bitis_ts - int(discord.utils.utcnow().timestamp())

            # Zaten bitmişse hemen bitir
            if kalan <= 0:
                kalan = 0

            try:
                kanal = self.bot.get_channel(veri["kanal_id"])
                if kanal is None:
                    kanal = await self.bot.fetch_channel(veri["kanal_id"])
                msg = await kanal.fetch_message(msg_id)
                baslatan = kanal.guild.get_member(veri["baslatan_id"])
            except Exception:
                cekilisler.pop(msg_id_str, None)
                continue

            task = asyncio.create_task(
                self._cekilis_bitir(
                    msg=msg,
                    odul=veri["odul"],
                    kazanan_sayisi=veri["kazanan_sayisi"],
                    baslatan=baslatan,
                    bitis_timestamp=bitis_ts,
                    sure_saniye=kalan
                )
            )
            self.aktif_cekilisler[msg_id] = task

        _save_cekilisler(cekilisler)

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

        # Saniyeye çevir (float hassasiyetiyle)
        sure_saniye = sure * 3600
        bitis = discord.utils.utcnow() + timedelta(seconds=sure_saniye)
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
        embed.set_footer(text="Nova Bot | Çekiliş Sistemi")
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)

        await interaction.response.send_message("✅ Çekiliş başlatıldı!", ephemeral=True)
        msg = await interaction.channel.send(content="🎉 **Çekiliş Başladı!** 🎉", embed=embed)
        await msg.add_reaction("🎉")

        # Çekilişi kaydet (bot restart'a karşı)
        cekilisler = _load_cekilisler()
        cekilisler[str(msg.id)] = {
            "kanal_id": interaction.channel.id,
            "odul": odul,
            "kazanan_sayisi": kazanan_sayisi,
            "baslatan_id": interaction.user.id,
            "bitis_timestamp": bitis_timestamp
        }
        _save_cekilisler(cekilisler)

        # Zamanlayıcı başlat
        task = asyncio.create_task(
            self._cekilis_bitir(
                msg=msg,
                odul=odul,
                kazanan_sayisi=kazanan_sayisi,
                baslatan=interaction.user,
                bitis_timestamp=bitis_timestamp,
                sure_saniye=sure_saniye
            )
        )
        self.aktif_cekilisler[msg.id] = task

    # ─── Çekiliş Bitirici ─────────────────────────────────────────────────────
    async def _cekilis_bitir(
        self,
        msg: discord.Message,
        odul: str,
        kazanan_sayisi: int,
        baslatan,
        bitis_timestamp: int,
        sure_saniye: float
    ):
        try:
            await asyncio.sleep(sure_saniye)
        except asyncio.CancelledError:
            return

        # Mesajı yenile
        try:
            msg = await msg.channel.fetch_message(msg.id)
        except discord.NotFound:
            self._temizle(msg.id)
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
            kazanan_mention = "Kimse katılmadı 😔"
        else:
            secilen = random.sample(katilimcilar, min(kazanan_sayisi, len(katilimcilar)))
            kazanan_mention = ", ".join(u.mention for u in secilen)

        # Embed güncelle
        embed = discord.Embed(
            title=f"🎁 Ödül: {odul}",
            color=0xFF4444,
            timestamp=discord.utils.utcnow()
        )
        baslatan_mention = baslatan.mention if baslatan else "Bilinmiyor"
        embed.description = (
            f"🏆 **Kazanan(lar):** {kazanan_mention}\n"
            f"👤 **Başlatan:** {baslatan_mention}\n"
            f"🗓️ **Bitiş Zamanı:** <t:{bitis_timestamp}:F>"
        )
        embed.set_footer(text="Nova Bot | Çekiliş Sistemi")
        embed.set_thumbnail(url=msg.guild.icon.url if msg.guild.icon else None)

        await msg.edit(content="🎉 **Çekiliş Sona Erdi!** 🎉", embed=embed)

        if len(katilimcilar) > 0:
            await msg.channel.send(
                f"🎊 Tebrikler {kazanan_mention}! **{odul}** ödülünü kazandınız!"
            )

        self._temizle(msg.id)

    def _temizle(self, msg_id: int):
        """Aktif listeden ve JSON'dan kaldır."""
        self.aktif_cekilisler.pop(msg_id, None)
        cekilisler = _load_cekilisler()
        cekilisler.pop(str(msg_id), None)
        _save_cekilisler(cekilisler)

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
        self._temizle(mid)

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
