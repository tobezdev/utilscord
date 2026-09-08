from discord import IntegrationType, InteractionContextType, Bot, ApplicationContext
from discord.ext.commands import Cog, cooldown, BucketType
from discord.commands import slash_command
from discord.ui import DesignerView, Container, TextDisplay


class Ping(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @slash_command(
        name="ping", description="Check the bot's latency.",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
        contexts={
            InteractionContextType.guild,
            InteractionContextType.bot_dm,
            InteractionContextType.private_channel,
        },
    )
    @cooldown(1, 300, BucketType.user)
    @cooldown(1, 5, BucketType.default)
    async def ping(self, ctx: ApplicationContext):
        latency = round(self.bot.latency * 1000, None)
        container = Container(TextDisplay(f"### 🏓 Pong!\nLatency: {latency}ms"))
        return await ctx.respond(view=DesignerView(container))


def setup(bot: Bot):
    bot.add_cog(Ping(bot))
