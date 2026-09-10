import math
import random
import string
import logging

from cogs.premium_handler import PremiumRequired

from discord import (
    ApplicationCommandInvokeError,
    ApplicationContext,
    Bot,
    ButtonStyle,
    CheckFailure as ApplicationCheckFailure,
    DiscordServerError,
    Forbidden,
    HTTPException,
    NotFound,
)
from discord.ext.commands import (
    BadArgument,
    BotMissingPermissions,
    CheckFailure,
    Cog,
    CommandOnCooldown,
    MaxConcurrencyReached,
    MissingPermissions,
    NoPrivateMessage,
    NotOwner,
)
from discord.ui import ActionRow, Button, Container, DesignerView, TextDisplay


log = logging.getLogger(__name__)


def build_exception_message_view(error: Exception, errcode: str) -> DesignerView:
    while isinstance(error, ApplicationCommandInvokeError):
        error = error.original

    match error:
        case BadArgument():
            msg = "One or more arguments were invalid or in the wrong format."
        case NoPrivateMessage():
            msg = "This command can't be used in DMs."
        case MissingPermissions():
            msg = "You don't have the required permissions to use this command."
        case BotMissingPermissions():
            msg = "I don't have the required permissions to perform that action."
        case CommandOnCooldown():
            seconds = max(1, math.ceil(error.retry_after))
            unit = "second" if seconds == 1 else "seconds"
            msg = f"That command is on cooldown. Try again in {seconds} {unit}."
        case MaxConcurrencyReached():
            msg = "This command has reached its limit of simultaneous uses. Please try again soon."
        case NotOwner():
            msg = "Only the bot owner can use this command."
        case PremiumRequired():
            msg = "This command requires a Premium Subscription."
        case CheckFailure() | ApplicationCheckFailure():
            msg = "You don't meet the requirements to use this command."
        case Forbidden():
            msg = "I don't have permission to perform that action."
        case NotFound():
            msg = "Something needed to complete this command could not be found."
        case DiscordServerError():
            msg = "Discord encountered a server error. Please try again later."
        case HTTPException():
            msg = "I couldn't complete a request to Discord."
        case _:
            msg = "Something went wrong while running this command."

    container = Container(TextDisplay(f"### ⚠️ Error\n{msg}"))
    button = Button(label=f"Error Code: {errcode}", style=ButtonStyle.gray, disabled=True)
    return DesignerView(container, ActionRow(button))


class ErrorHandler(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @Cog.listener()
    async def on_application_command_error(
        self,
        interaction: ApplicationContext,
        exception: Exception,
    ):
        errcode = "".join(random.choices(string.ascii_letters + string.digits, k=12))
        discord_interaction = getattr(interaction, "interaction", None)
        message = getattr(discord_interaction, "message", None)
        log.error(
            "Automated error report error_code=%s user_id=%s guild_id=%s "
            "channel_id=%s message_id=%s",
            errcode,
            getattr(interaction.author, "id", None),
            getattr(interaction.guild, "id", None),
            getattr(interaction.channel, "id", None),
            getattr(message, "id", None),
            exc_info=(type(exception), exception, exception.__traceback__),
        )
        return await interaction.respond(
            view=build_exception_message_view(exception, errcode)
        )


def setup(bot: Bot) -> None:
    bot.add_cog(ErrorHandler(bot))
