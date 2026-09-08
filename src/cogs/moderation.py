from datetime import timedelta
import re

from discord import AllowedMentions, Bot, ApplicationContext, InteractionContextType, Member, NotFound, Object, Permissions, TextChannel, Thread, option
from discord.ext.commands import Cog, NoPrivateMessage, guild_only, has_guild_permissions, bot_has_guild_permissions, has_permissions, bot_has_permissions
from discord.commands import slash_command
from discord.ui import DesignerView, Container, TextDisplay
from discord.utils import escape_markdown, utcnow


class Moderation(Cog):
	def __init__(self, bot: Bot) -> None:
		self.bot = bot

	@slash_command(
		name="kick",
		description="Kick a member from the server.",
		contexts={InteractionContextType.guild},
		default_member_permissions=Permissions(kick_members=True),
	)
	@has_guild_permissions(kick_members=True)
	@bot_has_guild_permissions(kick_members=True)
	@guild_only()
	@option("member", description="The member to kick.")
	@option("reason", description="The reason for the kick.", max_length=400)
	async def kick(
		self,
		ctx: ApplicationContext,
		member: Member,
		reason: str = "No reason provided.",
	):
		guild = ctx.guild
		author = ctx.author
		if guild is None or not isinstance(author, Member):
			raise NoPrivateMessage()

		error = None
		if member.id == author.id:
			error = "You can't kick yourself."
		elif member.id == guild.me.id:
			error = "I can't kick myself."
		elif member.id == guild.owner_id:
			error = "You can't kick the server owner."
		elif author.id != guild.owner_id and member.top_role >= author.top_role:
			error = "You can only kick members whose highest role is below yours."
		elif member.top_role >= guild.me.top_role:
			error = "I can only kick members whose highest role is below mine."

		if error is not None:
			return await ctx.respond(
				view=DesignerView(Container(TextDisplay(f"### ⚠️ Can't kick member\n{error}"))),
				ephemeral=True,
			)

		reason = reason.strip() or "No reason provided."
		await ctx.defer(ephemeral=True)
		audit_reason = f"Moderator: {author.display_name} ({author.name}) [{author.id}] | {reason}"[:512]
		await member.kick(reason=audit_reason)
		return await ctx.respond(
			view=DesignerView(Container(TextDisplay(
				f"### Member kicked\n{member.mention} (`{member.id}`) was kicked.\n"
				f"**Reason:** {escape_markdown(reason)}"
			))),
			ephemeral=True,
			allowed_mentions=AllowedMentions.none(),
		)

	async def _respond(self, ctx: ApplicationContext, title: str, message: str):
		return await ctx.respond(
			view=DesignerView(Container(TextDisplay(f"### {title}\n{message}"))),
			ephemeral=True,
			allowed_mentions=AllowedMentions.none(),
		)

	def _target_error(self, ctx: ApplicationContext, member: Member, action: str) -> str | None:
		guild = ctx.guild
		author = ctx.author
		if guild is None or not isinstance(author, Member):
			raise NoPrivateMessage()
		if member.id == author.id:
			return f"You can't {action} yourself."
		if member.id == guild.me.id:
			return f"I can't {action} myself."
		if member.id == guild.owner_id:
			return f"You can't {action} the server owner."
		if author.id != guild.owner_id and member.top_role >= author.top_role:
			return f"You can only {action} members whose highest role is below yours."
		if member.top_role >= guild.me.top_role:
			return f"I can only {action} members whose highest role is below mine."
		return None

	def _audit_reason(self, ctx: ApplicationContext, reason: str) -> str:
		return f"Moderator: {ctx.author.display_name} ({ctx.author.name}) [{ctx.author.id}] | {reason}"[:512]

	@slash_command(
		name="mute",
		description="Timeout a member.",
		contexts={InteractionContextType.guild},
		default_member_permissions=Permissions(moderate_members=True),
	)
	@has_guild_permissions(moderate_members=True)
	@bot_has_guild_permissions(moderate_members=True)
	@guild_only()
	@option("member", description="The member to mute.")
	@option("duration", description="Timeout duration, e.g. 30m, 5d, 2w or 1d12h (maximum 28 days).", max_length=100)
	@option("reason", description="The reason for this action.", max_length=400)
	async def mute(
		self,
		ctx: ApplicationContext,
		member: Member,
		duration: str,
		reason: str = "No reason provided.",
	):
		error = self._target_error(ctx, member, "mute")
		if error is None and member.guild_permissions.administrator:
			error = "Administrators can't be timed out."
		if error is not None:
			return await self._respond(ctx, "⚠️ Can't mute member", error)

		duration = duration.strip().lower()
		if len(duration) > 100 or re.fullmatch(r"(?:[0-9]+\s*[smhdw]\s*)+", duration) is None:
			return await self._respond(
				ctx, "⚠️ Invalid duration",
				"Use a duration such as 30s, 10m, 2h, 5d, 2w or 1d12h.",
			)
		units = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
		seconds = sum(int(amount) * units[unit] for amount, unit in re.findall(r"([0-9]+)\s*([smhdw])", duration))
		if not 1 <= seconds <= 28 * 86400:
			return await self._respond(ctx, "⚠️ Invalid duration", "Timeout duration must be between 1 second and 28 days.")

		reason = reason.strip() or "No reason provided."
		await ctx.defer(ephemeral=True)
		await member.timeout(utcnow() + timedelta(seconds=seconds), reason=self._audit_reason(ctx, reason))
		return await self._respond(
			ctx, "Member muted",
			f"{member.mention} (`{member.id}`) was timed out for {duration}.\n**Reason:** {escape_markdown(reason)}",
		)

	@slash_command(
		name="unmute",
		description="Remove a member's timeout.",
		contexts={InteractionContextType.guild},
		default_member_permissions=Permissions(moderate_members=True),
	)
	@has_guild_permissions(moderate_members=True)
	@bot_has_guild_permissions(moderate_members=True)
	@guild_only()
	@option("member", description="The member to unmute.")
	@option("reason", description="The reason for this action.", max_length=400)
	async def unmute(
		self,
		ctx: ApplicationContext,
		member: Member,
		reason: str = "No reason provided.",
	):
		error = self._target_error(ctx, member, "unmute")
		if error is not None:
			return await self._respond(ctx, "⚠️ Can't unmute member", error)

		reason = reason.strip() or "No reason provided."
		await ctx.defer(ephemeral=True)
		await member.timeout(None, reason=self._audit_reason(ctx, reason))
		return await self._respond(
			ctx, "Member unmuted",
			f"{member.mention} (`{member.id}`) had their timeout removed.\n**Reason:** {escape_markdown(reason)}",
		)

	@slash_command(
		name="ban",
		description="Ban a member from the server.",
		contexts={InteractionContextType.guild},
		default_member_permissions=Permissions(ban_members=True),
	)
	@has_guild_permissions(ban_members=True)
	@bot_has_guild_permissions(ban_members=True)
	@guild_only()
	@option("member", description="The member to ban.")
	@option("delete_days", description="Days of message history to delete (0 keeps messages).", min_value=0, max_value=7)
	@option("reason", description="The reason for this action.", max_length=400)
	async def ban(
		self,
		ctx: ApplicationContext,
		member: Member,
		delete_days: int = 0,
		reason: str = "No reason provided.",
	):
		error = self._target_error(ctx, member, "ban")
		if error is None and not 0 <= delete_days <= 7:
			error = "Message history deletion must be between 0 and 7 days."
		if error is not None:
			return await self._respond(ctx, "⚠️ Can't ban member", error)

		reason = reason.strip() or "No reason provided."
		await ctx.defer(ephemeral=True)
		await member.ban(delete_message_seconds=delete_days * 86400, reason=self._audit_reason(ctx, reason))
		return await self._respond(
			ctx, "Member banned",
			f"{member.mention} (`{member.id}`) was banned.\n**Reason:** {escape_markdown(reason)}",
		)

	@slash_command(
		name="unban",
		description="Unban a user by their Discord ID.",
		contexts={InteractionContextType.guild},
		default_member_permissions=Permissions(ban_members=True),
	)
	@has_guild_permissions(ban_members=True)
	@bot_has_guild_permissions(ban_members=True)
	@guild_only()
	@option("user_id", description="The Discord ID of the banned user.")
	@option("reason", description="The reason for this action.", max_length=400)
	async def unban(self, ctx: ApplicationContext, user_id: str, reason: str = "No reason provided."):
		guild = ctx.guild
		if guild is None:
			raise NoPrivateMessage()
		if not user_id.isascii() or not user_id.isdecimal() or not 1 <= len(user_id) <= 20 or not 0 < int(user_id) < 2**64:
			return await self._respond(ctx, "⚠️ Invalid user ID", "Enter a valid numeric Discord user ID.")

		reason = reason.strip() or "No reason provided."
		await ctx.defer(ephemeral=True)
		try:
			await guild.unban(Object(id=int(user_id)), reason=self._audit_reason(ctx, reason))
		except NotFound:
			return await self._respond(ctx, "⚠️ User not banned", "No ban was found for that user ID.")
		return await self._respond(
			ctx, "User unbanned",
			f"User `{user_id}` was unbanned.\n**Reason:** {escape_markdown(reason)}",
		)

	@slash_command(
		name="purge",
		description="Remove the most recent messages in this channel.",
		contexts={InteractionContextType.guild},
		default_member_permissions=Permissions(manage_messages=True),
	)
	@has_permissions(manage_messages=True)
	@bot_has_permissions(manage_messages=True, read_message_history=True, view_channel=True)
	@guild_only()
	@option("amount", int, description="Number of recent messages to remove (1-1000); use amount or until.", min_value=1, max_value=1000)
	@option("until", str, description="Remove messages newer than this ID; prefix with ! to also remove that message.", max_length=21)
	@option("reason", description="The reason for this action.", max_length=400)
	async def purge(
		self,
		ctx: ApplicationContext,
		amount: int | None = None,
		reason: str = "No reason provided.",
		until: str | None = None,
	):
		channel = ctx.channel
		if not isinstance(channel, (TextChannel, Thread)):
			return await self._respond(ctx, "⚠️ Unsupported channel", "Use this command in a text channel or thread.")
		if (amount is None) == (until is None):
			return await self._respond(ctx, "⚠️ Choose a purge mode", "Provide either amount or until, but not both.")
		if amount is not None and not 1 <= amount <= 1000:
			return await self._respond(ctx, "⚠️ Invalid amount", "Choose between 1 and 1000 messages.")

		message_id = None
		include_target = False
		if until is not None:
			until = until.strip()
			if re.fullmatch(r"!?[0-9]{1,20}", until) is None:
				return await self._respond(ctx, "⚠️ Invalid message ID", "Enter a message ID, optionally prefixed with ! to include it.")
			include_target = until.startswith("!")
			message_id = int(until.removeprefix("!"))
			if not 0 < message_id < 2**64:
				return await self._respond(ctx, "⚠️ Invalid message ID", "Enter a valid Discord message ID.")

		reason = reason.strip() or "No reason provided."
		await ctx.defer(ephemeral=True)
		after = None
		if message_id is not None:
			try:
				target = await channel.fetch_message(message_id)
			except NotFound:
				return await self._respond(ctx, "⚠️ Message not found", "That message isn't present in this channel. No messages were removed.")
			if target.channel.id != channel.id or target.created_at >= ctx.interaction.created_at:
				return await self._respond(ctx, "⚠️ Invalid target message", "Choose an existing message in this channel sent before this command. No messages were removed.")
			# History's after boundary is exclusive; subtract one to include the target.
			after = Object(id=target.id - 1 if include_target else target.id)

		deleted = await channel.purge(
			limit=amount,
			before=ctx.interaction.created_at,
			after=after,
			oldest_first=False,
			reason=self._audit_reason(ctx, reason),
		)
		return await self._respond(
			ctx, "Messages removed",
			f"Removed {len(deleted)} messages from {channel.mention}.\n**Reason:** {escape_markdown(reason)}",
		)

	@slash_command(
		name="slowmode",
		description="Set the message cooldown for this text channel.",
		contexts={InteractionContextType.guild},
		default_member_permissions=Permissions(manage_channels=True),
	)
	@has_permissions(manage_channels=True)
	@bot_has_permissions(manage_channels=True)
	@guild_only()
	@option("seconds", description="Cooldown in seconds (0 disables slowmode).", min_value=0, max_value=21600)
	@option("reason", description="The reason for this action.", max_length=400)
	async def slowmode(self, ctx: ApplicationContext, seconds: int, reason: str = "No reason provided."):
		channel = ctx.channel
		if not isinstance(channel, TextChannel):
			return await self._respond(ctx, "⚠️ Unsupported channel", "Use this command in a text channel.")
		if not 0 <= seconds <= 21600:
			return await self._respond(ctx, "⚠️ Invalid cooldown", "Choose between 0 and 21600 seconds.")

		reason = reason.strip() or "No reason provided."
		await ctx.defer(ephemeral=True)
		await channel.edit(slowmode_delay=seconds, reason=self._audit_reason(ctx, reason))
		status = f"Set the cooldown to {seconds} seconds" if seconds else "Disabled slowmode"
		return await self._respond(
			ctx, "Slowmode updated",
			f"{status} in {channel.mention}.\n**Reason:** {escape_markdown(reason)}",
		)


def setup(bot: Bot):
	bot.add_cog(Moderation(bot))
