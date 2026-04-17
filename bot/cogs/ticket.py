import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
from utils.ticket_db import add_ticket_claim, get_ticket_leaderboard


# ─── Ticket Butonları ─────────────────────────────────────────────────────────
class TicketButonlari(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # Yetkili - Sahiplen
    @discord.ui.button(
        label="Yetkili - Sahiplen",
        style=discord.ButtonStyle.primary,
        custom_id="ticket_sahiplen",
        emoji="👤"
    )
    async def sahiplen(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Ticket'ı açan kişi sahiplenemesin
        kanal_adi = interaction.channel.name  # örn: ticket-kerem
        kullanici_adi = interaction.user.name.lower()[:20]
        if kanal_adi == f"ticket-{kullanici_adi}":
            return await interaction.response.send_message(
                "❌ Kendi ticketını sahiplenemezssin!",
                ephemeral=True
            )

        # Önce response'u hemen kabul et (3 sn timeout'u aşmamak için)
        await interaction.response.defer(ephemeral=False)

        # Butonun bulunduğu mesaj direkt interaction.message üzerinden gelir
        msg = interaction.message
        if not msg or not msg.embeds:
            return await interaction.followup.send("❌ Embed bulunamadı.", ephemeral=True)

        embed = msg.embeds[0]

        # Durum field'ını güncelle
        yeni_embed = discord.Embed(
            title=embed.title,
            description=embed.description,
            color=embed.color,
            timestamp=embed.timestamp
        )
        if embed.thumbnail:
            yeni_embed.set_thumbnail(url=embed.thumbnail.url)
        if embed.footer:
            yeni_embed.set_footer(text=embed.footer.text)

        for field in embed.fields:
            if field.name == "Durum":
                yeni_embed.add_field(
                    name="Durum",
                    value=f"🟢 - {interaction.user.mention} Sahiplendi",
                    inline=False
                )
            else:
                yeni_embed.add_field(name=field.name, value=field.value, inline=field.inline)

        await msg.edit(embed=yeni_embed)
        await interaction.followup.send(
            f"✅ {interaction.user.mention} ticketi sahiplendi."
        )

        # Sahiplenme verisini kaydet
        add_ticket_claim(str(interaction.user.id), str(interaction.guild.id))

    # Yetkili - Kapat
    @discord.ui.button(
        label="Yetkili - Kapat",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_yetkili_kapat",
        emoji="🗂️"
    )
    async def yetkili_kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Yetkili kontrolü
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                "❌ Bu butonu sadece yetkililer kullanabilir.",
                ephemeral=True
            )
        embed = discord.Embed(
            title="🔒 Ticket Kapatılıyor",
            description=(
                f"Bu ticket **{interaction.user}** tarafından kapatıldı.\n"
                "Kanal **5 saniye** içinde silinecek."
            ),
            color=0xFF8C00,
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)
        await interaction.channel.delete()

    # Oyuncu - Kapat
    @discord.ui.button(
        label="Oyuncu - Kapat",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_oyuncu_kapat",
        emoji="⚙️"
    )
    async def oyuncu_kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔒 Ticket Kapatılıyor",
            description=(
                f"Bu ticket **{interaction.user}** tarafından kapatıldı.\n"
                "Kanal **5 saniye** içinde silinecek."
            ),
            color=0xFF4444,
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)
        await interaction.channel.delete()


# ─── Ticket Kategori Dropdown ─────────────────────────────────────────────────
class TicketKategoriSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Genel Destek",
                description="Genel sorularınız için destek alın.",
                value="genel_destek",
                emoji="🛠️"
            ),
            discord.SelectOption(
                label="Şikayet",
                description="Bir kullanıcı veya durum hakkında şikayet.",
                value="sikayet",
                emoji="⚠️"
            ),
            discord.SelectOption(
                label="Satın Alma",
                description="Satın alma işlemleri için destek.",
                value="satin_alma",
                emoji="💰"
            ),
        ]
        super().__init__(
            placeholder="Ticket Açmak İçin Kategori Seçiniz.",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_kategori"
        )

    async def callback(self, interaction: discord.Interaction):
        kategori_isimler = {
            "genel_destek": "🛠️ Genel Destek",
            "sikayet": "⚠️ Şikayet",
            "satin_alma": "💰 Satın Alma",
        }
        secilen = self.values[0]
        kategori_adi = kategori_isimler[secilen]
        guild = interaction.guild
        user = interaction.user

        # Zaten açık ticket var mı?
        kanal_adi = f"ticket-{user.name.lower()[:20]}"
        mevcut = discord.utils.get(guild.text_channels, name=kanal_adi)
        if mevcut:
            return await interaction.response.send_message(
                f"❌ Zaten açık bir ticketin var: {mevcut.mention}",
                ephemeral=True
            )

        # İzinler
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True
            ),
        }

        try:
            kanal = await guild.create_text_channel(
                name=kanal_adi,
                overwrites=overwrites
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ Kanal oluşturma yetkim yok. Bot yetkilerini kontrol edin.",
                ephemeral=True
            )

        # ─── Ticket Embed (görseldeki gibi) ──────────────────────────────────
        embed = discord.Embed(
            title=f"🎮 {kategori_adi.split(' ', 1)[-1]} Kategorili Destek!",
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )

        # Kullanıcı avatarını thumbnail olarak ekle
        embed.set_thumbnail(url=user.display_avatar.url)

        # Açıklama satırı (görseldeki gibi)
        embed.description = (
            f"> {user.mention} kişisi <t:{int(discord.utils.utcnow().timestamp())}:R> "
            f"tarihinde destek talebi oluşturdu.\n\n"
            "Oluşturulan destek talebinin bilgilerini aşağıda belirttim;"
        )

        embed.add_field(
            name="Oluşturan Kullanıcı:",
            value=f"```{user.name}```",
            inline=False
        )
        embed.add_field(
            name="Kategori:",
            value=f"```{kategori_adi.split(' ', 1)[-1]}```",
            inline=False
        )
        embed.add_field(
            name="Durum",
            value="🟡 - Yetkili Sahiplendi",
            inline=False
        )
        embed.set_footer(text="303 Bot | Ticket Sistemi.")

        view = TicketButonlari()
        await kanal.send(content=user.mention, embed=embed, view=view)

        await interaction.response.send_message(
            f"✅ Ticketin oluşturuldu: {kanal.mention}",
            ephemeral=True
        )

        # Dropdown'ı sıfırla (seçili kategori kalmasın)
        await interaction.message.edit(view=TicketPanelView())


# ─── Ticket Panel View ────────────────────────────────────────────────────────
class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketKategoriSelect())


# ─── Ticket Cog ───────────────────────────────────────────────────────────────
class Ticket(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.add_view(TicketPanelView())
        bot.add_view(TicketButonlari())

    @app_commands.command(name="ticket-top", description="Ticket sahiplenme sıralamasını gösterir.")
    async def ticket_top(self, interaction: discord.Interaction):
        await interaction.response.defer()

        leaderboard = get_ticket_leaderboard(str(interaction.guild.id))

        if not leaderboard:
            return await interaction.followup.send(
                "❌ Henüz hiç ticket sahiplenme verisi yok.",
                ephemeral=True
            )

        # Sayfa sistemi - her sayfada 10 kişi
        sayfa_boyutu = 10
        toplam_sayfa = (len(leaderboard) + sayfa_boyutu - 1) // sayfa_boyutu
        sayfa = 0

        async def build_embed(sayfa: int) -> discord.Embed:
            embed = discord.Embed(
                title="🎫 Toplam Ticket Sıralaması",
                color=0x5865F2,
                timestamp=discord.utils.utcnow()
            )
            if interaction.guild.icon:
                embed.set_author(
                    name=interaction.guild.name,
                    icon_url=interaction.guild.icon.url
                )

            medals = {1: "🥇", 2: "🥈", 3: "🥉"}
            baslangic = sayfa * sayfa_boyutu
            bitis = baslangic + sayfa_boyutu
            sayfa_verisi = leaderboard[baslangic:bitis]

            satirlar = []
            for i, (user_id, count) in enumerate(sayfa_verisi, start=baslangic + 1):
                member = interaction.guild.get_member(int(user_id))
                isim = member.mention if member else f"`{user_id}`"
                medal = medals.get(i, "🔹")
                satirlar.append(f"{medal} **{i}.** {isim} • **{count}** ticket")

            embed.description = "\n".join(satirlar)
            embed.set_footer(
                text=f"Sayfa {sayfa + 1}/{toplam_sayfa} • {interaction.user.display_name}"
            )
            return embed

        # Sayfa butonları
        class SayfalamaButonlari(discord.ui.View):
            def __init__(self, mevcut_sayfa: int):
                super().__init__(timeout=60)
                self.sayfa = mevcut_sayfa
                self._update_buttons()

            def _update_buttons(self):
                self.geri.disabled = self.sayfa == 0
                self.ileri.disabled = self.sayfa >= toplam_sayfa - 1

            @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
            async def geri(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != interaction.user.id:
                    return await btn_interaction.response.send_message(
                        "❌ Bu butonları sadece komutu kullanan kişi kullanabilir.",
                        ephemeral=True
                    )
                self.sayfa -= 1
                self._update_buttons()
                embed = await build_embed(self.sayfa)
                await btn_interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
            async def ileri(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != interaction.user.id:
                    return await btn_interaction.response.send_message(
                        "❌ Bu butonları sadece komutu kullanan kişi kullanabilir.",
                        ephemeral=True
                    )
                self.sayfa += 1
                self._update_buttons()
                embed = await build_embed(self.sayfa)
                await btn_interaction.response.edit_message(embed=embed, view=self)

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True

        embed = await build_embed(sayfa)
        view = SayfalamaButonlari(sayfa)
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="ticket-panel", description="Ticket panelini gönderir.")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(color=0x5865F2)
        embed.set_author(
            name="303 | Destek Sistemi",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        embed.title = "✨ Destek Sistemi"
        embed.description = (
            "**✨ Destek Sistemi Hakkında:**\n"
            "Aşağıdaki seçeneklerden uygun olanı seçerek "
            "hemen bir ticket oluşturabilirsiniz.\n\n"
            "**🔗 Sunucu Bilgisi:**\n"
            "Sunucumuzun kurallarını okumayı unutmayın."
        )
        embed.set_footer(text="303 Bot | Ticket Sistemi.")

        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
        view = TicketPanelView()

        if os.path.exists(logo_path):
            file = discord.File(logo_path, filename="logo.png")
            embed.set_image(url="attachment://logo.png")
            await interaction.response.send_message(embed=embed, view=view, file=file)
        else:
            await interaction.response.send_message(embed=embed, view=view)

    @ticket_panel.error
    async def ticket_panel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Bu komutu kullanmak için **Administrator** yetkisine ihtiyacın var.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Ticket(bot))
