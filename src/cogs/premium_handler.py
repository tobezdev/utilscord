import asyncio
import logging
import time
from collections import OrderedDict, defaultdict

from discord import ApplicationContext, Entitlement, HTTPException, Member, NotFound, Object
from discord.ext import tasks
from discord.ext.commands import BucketType, CheckFailure, Cog, CommandOnCooldown, Cooldown, check, slash_command
from discord.utils import utcnow


USER_PREMIUM_SKU_ID = 1547031239700123661
USER_PREMIUM_PLUS_SKU_ID = 1547041149036925011
PREMIUM_SKU_IDS = frozenset({USER_PREMIUM_SKU_ID, USER_PREMIUM_PLUS_SKU_ID})
OFFICIAL_GUILD_ID = 1546590587421986886
PREMIUM_ROLE_ID = 1546920314649313310
ROLE_REMOVAL_GRACE_SECONDS = 300
log = logging.getLogger(__name__)


def log_subscription_event(event: str, sku_id: int) -> None:
    timestamp = utcnow().isoformat().replace("+00:00", "Z")
    log.info("Premium subscription %s sku_id=%s timestamp=%s", event, sku_id, timestamp)


class PremiumRequired(CheckFailure):
    pass


def is_active(entitlement: Entitlement, application_id: int | None) -> bool:
    now = utcnow()
    return (
        application_id is not None
        and entitlement.application_id == application_id
        and not entitlement.deleted
        and (not entitlement.starts_at or entitlement.starts_at <= now)
        and (not entitlement.ends_at or entitlement.ends_at > now)
    )


def has_premium(ctx: ApplicationContext) -> bool:
    return any(
        is_active(entitlement, ctx.bot.application_id)
        and entitlement.sku_id in PREMIUM_SKU_IDS
        and entitlement.user_id == ctx.author.id
        and not entitlement.guild_id
        for entitlement in ctx.interaction.entitlements
    )


def premium_only():
    async def predicate(ctx):
        if not has_premium(ctx):
            raise PremiumRequired()
        return True

    return check(predicate)


def premium_cooldown(*, normal: float, premium: float):
    if normal <= 0 or not 0 <= premium <= normal:
        raise ValueError("Require normal > 0 and 0 <= premium <= normal")
    last_used = OrderedDict()

    async def predicate(ctx):
        now = time.monotonic()
        while last_used and next(iter(last_used.values())) <= now - normal:
            last_used.popitem(last=False)
        period = premium if has_premium(ctx) else normal
        previous = last_used.get(ctx.author.id)
        if period and previous is not None and (retry := previous + period - now) > 0:
            raise CommandOnCooldown(
                Cooldown(1, period), retry, BucketType.user)
        last_used[ctx.author.id] = now
        last_used.move_to_end(ctx.author.id)
        return True

    return check(predicate)


class PremiumHandler(Cog):
    def __init__(self, bot):
        self.bot = bot
        self._lock = asyncio.Lock()
        self._pending_role_removals: dict[int, float] = {}

    def cog_unload(self):
        self.reconcile_roles.cancel()

    @Cog.listener()
    async def on_ready(self):
        if not self.reconcile_roles.is_running():
            self.reconcile_roles.start()

    async def _personal_entitlements(self, user=None):
        return [
            entitlement async for entitlement in self.bot.entitlements(
                user=user, skus=[Object(sku_id) for sku_id in PREMIUM_SKU_IDS],
                limit=None, exclude_ended=True,
            )
        ]

    def _entitled_users(self, entitlements):
        return {
            entitlement.user_id for entitlement in entitlements
            if entitlement.sku_id in PREMIUM_SKU_IDS
            and entitlement.user_id and not entitlement.guild_id
            and is_active(entitlement, self.bot.application_id)
        }

    async def _set_role(self, member, role, entitled):
        if entitled or role not in member.roles:
            self._pending_role_removals.pop(member.id, None)
        if (role in member.roles) == entitled:
            return
        if not entitled:
            # Renewals can briefly leave entitlement reads out of sync. Keep
            # the role until the absence persists, then confirm with a fresh
            # user-specific read across both tiers before removing anything.
            now = time.monotonic()
            first_missing = self._pending_role_removals.setdefault(member.id, now)
            if now - first_missing < ROLE_REMOVAL_GRACE_SECONDS:
                return
            entitlements = await self._personal_entitlements(Object(member.id))
            if member.id in self._entitled_users(entitlements):
                self._pending_role_removals.pop(member.id, None)
                return
        try:
            if entitled:
                await member.add_roles(role, reason="Active personal Utilscord Premium subscription")
            else:
                await member.remove_roles(role, reason="Expired personal Utilscord Premium subscription")
                self._pending_role_removals.pop(member.id, None)
        except HTTPException:
            log.exception("Could not sync Premium role")

    @tasks.loop(minutes=1)
    async def reconcile_roles(self):
        try:
            async with self._lock:
                guild = self.bot.get_guild(OFFICIAL_GUILD_ID)
                role = guild.get_role(PREMIUM_ROLE_ID) if guild else None
                if role is None:
                    log.warning(
                        "Premium role or official guild is unavailable")
                    return
                members = [member async for member in guild.fetch_members(limit=None)]
                entitlements = await self._personal_entitlements()
                by_user = defaultdict(list)
                for entitlement in entitlements:
                    by_user[entitlement.user_id].append(entitlement)
                for member in members:
                    entitled = member.id in self._entitled_users(
                        by_user[member.id])
                    await self._set_role(member, role, entitled)
        except (HTTPException, OSError):
            log.exception("Premium role reconciliation failed; retrying next minute")

    async def _sync_user(self, user_id):
        try:
            async with self._lock:
                guild = self.bot.get_guild(OFFICIAL_GUILD_ID)
                role = guild.get_role(PREMIUM_ROLE_ID) if guild else None
                if role is None:
                    return
                member = await guild.fetch_member(user_id)
                entitlements = await self._personal_entitlements(Object(user_id))
                await self._set_role(member, role, user_id in self._entitled_users(entitlements))
        except NotFound:
            return
        except (HTTPException, OSError):
            log.exception("Could not refresh Premium role")

    @Cog.listener()
    async def on_member_join(self, member: Member):
        if member.guild.id == OFFICIAL_GUILD_ID:
            await self._sync_user(member.id)

    async def _entitlement_changed(self, entitlement):
        if entitlement.sku_id in PREMIUM_SKU_IDS and entitlement.user_id:
            await self._sync_user(entitlement.user_id)

    @Cog.listener()
    async def on_entitlement_create(self, entitlement: Entitlement):
        if entitlement.sku_id in PREMIUM_SKU_IDS:
            log_subscription_event("created", entitlement.sku_id)
        await self._entitlement_changed(entitlement)

    @Cog.listener()
    async def on_entitlement_update(self, entitlement: Entitlement):
        if entitlement.sku_id in PREMIUM_SKU_IDS:
            log_subscription_event("renewed", entitlement.sku_id)
        await self._entitlement_changed(entitlement)

    @Cog.listener()
    async def on_entitlement_delete(self, entitlement: Entitlement):
        if entitlement.sku_id in PREMIUM_SKU_IDS:
            log_subscription_event("deleted", entitlement.sku_id)
        await self._entitlement_changed(entitlement)

    @slash_command(name="premium", description="Check your Premium subscription status")
    async def premium(self, ctx: ApplicationContext):
        entitlements = await self._personal_entitlements(ctx.author)
        entitlements = [
            entitlement for entitlement in entitlements
            if entitlement.sku_id in PREMIUM_SKU_IDS
            and entitlement.user_id == ctx.author.id
            and not entitlement.guild_id
            and is_active(entitlement, self.bot.application_id)
        ]
        tier = (
            "Premium+" if any(
                entitlement.sku_id == USER_PREMIUM_PLUS_SKU_ID
                for entitlement in entitlements
            ) else "Premium"
        )
        msg = (
            f"You have an active personal {tier} subscription."
            if entitlements else
            "You do not have an active personal Premium subscription."
        )
        for entitlement in entitlements:
            if entitlement.ends_at:
                msg += f"\nYour subscription will expire on {entitlement.ends_at}."
        await ctx.respond(msg)


def setup(bot):
    bot.add_cog(PremiumHandler(bot))
