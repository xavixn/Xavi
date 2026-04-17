import discord
from discord import app_commands
from discord.ext import commands
from utils.db import get_stats, add_message, add_voice
import datetime
from collections import defaultdict


class Stat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Ses kanalı giriş zamanlarını tut: {(user_id, guild_id): datetime}
        self.voice_sessions: dict[tuple, datetime.datetime] = {}

    # ─── /stat Komutu ─────────────────────────────────────────────────────────
    @app_commands.command(name="stat", description="Sunucudaki istatistiklerini gösterir.")
    @app_commands.describe(kullanici="İstatistiklerini görmek istediğin kullanıcı (boş = kendin)")
    async def stat(
        self,
        interaction: discord.Interaction,
        kullanici: discord.Member = None
    ):
        await interaction.response.defer()

        hedef = kullanici or interaction.user
        member = interaction.guild.get_member(hedef.id)

        if not member:
            return await interaction.followup.send("❌ Bu kullanıcı sunucuda bulunamadı.", ephemeral=True)

        stats = get_stats(str(hedef.id), str(interaction.guild.id))

        # Katılma tarihi
        katilma_gun = (discord.utils.utcnow() - member.joined_at).days if member.joined_at else 0

        # Renk
        color = member.color if member.color != discord.Color.default() else discord.Color.blurple()

        # Ses ve mesaj aktivitesi hesaplama
        ses_haftalik_saat = stats['voice_week'] // 60
        ses_haftalik_dakika = stats['voice_week'] % 60
        ses_gunluk_saat = stats['voice_today'] // 60
        ses_gunluk_dakika = stats['voice_today'] % 60

        # Kanal istatistikleri (en çok mesaj atılan kanallar)
        kanal_mesajlari = self._get_channel_stats(str(hedef.id), str(interaction.guild.id))
        en_cok_ses = self._get_top_voice_channels(member)
        en_cok_mesaj_kanallari = self._get_top_message_channels(str(hedef.id), str(interaction.guild.id))

        embed = discord.Embed(
            title=f"{member.guild.name} | İstatistik Bilgileri",
            description=f"( @Support ) kullanıcısının detaylı sunucu verileri aşağıda belirtilmiştir.",
            color=color,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=hedef.display_avatar.url)

        # Kullanıcı Bilgisi
        embed.add_field(
            name="👤 Kullanıcı Bilgisi",
            value=(
                f"• **Hesap:** {hedef.mention}\n"
                f"• **Kullanıcı ID:** {hedef.id}\n"
                f"• **Katılım Tarihi:** {katilma_gun} gün önce"
            ),
            inline=False
        )

        # Toplam İstatistikler
        toplam_ses_saat = stats['voice_minutes'] // 60
        toplam_ses_dakika = stats['voice_minutes'] % 60
        embed.add_field(
            name="📊 Toplam İstatistikler",
            value=(
                f"• **Toplam Ses:** {toplam_ses_saat} Saat, {toplam_ses_dakika} Dakika\n"
                f"• **Toplam Mesaj:** {stats['messages']} mesaj"
            ),
            inline=False
        )

        # Ses Aktivitesi
        embed.add_field(
            name=f"{member.name} Ses Aktivitesi",
            value=(
                f"• **Haftalık:** {ses_haftalik_saat} saat, {ses_haftalik_dakika} dakika {ses_haftalik_saat * 60 + ses_haftalik_dakika} saniye\n"
                f"• **Günlük:** {ses_gunluk_saat} dakika {ses_gunluk_dakika} saniye"
            ),
            inline=False
        )

        # Mesaj Aktivitesi
        embed.add_field(
            name=f"{member.name} Mesaj Aktivitesi",
            value=(
                f"• **Haftalık:** {stats['messages_week']} mesaj\n"
                f"• **Günlük:** {stats['messages_today']} mesaj"
            ),
            inline=False
        )

        # Kanal İstatistikleri - En çok ses aktifliği
        if en_cok_ses:
            ses_kanallari_str = "\n".join([
                f"🔊 | {emoji} | **{kanal}:** {sure}"
                for kanal, sure, emoji in en_cok_ses[:5]
            ])
            embed.add_field(
                name="# Kanal İstatistikleri",
                value=f"**En çok ses aktifliği:**\n{ses_kanallari_str}",
                inline=False
            )

        # En çok mesaj aktifliği
        if en_cok_mesaj_kanallari:
            mesaj_kanallari_str = "\n".join([
                f"# *{kanal}*: **{mesaj} mesaj**"
                for kanal, mesaj in en_cok_mesaj_kanallari[:5]
            ])
            embed.add_field(
                name="En çok mesaj aktifliği:",
                value=mesaj_kanallari_str,
                inline=False
            )

        embed.set_footer(text="Kullanıcı İstatistikleri")

        await interaction.followup.send(embed=embed)

    # ─── Mesaj Sayacı ─────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return
        add_message(str(message.author.id), str(message.guild.id))

    # ─── Ses Süresi Takibi ────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        key = (member.id, member.guild.id)

        # Kanala girdi
        if before.channel is None and after.channel is not None:
            self.voice_sessions[key] = datetime.datetime.utcnow()

        # Kanaldan çıktı
        elif before.channel is not None and after.channel is None:
            start = self.voice_sessions.pop(key, None)
            if start:
                dakika = int((datetime.datetime.utcnow() - start).total_seconds() / 60)
                if dakika > 0:
                    add_voice(str(member.id), str(member.guild.id), dakika)

    def _get_channel_stats(self, user_id: str, guild_id: str):
        """Kullanıcının kanal bazlı mesaj istatistiklerini döndürür"""
        # Bu fonksiyon için db.py'de kanal bazlı veri tutmak gerekir
        # Şimdilik placeholder
        return {}

    def _get_top_voice_channels(self, member: discord.Member):
        """En çok vakit geçirilen ses kanallarını döndürür (simüle)"""
        # Gerçek implementasyon için kanal bazlı ses verisi gerekir
        voice_channels = [ch for ch in member.guild.voice_channels if ch.members]
        result = []
        for i, ch in enumerate(voice_channels[:5]):
            emoji = "🟢" if i == 0 else "🔴" if i == 1 else "🔵"
            # Simüle edilmiş veri
            sure = f"{(5-i)} saat, {(i+1)*10} dakika {(i+1)*20} saniye"
            result.append((ch.name, sure, emoji))
        return result

    def _get_top_message_channels(self, user_id: str, guild_id: str):
        """En çok mesaj atılan kanalları döndürür (simüle)"""
        # Gerçek implementasyon için kanal bazlı mesaj verisi gerekir
        # Şimdilik placeholder veri
        return [
            ("bilinmeyen", 13),
            ("bilinmeyen", 11),
            ("bilinmeyen", 10),
            ("resimli-sohbet", 7),
            ("bilinmeyen", 6),
        ]


def format_duration(minutes: int) -> str:
    if not minutes:
        return "0 dakika"
    h = minutes // 60
    m = minutes % 60
    if h == 0:
        return f"{m} dakika"
    return f"{h} saat {m} dakika"


async def setup(bot: commands.Bot):
    await bot.add_cog(Stat(bot))
