import os
from urllib.parse import urlsplit

import aiohttp
from discord import IntegrationType, InteractionContextType, AllowedMentions, ApplicationContext, Bot, Interaction, MediaGalleryItem, SelectOption
from discord.commands import slash_command
from discord.ext.commands import Cog

from cogs.premium_handler import premium_cooldown
from discord.ui import Container, DesignerModal, DesignerView, InputText, Label, MediaGallery, Select, TextDisplay
from discord.utils import escape_markdown


FILTERS = ("high", "medium", "low", "off")
SEARCH_URL = "https://api.klipy.com/v2/search"


def https_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme == "https" and parsed.hostname and not parsed.username:
            return value
    except ValueError:
        pass
    return None


def result_view(result: dict) -> DesignerView:
    formats = result.get("media_formats")
    if not isinstance(formats, dict):
        raise ValueError("Missing media formats")
    gif = formats.get("gif")
    media_url = https_url(gif.get("url")) if isinstance(gif, dict) else None
    if media_url is None:
        raise ValueError("Missing GIF URL")
    title = str(result.get("title") or "KLIPY GIF")[:200]
    description = str(result.get("content_description") or title)[:1024]
    container = Container(
        TextDisplay(f"### {escape_markdown(title)}"),
        MediaGallery(MediaGalleryItem(url=media_url, description=description)),
        TextDisplay("Powered by KLIPY"),
    )
    for field in ("username", "source", "content_description_source"):
        if result.get(field):
            container.add_item(TextDisplay(f"{field.replace('_', ' ').title()}: {escape_markdown(str(result[field])[:500])}"))
    return DesignerView(container, timeout=None)


class KlipySearchModal(DesignerModal):
    def __init__(self):
        super().__init__(title="Search KLIPY", timeout=300)
        self.query = InputText(placeholder="Search KLIPY", min_length=1, max_length=200)
        self.maturity = Select(
            options=[
                SelectOption(label=value.title(), value=value, default=value == "low")
                for value in FILTERS
            ],
            min_values=1,
            max_values=1,
            required=True,
        )
        self.add_item(Label("GIF search", self.query))
        self.add_item(Label("Maturity filter (high = strongest)", self.maturity))

    async def callback(self, interaction: Interaction):
        query = (self.query.value or "").strip()
        if not query:
            await interaction.response.send_message("Enter a search term.", ephemeral=True)
            return
        maturity = (self.maturity.values or ["high"])[0]
        if maturity not in FILTERS:
            await interaction.response.send_message("Choose high, medium, low, or off.", ephemeral=True)
            return
        api_key = os.getenv("KLIPY_API_KEY", "").strip()
        if not api_key:
            await interaction.response.send_message("KLIPY search isn't configured yet.", ephemeral=True)
            return
        await interaction.response.defer()
        view: DesignerView | None = None
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.get(SEARCH_URL, params={
                    "key": api_key,
                    "q": query,
                    "contentfilter": maturity,
                    "media_filter": "gif",
                    "limit": 1,
                }, allow_redirects=False) as response:
                    if response.status == 429:
                        message = "KLIPY is receiving too many requests. Please try again shortly."
                    elif response.status in (401, 403):
                        message = "KLIPY search is unavailable. We're working on it - please try again later."
                    elif response.status != 200:
                        message = "KLIPY is unavailable. Please try again later."
                    else:
                        payload = await response.json()
                        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                            raise ValueError("Invalid search response")
                        results = payload["results"]
                        if not results:
                            message = "No GIFs found. Try another search or maturity filter."
                        else:
                            if not isinstance(results[0], dict):
                                raise ValueError("Invalid GIF result")
                            view = result_view(results[0])
                            message = None
        except (aiohttp.ClientError, TimeoutError, ValueError):
            message = "Couldn't load GIFs from KLIPY. Please try again later."
        if message is not None:
            await interaction.followup.send(message, ephemeral=True)
            return
        if view is None:
            await interaction.followup.send("Couldn't load GIFs from KLIPY. Please try again later.", ephemeral=True)
            return
        await interaction.followup.send(view=view, allowed_mentions=AllowedMentions.none())


class Klipy(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @slash_command(
        name="klipy", description="Search KLIPY for a GIF.",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
        contexts={
            InteractionContextType.guild,
            InteractionContextType.bot_dm,
            InteractionContextType.private_channel,
        },
    )
    @premium_cooldown(normal=10, premium=0)
    async def klipy(self, ctx: ApplicationContext):
        await ctx.response.send_modal(KlipySearchModal())


def setup(bot: Bot):
    bot.add_cog(Klipy(bot))
