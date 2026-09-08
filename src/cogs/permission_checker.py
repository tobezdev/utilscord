from discord import (
	AllowedMentions, ApplicationContext, Bot, InteractionContextType,
	Member, Permissions, Thread, option,
)
from discord.abc import GuildChannel
from discord.commands import slash_command
from discord.ext.commands import Cog, NoPrivateMessage, guild_only
from discord.ui import Container, DesignerView, TextDisplay


class PermissionChecker(Cog):
	def __init__(self, bot: Bot) -> None:
		self.bot = bot

	@slash_command(
		name="permissions",
		description="Check a member's permissions in this channel.",
		contexts={InteractionContextType.guild},
	)
	@guild_only()
	@option("user", description="The server member whose permissions to check.")
	async def permissions(self, ctx: ApplicationContext, user: Member):
		if ctx.guild is None:
			raise NoPrivateMessage()

		channel = ctx.channel
		if isinstance(channel, Thread):
			channel = channel.parent
		if not isinstance(channel, GuildChannel):
			return await ctx.respond("This channel's permissions are unavailable.", ephemeral=True)

		resolved = channel.permissions_for(user)
		notes = []
		if user.id == ctx.guild.owner_id:
			notes.append("The server owner bypasses channel overrides.")
		elif user.guild_permissions.administrator:
			notes.append("Administrator bypasses channel overrides.")
		elif user.timed_out:
			resolved.value &= Permissions(view_channel=True, read_message_history=True).value
			notes.append("An active timeout restricts this member's permissions.")
		if isinstance(ctx.channel, Thread):
			notes.append("Threads inherit parent channel permissions; private membership and archived/locked state can further restrict access.")

		allowed = []
		denied = []
		for name, enabled in resolved:
			(allowed if enabled else denied).append(name.replace("_", " ").title())

		header = (
			f"### Permissions\n**Member:** {user.mention}\n"
			f"**Channel:** {channel.mention}\n"
			"Includes @everyone, assigned roles, and applicable channel/member overrides."
		)
		if notes:
			header += "\n" + "\n".join(notes)
		return await ctx.respond(
			view=DesignerView(Container(
				TextDisplay(header),
				TextDisplay("### Allowed\n" + (", ".join(allowed) or "None")),
				TextDisplay("### Denied / unavailable\n" + (", ".join(denied) or "None")),
			)),
			ephemeral=True,
			allowed_mentions=AllowedMentions.none(),
		)


def setup(bot: Bot):
	bot.add_cog(PermissionChecker(bot))
